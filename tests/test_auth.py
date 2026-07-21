"""
Test authentication flows.
"""
import pytest
from models import User
from extensions import db


class TestRegister:
    def test_register_valid(self, client, app):
        """Registrasi valid membuat user dengan is_approved=False."""
        r = client.post("/register", data={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "NewUser123",
            "confirm_password": "NewUser123",
        }, follow_redirects=False)
        assert r.status_code == 302
        with app.app_context():
            user = db.session.query(User).filter_by(username="newuser").first()
            assert user is not None
            assert user.is_approved is False
            assert user.is_admin is False

    def test_register_username_too_short(self, client):
        """Username kurang dari 3 karakter ditolak."""
        r = client.post("/register", data={
            "username": "ab",
            "email": "ab@example.com",
            "password": "Abcd1234",
            "confirm_password": "Abcd1234",
        }, follow_redirects=False)
        assert r.status_code == 200  # stays on register page

    def test_register_password_too_short(self, client):
        """Password kurang dari 8 karakter ditolak."""
        r = client.post("/register", data={
            "username": "testuser2",
            "email": "test2@example.com",
            "password": "short",
            "confirm_password": "short",
        }, follow_redirects=False)
        assert r.status_code == 200

    def test_register_duplicate_username(self, client):
        """Username duplikat ditolak."""
        r = client.post("/register", data={
            "username": "testuser",
            "email": "different@example.com",
            "password": "Different123",
            "confirm_password": "Different123",
        }, follow_redirects=False)
        assert r.status_code == 200

    def test_register_duplicate_email(self, client):
        """Email duplikat ditolak."""
        r = client.post("/register", data={
            "username": "differentuser",
            "email": "testuser@example.com",
            "password": "Different123",
            "confirm_password": "Different123",
        }, follow_redirects=False)
        assert r.status_code == 200

    def test_register_password_mismatch(self, client):
        """Konfirmasi password tidak cocok ditolak."""
        r = client.post("/register", data={
            "username": "mismatch",
            "email": "mismatch@example.com",
            "password": "Password1",
            "confirm_password": "Password2",
        }, follow_redirects=False)
        assert r.status_code == 200


class TestLogin:
    def test_login_valid_approved(self, client):
        """Approved user dapat login."""
        r = client.post("/login", data={
            "username": "testuser",
            "password": "UserPass123",
        }, follow_redirects=False)
        assert r.status_code == 302
        assert "/dashboard" in r.location

    def test_login_invalid_password(self, client):
        """Password salah ditolak."""
        r = client.post("/login", data={
            "username": "testuser",
            "password": "WrongPassword",
        }, follow_redirects=False)
        assert r.status_code == 200  # stays on login

    def test_login_nonexistent_user(self, client):
        """User tidak ada ditolak."""
        r = client.post("/login", data={
            "username": "nonexistent",
            "password": "AnyPassword123",
        }, follow_redirects=False)
        assert r.status_code == 200

    def test_login_pending_user_rejected(self, client):
        """Pending user tidak dapat login."""
        r = client.post("/login", data={
            "username": "pendinguser",
            "password": "Pending123",
        }, follow_redirects=False)
        assert r.status_code == 200
        assert b"belum disetujui" in r.data or b"not approved" in r.data.lower()


class TestLogout:
    def test_logout_post_only(self, client):
        """Logout hanya boleh via POST, GET tidak mengubah state."""
        # Login first
        client.post("/login", data={
            "username": "testuser",
            "password": "UserPass123",
        })
        # GET logout should return 405 or redirect without logging out
        r = client.get("/logout")
        assert r.status_code == 405  # Method Not Allowed
