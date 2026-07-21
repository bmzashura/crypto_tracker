# Changelog — CryptoTracker BMZ (UAS)

Semua perubahan dari baseline ke versi UAS final didokumentasikan di sini.

---

## [UAS Final] — 2026-07-20

### Added
- **`config.py`** — Konfigurasi berbasis environment variable (SECRET_KEY, DATABASE_URL, API_TIMEOUT, dll.)
- **`extensions.py`** — Ekstensi Flask terpusat (`db`, `login_manager`, `csrf`)
- **`models.py`** — SQLAlchemy models: `User` dan `Watchlist` dengan relationship dan unique constraint
- **`decorators.py`** — Decorator `admin_required` dan helper `safe_redirect`, `count_active_admins`
- **`validators.py`** — Validasi username, email, password, pagination, sort order, chart days
- **`services/cache_service.py`** — In-memory TTL cache singleton
- **`services/coingecko_service.py`** — Semua request CoinGecko dengan session, error handling terstruktur
- **Custom exception classes** — `CoinGeckoTimeout`, `CoinGeckoRateLimit`, `CoinGeckoAPIError`, `CoinGeckoDataError`
- **CSRF protection** — Semua form POST dilindungi Flask-WTF CSRFProtect
- **`/market` route** — Halaman data API eksplisit (route baru, terpisah dari `/`)
- **Safe redirect** — Validasi `next` parameter same-origin
- **`/theme` → POST** — Theme toggle berubah dari GET ke POST
- **`/logout` → POST** — Logout berubah dari GET ke POST
- **`flask create-admin` CLI** — Command untuk buat admin via terminal
- **Auto-create default admin** — `ensure_default_admin()` bootstrap saat startup
- **Admin last-admin protection** — `count_active_admins()` helper
- **Error handlers** — Custom 403/404/405/500 + CSRF error pages
- **`error.html` template** — Custom error page dengan Lucide icons
- **`admin_edit.html` template** — Form edit user oleh admin
- **`admin_create_user` route** — Buat user langsung approved oleh admin
- **ML timestamp fix** — `get_price_prediction_from_data()` dan `get_advanced_prediction_from_data()` menggunakan elapsed days dari timestamp
- **ML `confidence` → `trend_fit_label`** — R² tidak disebut "confidence" lagi
- **`calculate_rsi_status()`** — Fungsi terpisah, RSI 0 ditangani dengan benar sebagai "Oversold"
- **`calculate_sma()`** — Fix `0` falsy bug, gunakan `is not None`
- **Bollinger position text** — Interpretasi lebih netral (tidak "Strong Buy" otomatis)
- **`docs/UAS_DOCUMENTATION.md`** — Dokumentasi UAS lengkap
- **`docs/ENDPOINTS.md`** — Tabel semua endpoint
- **`docs/ERD.md`** — ERD dengan Mermaid
- **`docs/SCREENSHOT_CHECKLIST.md`** — Checklist screenshot untuk demo
- **`.env.example`** — Template environment variable
- **`.gitignore`** — Mengabaikan `.env`, `instance/*.db`, `__pycache__/`

### Changed
- **`app.py`** — Di-refactor dari 868 baris monolithic ke struktur modular dengan import dari `services/`, `models.py`, `config.py`, dll.
- **Secret management** — SECRET_KEY dan API key dipindahkan ke `.env`
- **`debug=True` → `debug=False`** — Default production-safe
- **Password hashing** — Konsisten menggunakan `werkzeug.security.generate_password_hash(method='pbkdf2:sha256')`
- **`detail.html`** — ML signal display sekarang menggunakan `adv.lr.confidence` (trend_fit_label)
- **`base.html`** — Theme toggle menggunakan POST form dengan CSRF, logout menggunakan POST

### Fixed
- **Open redirect** — Parameter `next` di login divalidasi same-origin
- **Watchlist unique constraint** — `UniqueConstraint(user_id, coin_id)` mencegah duplikat
- **Admin bootstrap deadlock** — Fresh install sekarang otomatis membuat admin default
- **RSI 0 bug** — RSI 0 sekarang correctly "Oversold", tidak di-falsy-check
- **SMA 0 bug** — SMA 0 sekarang returned sebagai `0.0`, bukan `None`
- **Prediction timestamp** — Forecast horizon sekarang menggunakan elapsed days, bukan indeks array
- **Double fetch ML** — `get_advanced_prediction_from_data()` tidak fetch API kedua kali
- **Session cookie** — `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SAMESITE='Lax'`

---

## [Baseline] — Sebelum Refactoring

Versi awal proyek dengan fitur:
- Flask monolithic (`app.py` 868 baris)
- Hardcoded SECRET_KEY dan API key
- Debug mode on
- Tidak ada CSRF protection
- GET untuk logout dan theme toggle
- Prediction menggunakan indeks bukan timestamp
- Tidak ada cache service
- Tidak ada modularisasi
- Error handling dengan `except Exception: pass`
