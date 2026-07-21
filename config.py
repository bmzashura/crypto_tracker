"""
Konfigurasi aplikasi CryptoTracker BMZ.
Semua nilai sensitif dibaca dari environment variable.
"""
import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    """Konfigurasi dasar aplikasi."""

    # ─── Secret & Security ────────────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY", "").strip()
    if not SECRET_KEY:
        raise ValueError(
            "SECRET_KEY environment variable belum diset. "
            "Buat file .env dan isi SECRET_KEY dengan nilai acak."
        )

    # ─── Database ────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'instance' / 'users.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ─── Session ─────────────────────────────────────────
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = (
        os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    )
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # ─── API ─────────────────────────────────────────────
    _key1 = os.getenv("COINGECKO_API_KEY", "").strip()
    _key2 = os.getenv("COINGECKO_API_KEY_2", "").strip()
    COINGECKO_API_KEYS = [_k for _k in [_key1, _key2] if _k] or [""]
    COINGECKO_API_KEY = _key1  # backward compat
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "10"))

    # ─── Cache TTL (detik) ───────────────────────────────
    MARKET_CACHE_TTL = int(os.getenv("MARKET_CACHE_TTL", "120"))       # 2 menit
    DETAIL_CACHE_TTL = int(os.getenv("DETAIL_CACHE_TTL", "300"))       # 5 menit
    HISTORY_CACHE_TTL = int(os.getenv("HISTORY_CACHE_TTL", "600"))     # 10 menit
    PREDICTION_CACHE_TTL = int(os.getenv("PREDICTION_CACHE_TTL", "3600"))  # 1 jam

    # ─── Default Admin ───────────────────────────────────
    DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "admin").strip()
    DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.local").strip().lower()
    DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "Admin1234")
    AUTO_CREATE_DEFAULT_ADMIN = (
        os.getenv("AUTO_CREATE_DEFAULT_ADMIN", "true").lower() == "true"
    )

    # ─── Flask Run ────────────────────────────────────────
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    PORT = int(os.getenv("PORT", "5050"))


class DevelopmentConfig(Config):
    """Konfigurasi untuk development."""
    DEBUG = True


class ProductionConfig(Config):
    """Konfigurasi untuk production."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": Config,
}

FLASK_ENV = os.getenv("FLASK_ENV", "default")
_current_config = config_by_name.get(FLASK_ENV, Config)

# Export sebagai dict untuk Flask.from_object / ekspos langsung
globals().update({
    k: getattr(_current_config, k)
    for k in dir(_current_config)
    if not k.startswith("_")
})
