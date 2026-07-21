"""
CryptoTracker BMZ — Flask Application
Modular architecture untuk UAS Pemrograman Backend.
"""
import logging
import os

# Load .env sebelum import config
from dotenv import load_dotenv
load_dotenv()

from flask import (
    Flask, request, redirect, url_for, render_template,
    flash, abort, session,
)
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.security import check_password_hash
from werkzeug.exceptions import HTTPException
from flask_wtf.csrf import CSRFError

# Modular components
from config import Config
from extensions import db, login_manager, csrf
from models import User, Watchlist
from decorators import admin_required, count_active_admins
import validators as V
from services.cache_service import cache
import services.coingecko_service as cg

# ─── Runtime API Key Manager ────────────────────────────────
from ml_model import (
    get_price_prediction_from_data,
    get_advanced_prediction_from_data,
)

# ─── App Factory ─────────────────────────────────────────────

def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # Login manager
    login_manager.login_view = "login"
    login_manager.login_message = "Silakan login terlebih dahulu."

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register error handlers
    register_error_handlers(app)

    # Register routes
    register_routes(app)

    # Bootstrap database
    with app.app_context():
        db.create_all()
        ensure_default_admin(app)

    return app


# ─── Database Bootstrap ──────────────────────────────────────

def ensure_default_admin(app: Flask) -> None:
    """Buat admin default jika belum ada dan AUTO_CREATE_DEFAULT_ADMIN=true."""
    auto_create = app.config.get("AUTO_CREATE_DEFAULT_ADMIN", True)
    # Handle string "false" from environment variables
    if isinstance(auto_create, str):
        auto_create = auto_create.lower() not in ("false", "0", "no", "")
    if not auto_create:
        return

    if db.session.query(User).filter(User.is_admin == True).count() > 0:
        return  # Sudah ada admin

    username = app.config.get("DEFAULT_ADMIN_USERNAME", "admin")
    email = app.config.get("DEFAULT_ADMIN_EMAIL", "admin@example.local")
    password = app.config.get("DEFAULT_ADMIN_PASSWORD", "")

    if not password or len(password) < 8:
        app.logger.critical(
            "DEFAULT_ADMIN_PASSWORD terlalu lemah atau kosong. "
            "Admin default TIDAK dibuat. Buat via 'flask create-admin'."
        )
        return

    try:
        user = User(
            username=username,
            email=email.lower(),
            is_admin=True,
            is_approved=True,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        app.logger.warning(
            "[!] Admin default dibuat (username=%s, email=%s). "
            "Ini adalah akun DEMO. Segera ubah password setelah demonstrasi.",
            username, email,
        )
    except Exception as e:
        db.session.rollback()
        app.logger.error("Gagal membuat admin default: %s", e)


# ─── Error Handlers ──────────────────────────────────────────

def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def not_found(e):
        return render_template(
            "error.html",
            error_code="404",
            error_title="Halaman Tidak Ditemukan",
            icon_name="file-x",
            message="Halaman yang Anda cari tidak ditemukan.",
        ), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template(
            "error.html",
            error_code="403",
            error_title="Akses Ditolak",
            icon_name="shield-off",
            message="Anda tidak memiliki izin untuk mengakses halaman ini.",
        ), 403

    @app.errorhandler(405)
    def method_not_allowed(e):
        return render_template(
            "error.html",
            error_code="405",
            error_title="Metode Tidak Diizinkan",
            icon_name="x-circle",
            message="Metode request tidak diizinkan untuk halaman ini.",
        ), 405

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return render_template(
            "error.html",
            error_code="400",
            error_title="Permintaan Tidak Valid",
            icon_name="shield-off",
            message="Token keamanan tidak valid atau telah kedaluwarsa.",
        ), 400

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_template(
            "error.html",
            error_code="500",
            error_title="Kesalahan Server",
            icon_name="server-off",
            message="Terjadi kesalahan di sisi server. Tim kami sudah notified.",
        ), 500

    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, HTTPException):
            return e

        app.logger.exception("Unhandled exception: %s", e)

        try:
            db.session.rollback()
        except Exception:
            app.logger.exception("Failed to rollback database session")

        return render_template(
            "error.html",
            error_code="500",
            error_title="Kesalahan Server",
            icon_name="server-off",
            message="Terjadi kesalahan pada server.",
        ), 500


# ─── Helpers ─────────────────────────────────────────────────

def format_number(num):
    if num is None:
        return "N/A"
    return f"{num:,.0f}"


def format_market_cap(num):
    if num is None:
        return "N/A"
    if num >= 1_000_000_000_000:
        return f"${num / 1_000_000_000_000:.2f}T"
    if num >= 1_000_000_000:
        return f"${num / 1_000_000_000:.2f}B"
    if num >= 1_000_000:
        return f"${num / 1_000_000:.2f}M"
    return f"${num:,.0f}"


def get_safe_next():
    """Ambil parameter next yang sudah divalidasi same-origin."""
    raw = request.values.get("next", "")
    if not raw:
        return None
    from urllib.parse import urlparse, urljoin
    parsed = urlparse(urljoin(request.url, raw))
    if parsed.netloc and parsed.netloc != request.host:
        return None
    return parsed.path + (("?" + parsed.query) if parsed.query else "")


# ─── Routes ──────────────────────────────────────────────────

def register_routes(app: Flask) -> None:

    # ── Static Pages ──────────────────────────────────────

    @app.route("/")
    def index():
        """Landing page — ringkasan pasar + CTA ke /market."""
        try:
            stats = cg.fetch_global_stats(
                api_key=app.config.get("COINGECKO_API_KEY", ""),
                timeout=app.config.get("API_TIMEOUT", 10),
                api_keys=app.config.get("COINGECKO_API_KEYS", []),
            )
        except cg.CoinGeckoRateLimit:
            stats = {}
            flash("Data pasar mungkin tidak terbaru (rate limit).", "warning")
        except cg.CoinGeckoServiceError:
            stats = {}
        return render_template(
            "index.html",
            global_data=stats,
            format_market_cap=format_market_cap,
            format_number=format_number,
            # Pagination defaults untuk template
            page=1,
            per_page=20,
            order="market_cap_desc",
            coins=[],
            is_search=False,
            search_query="",
            search_results=None,
            signal_filter=None,
            user_signals={},
            user_watchlist_ids=[],
            total_pages=1,
        )

    @app.route("/market")
    def market():
        """Halaman data API CoinGecko — publik, min 20 koin."""
        page, per_page = V.validate_pagination(
            request.values.get("page", "1"),
            request.values.get("per_page", "20"),
        )
        order = V.validate_sort_order(request.values.get("order", "market_cap_desc"))
        search_query = request.values.get("search", "").strip()

        cache_key_ns = "coins"
        cached = cache.get(cache_key_ns, order=order, page=page, per_page=per_page)
        if cached is not None:
            coins = cached
        else:
            try:
                coins = cg.fetch_coins(
                    api_key=app.config.get("COINGECKO_API_KEY", ""),
                    api_keys=app.config.get("COINGECKO_API_KEYS", []),
                    timeout=app.config.get("API_TIMEOUT", 10),
                    per_page=per_page,
                    page=page,
                    order=order,
                )
                cache.set(
                    cache_key_ns, coins,
                    ttl=app.config.get("MARKET_CACHE_TTL", 300),
                    order=order, page=page, per_page=per_page,
                )
            except cg.CoinGeckoServiceError:
                coins = []
                flash("Data pasar tidak tersedia (rate limit CoinGecko). Silakan coba beberapa saat lagi.", "warning")

        # Search (bukan dari cache)
        if search_query:
            try:
                results = cg.fetch_search(
                    api_key=app.config.get("COINGECKO_API_KEY", ""),
                    api_keys=app.config.get("COINGECKO_API_KEYS", []),
                    timeout=app.config.get("API_TIMEOUT", 10),
                    query=search_query,
                )
            except cg.CoinGeckoServiceError:
                results = []
        else:
            results = None

        user_watchlist_ids = []
        if current_user.is_authenticated:
            user_watchlist_ids = [w.coin_id for w in current_user.watchlist.all()]

        return render_template(
            "market.html",
            coins=coins,
            search_query=search_query,
            search_results=results,
            page=page,
            per_page=per_page,
            order=order,
            user_watchlist_ids=user_watchlist_ids,
            format_market_cap=format_market_cap,
            format_number=format_number,
            is_search=False,
            signal_filter=None,
            user_signals={},
            total_pages=1,
        )

    @app.route("/coin/<coin_id>")
    def coin_detail(coin_id: str):
        """Halaman detail koin — chart + ML indicators."""
        days = V.validate_chart_days(request.values.get("days", "7"))

        # Fetch price history (untuk chart + ML)
        try:
            history_data = cg.fetch_price_history(
                api_key=app.config.get("COINGECKO_API_KEY", ""),
                    api_keys=app.config.get("COINGECKO_API_KEYS", []),
                timeout=app.config.get("API_TIMEOUT", 10),
                coin_id=coin_id,
                days=days,
            )
            price_points = history_data.get("prices", [])
        except cg.CoinGeckoServiceError as e:
            price_points = []
            flash(f"Gagal mengambil data harga: {e}", "error")

        # ML prediction — dari data yang SUDAH ada (tidak fetch ulang)
        adv = None
        if price_points and len(price_points) >= 7:
            try:
                adv = get_advanced_prediction_from_data(price_points, days_ahead=7)
            except Exception as e:
                app.logger.warning("ML prediction failed for %s: %s", coin_id, e)

        # Market data untuk stats
        try:
            coin_data = cg.fetch_coin_detail(
                api_key=app.config.get("COINGECKO_API_KEY", ""),
                    api_keys=app.config.get("COINGECKO_API_KEYS", []),
                timeout=app.config.get("API_TIMEOUT", 10),
                coin_id=coin_id,
            )
        except cg.CoinGeckoServiceError:
            flash("Gagal mengambil data koin. Kemungkinan rate limit CoinGecko. Coba lagi nanti.", "error")
            return redirect(url_for("market"))

        in_watchlist = False
        if current_user.is_authenticated and coin_id:
            in_watchlist = (
                db.session.query(Watchlist)
                .filter_by(user_id=current_user.id, coin_id=coin_id)
                .first()
            ) is not None

        # Extract flat vars from nested market_data
        mkt = coin_data.get("market_data", {}) or {}
        current_price = mkt.get("current_price", {})
        price_change_24h = mkt.get("price_change_percentage_24h_in_currency", {}).get("usd", 0) or 0
        market_cap = mkt.get("market_cap", {})
        total_volume = mkt.get("total_volume", {})
        circulating_supply = mkt.get("circulating_supply", 0)
        ath = mkt.get("ath", {})
        atl = mkt.get("atl", {})
        market_extra = {
            "ath_date": mkt.get("ath_date", {}).get("usd", ""),
            "atl_date": mkt.get("atl_date", {}).get("usd", ""),
            "high_24h": mkt.get("high_24h", {}).get("usd", 0),
            "low_24h": mkt.get("low_24h", {}).get("usd", 0),
            "max_supply": mkt.get("max_supply", 0),
        }

        return render_template(
            "detail.html",
            coin=coin_data,
            coin_id=coin_id,
            price_points=price_points,
            chart_days=days,
            adv=adv,
            in_watchlist=in_watchlist,
            current_price=current_price,
            price_change_24h=price_change_24h,
            market_cap=market_cap,
            total_volume=total_volume,
            circulating_supply=circulating_supply,
            ath=ath,
            atl=atl,
            market_extra=market_extra,
            format_number=format_number,
            format_market_cap=format_market_cap,
        )

    @app.route("/about")
    def about():
        return render_template("about.html")

    # ── Auth ───────────────────────────────────────────────

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            confirm = request.form.get("confirm_password", "")

            errors = []

            # Validasi
            v_user = V.validate_username(username)
            if v_user:
                errors.append(v_user.message)
            else:
                if db.session.query(User).filter_by(username=username).first():
                    errors.append("Username sudah digunakan.")

            # Email uniqueness check only (no format validation)
            if db.session.query(User).filter_by(email=email).first():
                errors.append("Email sudah digunakan.")

            v_pass = V.validate_password_register(password)
            if v_pass:
                errors.append(v_pass.message)

            if password != confirm:
                errors.append("Konfirmasi password tidak cocok.")

            if errors:
                for e in errors:
                    flash(e, "error")
            else:
                user = User(username=username, email=email)
                user.set_password(password)
                user.is_approved = False
                user.is_admin = False
                db.session.add(user)
                try:
                    db.session.commit()
                    flash(
                        "Registrasi berhasil! Akun Anda menunggu approval dari admin.",
                        "success",
                    )
                    return redirect(url_for("login"))
                except Exception as e:
                    db.session.rollback()
                    flash("Terjadi kesalahan database. Silakan coba lagi.", "error")

        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")

            if not username or not password:
                flash("Username dan password wajib diisi.", "error")
                return render_template("login.html")

            user = db.session.query(User).filter_by(username=username).first()

            if not user or not user.check_password(password):
                flash("Username atau password salah.", "error")
                return render_template("login.html")

            if not user.is_approved:
                flash(
                    "Akun Anda belum disetujui admin. "
                    "Silakan tunggu atau hubungi administrator.",
                    "error",
                )
                return render_template("login.html")

            login_user(user, remember=False)
            next_target = get_safe_next()
            return redirect(next_target or url_for("dashboard"))

        return render_template("login.html")

    @app.route("/logout", methods=["POST"])
    @login_required
    def logout():
        logout_user()
        flash("Anda sudah logout.", "success")
        return redirect(url_for("index"))

    # ── Theme Toggle ───────────────────────────────────────

    @app.route("/theme", methods=["POST"])
    def theme():
        """Toggle theme via POST — tidak mengubah state melalui GET."""
        current = session.get("theme", "light")
        session["theme"] = "dark" if current == "light" else "light"
        next_target = get_safe_next()
        return redirect(next_target or request.referrer or url_for("index"))

    # ── Authenticated Pages ───────────────────────────────

    @app.route("/dashboard")
    @login_required
    def dashboard():
        watchlist = current_user.watchlist.all()
        coin_ids = [w.coin_id for w in watchlist]

        watchlist_coins = []
        if coin_ids:
            try:
                watchlist_coins = cg.fetch_market_by_ids(
                    api_key=app.config.get("COINGECKO_API_KEY", ""),
                    api_keys=app.config.get("COINGECKO_API_KEYS", []),
                    timeout=app.config.get("API_TIMEOUT", 10),
                    coin_ids=coin_ids,
                )
                for coin in watchlist_coins:
                    try:
                        hist = cg.fetch_price_history(
                            api_key=app.config.get("COINGECKO_API_KEY", ""),
                    api_keys=app.config.get("COINGECKO_API_KEYS", []),
                            timeout=app.config.get("API_TIMEOUT", 10),
                            coin_id=coin["id"],
                            days=30,
                        )
                        pp = hist.get("prices", [])
                        if len(pp) >= 7:
                            coin["prediction"] = get_advanced_prediction_from_data(pp, days_ahead=7)
                    except cg.CoinGeckoServiceError:
                        coin["prediction"] = None
            except cg.CoinGeckoServiceError:
                watchlist_coins = []

        try:
            global_data = cg.fetch_global_stats(
                api_key=app.config.get("COINGECKO_API_KEY", ""),
                timeout=app.config.get("API_TIMEOUT", 10),
                api_keys=app.config.get("COINGECKO_API_KEYS", []),
            )
        except cg.CoinGeckoServiceError:
            global_data = {}

        try:
            trending = cg.fetch_trending(
                api_key=app.config.get("COINGECKO_API_KEY", ""),
                timeout=app.config.get("API_TIMEOUT", 10),
                api_keys=app.config.get("COINGECKO_API_KEYS", []),
            )
        except cg.CoinGeckoServiceError:
            trending = []

        return render_template(
            "dashboard.html",
            watchlist_coins=watchlist_coins,
            global_data=global_data,
            trending_coins=trending,
            format_number=format_number,
            format_market_cap=format_market_cap,
        )

    @app.route("/watchlist/add/<coin_id>", methods=["POST"])
    @login_required
    def watchlist_add(coin_id: str):
        existing = db.session.query(Watchlist).filter_by(
            user_id=current_user.id, coin_id=coin_id
        ).first()
        if not existing:
            w = Watchlist(user_id=current_user.id, coin_id=coin_id)
            db.session.add(w)
            try:
                db.session.commit()
                flash(f"'{coin_id}' ditambahkan ke watchlist.", "success")
            except Exception:
                db.session.rollback()
                flash("Gagal menambah watchlist.", "error")
        next_target = get_safe_next()
        return redirect(next_target or url_for("dashboard"))

    @app.route("/watchlist/remove/<coin_id>", methods=["POST"])
    @login_required
    def watchlist_remove(coin_id: str):
        db.session.query(Watchlist).filter_by(
            user_id=current_user.id, coin_id=coin_id
        ).delete()
        try:
            db.session.commit()
            flash(f"'{coin_id}' dihapus dari watchlist.", "success")
        except Exception:
            db.session.rollback()
            flash("Gagal menghapus watchlist.", "error")
        next_target = get_safe_next()
        return redirect(next_target or url_for("dashboard"))

    @app.route("/profile", methods=["GET", "POST"])
    @login_required
    def profile():
        if request.method == "POST":
            new_username = request.form.get("username", "").strip()
            new_email = request.form.get("email", "").strip().lower()

            errors = []
            v_user = V.validate_username(new_username)
            if v_user:
                errors.append(v_user.message)
            else:
                dup = db.session.query(User).filter(
                    User.username == new_username,
                    User.id != current_user.id,
                ).first()
                if dup:
                    errors.append("Username sudah digunakan.")

            dup = db.session.query(User).filter(
                User.email == new_email,
                User.id != current_user.id,
            ).first()
            if dup:
                errors.append("Email sudah digunakan.")

            if errors:
                for e in errors:
                    flash(e, "error")
            else:
                current_user.username = new_username
                current_user.email = new_email
                try:
                    db.session.commit()
                    flash("Profil berhasil diperbarui.", "success")
                except Exception:
                    db.session.rollback()
                    flash("Gagal memperbarui profil.", "error")

        return render_template("profile.html")

    @app.route("/change-password", methods=["GET", "POST"])
    @login_required
    def change_password():
        if request.method == "POST":
            old = request.form.get("current_password", "")
            new = request.form.get("new_password", "")
            confirm = request.form.get("confirm_password", "")

            errors = V.validate_password_change(old, new, confirm)
            if errors:
                for e in errors:
                    flash(e.message, "error")
            else:
                if not current_user.check_password(old):
                    flash("Password lama salah.", "error")
                elif new == old:
                    flash("Password baru harus berbeda dari password lama.", "error")
                else:
                    current_user.set_password(new)
                    try:
                        db.session.commit()
                        flash("Password berhasil diubah. Silakan login ulang.", "success")
                        logout_user()
                        return redirect(url_for("login"))
                    except Exception:
                        db.session.rollback()
                        flash("Gagal mengubah password.", "error")

        return render_template("change_password.html")

    # ── Admin ─────────────────────────────────────────────

    @app.route("/admin")
    @admin_required
    def admin():
        pending = (
            db.session.query(User)
            .filter_by(is_approved=False)
            .order_by(User.created_at.desc())
            .all()
        )
        approved = (
            db.session.query(User)
            .filter_by(is_approved=True)
            .order_by(User.created_at.desc())
            .limit(50)
            .all()
        )
        return render_template("admin.html", pending_users=pending, approved_users=approved)

    @app.route("/admin/create-user", methods=["POST"])
    @admin_required
    def admin_create_user():
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        make_admin = request.form.get("make_admin") == "on"

        errors = []
        v_user = V.validate_username(username)
        if v_user:
            errors.append(v_user.message)
        else:
            if db.session.query(User).filter_by(username=username).first():
                errors.append("Username sudah digunakan.")

        # Email uniqueness check only (no format validation)
        if db.session.query(User).filter_by(email=email).first():
            errors.append("Email sudah digunakan.")

        v_pass = V.validate_password_register(password)
        if v_pass:
            errors.append(v_pass.message)

        if errors:
            for e in errors:
                flash(e, "error")
            return redirect(url_for("admin"))

        user = User(username=username, email=email)
        user.set_password(password)
        user.is_approved = True
        user.is_admin = make_admin
        db.session.add(user)
        try:
            db.session.commit()
            flash(f"User '{username}' dibuat. {'Admin access granted.' if make_admin else ''}", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Gagal membuat user: {e}", "error")

        return redirect(url_for("admin"))

    @app.route("/admin/edit-user/<int:user_id>", methods=["GET", "POST"])
    @admin_required
    def admin_edit_user(user_id: int):
        user = db.session.get(User, user_id)
        if not user:
            flash("User tidak ditemukan.", "error")
            return redirect(url_for("admin"))

        if request.method == "POST":
            new_username = request.form.get("username", "").strip()
            new_email = request.form.get("email", "").strip().lower()
            new_password = request.form.get("password", "")
            make_admin = request.form.get("make_admin") == "on"

            errors = []
            v_user = V.validate_username(new_username)
            if v_user:
                errors.append(v_user.message)
            else:
                dup = db.session.query(User).filter(
                    User.username == new_username, User.id != user_id
                ).first()
                if dup:
                    errors.append("Username sudah digunakan.")

            # Email uniqueness check only (no format validation)
            dup = db.session.query(User).filter(
                User.email == new_email, User.id != user_id
            ).first()
            if dup:
                errors.append("Email sudah digunakan.")

            if errors:
                for e in errors:
                    flash(e, "error")
                return redirect(url_for("admin_edit_user", user_id=user_id))

            # Proteksi: tidak bisa menurunkan hak admin diri sendiri
            if user.is_admin and not make_admin and user.id == current_user.id:
                flash("Tidak dapat menurunkan hak admin akun sendiri.", "error")
                return redirect(url_for("admin_edit_user", user_id=user_id))

            # Proteksi: tidak bisa menurunkan admin terakhir
            if user.is_admin and not make_admin and count_active_admins() <= 1:
                flash("Admin terakhir tidak dapat diturunkan.", "error")
                return redirect(url_for("admin_edit_user", user_id=user_id))

            user.username = new_username
            user.email = new_email
            user.is_admin = make_admin
            if new_password:
                if len(new_password) < 8:
                    flash("Password minimal 8 karakter.", "error")
                    return redirect(url_for("admin_edit_user", user_id=user_id))
                user.set_password(new_password)

            try:
                db.session.commit()
                flash(f"User '{user.username}' diperbarui.", "success")
            except Exception:
                db.session.rollback()
                flash("Gagal memperbarui user.", "error")

            return redirect(url_for("admin"))

        return render_template("admin_edit.html", edit_user=user)

    @app.route("/admin/approve/<int:user_id>", methods=["POST"])
    @admin_required
    def admin_approve(user_id: int):
        user = db.session.get(User, user_id)
        if not user:
            flash("User tidak ditemukan.", "error")
            return redirect(url_for("admin"))
        user.is_approved = True
        try:
            db.session.commit()
            flash(f"User '{user.username}' disetujui.", "success")
        except Exception:
            db.session.rollback()
            flash("Gagal menyetujui user.", "error")
        return redirect(url_for("admin"))

    @app.route("/admin/reject/<int:user_id>", methods=["POST"])
    @admin_required
    def admin_reject(user_id: int):
        user = db.session.get(User, user_id)
        if not user:
            flash("User tidak ditemukan.", "error")
            return redirect(url_for("admin"))
        if user.is_approved:
            flash("User yang sudah disetujui tidak dapat ditolak.", "error")
            return redirect(url_for("admin"))
        if user.is_admin:
            flash("Tidak dapat menolak admin.", "error")
            return redirect(url_for("admin"))
        if user.id == current_user.id:
            flash("Tidak dapat menolak diri sendiri.", "error")
            return redirect(url_for("admin"))
        db.session.delete(user)
        try:
            db.session.commit()
            flash(f"User '{user.username}' ditolak dan dihapus.", "error")
        except Exception:
            db.session.rollback()
            flash("Gagal menolak user.", "error")
        return redirect(url_for("admin"))

    @app.route("/admin/toggle-admin/<int:user_id>", methods=["POST"])
    @admin_required
    def admin_toggle_admin(user_id: int):
        user = db.session.get(User, user_id)
        if not user:
            flash("User tidak ditemukan.", "error")
            return redirect(url_for("admin"))
        if user.id == current_user.id:
            flash("Tidak dapat mengubah role diri sendiri.", "error")
            return redirect(url_for("admin"))

        # Lindungi admin terakhir
        if user.is_admin and count_active_admins() <= 1:
            flash("Tidak dapat mengubah role admin terakhir.", "error")
            return redirect(url_for("admin"))

        user.is_admin = not user.is_admin
        status = "promoted to admin" if user.is_admin else "removed from admin"
        try:
            db.session.commit()
            flash(f"User '{user.username}' {status}.", "success")
        except Exception:
            db.session.rollback()
            flash("Gagal mengubah role.", "error")
        return redirect(url_for("admin"))

    @app.route("/admin/delete-user/<int:user_id>", methods=["POST"])
    @admin_required
    def admin_delete_user(user_id: int):
        user = db.session.get(User, user_id)
        if not user:
            flash("User tidak ditemukan.", "error")
            return redirect(url_for("admin"))
        if user.id == current_user.id:
            flash("Tidak dapat menghapus diri sendiri.", "error")
            return redirect(url_for("admin"))
        if user.is_admin and count_active_admins() <= 1:
            flash("Tidak dapat menghapus admin terakhir.", "error")
            return redirect(url_for("admin"))

        Watchlist.query.filter_by(user_id=user.id).delete()
        db.session.delete(user)
        try:
            db.session.commit()
            flash(f"User '{user.username}' dihapus.", "error")
        except Exception:
            db.session.rollback()
            flash("Gagal menghapus user.", "error")
        return redirect(url_for("admin"))


# ─── Run ────────────────────────────────────────────────────

if __name__ == "__main__":
    _app = create_app()

    # CLI: create-admin
    @_app.cli.command("create-admin")
    def create_admin():
        """Buat admin user via CLI. Usage: flask create-admin"""
        import getpass
        print("=" * 50)
        print("CryptoTracker BMZ — Create Admin Account")
        print("=" * 50)
        username = input("Username (min. 3 chars): ").strip()
        if not username or len(username) < 3:
            print("[ERROR] Username minimal 3 karakter.")
            return
        email = input("Email: ").strip().lower()
        password = getpass.getpass("Password (min. 8 chars): ")
        if len(password) < 8:
            print("[ERROR] Password minimal 8 karakter.")
            return
        confirm = getpass.getpass("Konfirmasi password: ")
        if password != confirm:
            print("[ERROR] Password tidak cocok.")
            return
        with _app.app_context():
            if db.session.query(User).filter_by(username=username).first():
                print(f"[ERROR] Username '{username}' sudah digunakan.")
                return
            if db.session.query(User).filter_by(email=email).first():
                print(f"[ERROR] Email '{email}' sudah digunakan.")
                return
            user = User(username=username, email=email)
            user.set_password(password)
            user.is_admin = True
            user.is_approved = True
            db.session.add(user)
            try:
                db.session.commit()
                print(f"[OK] Admin '{username}' berhasil dibuat.")
            except Exception as e:
                db.session.rollback()
                print(f"[ERROR] Gagal membuat admin: {e}")

    port = int(os.getenv("PORT", 5050))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    _app.run(debug=debug, host="0.0.0.0", port=port)
