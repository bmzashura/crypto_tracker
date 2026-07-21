"""
Validators untuk input form CryptoTracker BMZ.
Import-friendly, bisa digunakan di semua route.
"""
import re
from typing import Optional

try:
    from email_validator import validate_email as _ev_validate, EmailNotValidError
    HAS_EMAIL_VALIDATOR = True
except ImportError:
    HAS_EMAIL_VALIDATOR = False

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_\-.]{3,30}$")


class ValidationError:
    """Error object untuk validasi."""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message

    def __str__(self):
        return self.message


def validate_username(username: str) -> Optional[ValidationError]:
    """
    Validasi username.
    Pattern: 3-30 karakter, alphanumeric + _ . -
    """
    if not username:
        return ValidationError("username", "Username wajib diisi.")
    if not USERNAME_PATTERN.match(username):
        return ValidationError(
            "username",
            "Username hanya boleh berisi huruf, angka, titik (.), "
            "garis bawah (_), dan tanda minus (-), dengan panjang 3–30 karakter.",
        )
    return None


def validate_email(email: str) -> Optional[ValidationError]:
    """
    Validasi format email menggunakan email-validator (atau regex fallback).
    Normalisasi: lowercase + strip whitespace.
    """
    if not email:
        return ValidationError("email", "Email wajib diisi.")
    normalized = email.strip().lower()
    if HAS_EMAIL_VALIDATOR:
        try:
            _ev_validate(normalized)
            return None
        except EmailNotValidError as e:
            return ValidationError("email", f"Email tidak valid: {e}")
    else:
        # Fallback: simple regex check
        simple_pattern = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
        if not simple_pattern.match(normalized):
            return ValidationError("email", "Format email tidak valid.")
        return None


def validate_password_register(password: str) -> Optional[ValidationError]:
    """Validasi password saat registrasi. Min 8 karakter."""
    if not password:
        return ValidationError("password", "Password wajib diisi.")
    if len(password) < 8:
        return ValidationError("password", "Password minimal 8 karakter.")
    return None


def validate_password_change(
    old_password: str,
    new_password: str,
    confirm_password: str,
) -> list[ValidationError]:
    """
    Validasi perubahan password.
    Returns list of errors (bisa kosong).
    """
    errors = []
    if not old_password:
        errors.append(ValidationError("current_password", "Password lama wajib diisi."))
    if not new_password:
        errors.append(ValidationError("new_password", "Password baru wajib diisi."))
    elif len(new_password) < 8:
        errors.append(ValidationError("new_password", "Password baru minimal 8 karakter."))
    if new_password and confirm_password != new_password:
        errors.append(ValidationError("confirm_password", "Konfirmasi password tidak cocok."))
    return errors


def validate_pagination(page: str, per_page: str) -> tuple[int, int]:
    """
    Validasi dan sanitasi parameter pagination.
    Returns (page, per_page) dengan nilai aman.
    """
    try:
        page = max(1, int(page or "1"))
    except (ValueError, TypeError):
        page = 1

    try:
        per_page = int(per_page or "20")
    except (ValueError, TypeError):
        per_page = 20

    # Batasi nilai yang diizinkan
    if per_page not in (10, 20, 50):
        per_page = 20
    per_page = max(10, min(50, per_page))

    return page, per_page


ALLOWED_SORT_ORDERS = {
    "market_cap_desc", "market_cap_asc",
    "volume_desc", "volume_asc",
    "id_asc", "id_desc",
    "trending",
}


def validate_sort_order(order: str) -> str:
    """Validasi sort order. Default: market_cap_desc."""
    if order not in ALLOWED_SORT_ORDERS:
        return "market_cap_desc"
    return order


def validate_chart_days(days: str) -> int:
    """Validasi rentang hari untuk chart. Hanya boleh 7, 30, atau 90."""
    try:
        days = int(days or "7")
    except (ValueError, TypeError):
        return 7
    if days not in (7, 30, 90):
        return 7
    return days
