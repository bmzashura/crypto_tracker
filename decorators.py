"""
Custom decorators untuk CryptoTracker BMZ.
"""
from functools import wraps
from flask import abort
from flask_login import current_user
from urllib.parse import urlparse, urljoin


def admin_required(view):
    """
    Decorator: memastikan user sudah login, admin, dan approved.
    Jika tidak, abort 403.
    """
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)
        if not current_user.is_admin or not current_user.is_approved:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def safe_redirect(next_param: str = "next") -> str:
    """
    Validasi parameter redirect agar tidak ke domain eksternal.
    Returns validated redirect target, atau None jika tidak valid.
    """
    from flask import request
    raw = request.values.get(next_param, "")
    if not raw:
        return None
    parsed = urlparse(urljoin(request.url, raw))
    # Hanya izinkan redirect ke domain yang sama (same-origin)
    if parsed.netloc and parsed.netloc != request.host:
        return None
    return parsed.path + (("?" + parsed.query) if parsed.query else "")


def count_active_admins() -> int:
    """Hitung jumlah admin yang aktif (approved + is_admin)."""
    from models import User
    from extensions import db
    return db.session.query(User).filter(
        User.is_admin == True,
        User.is_approved == True,
    ).count()
