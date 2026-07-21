"""
Test authorization: admin_required, role-based access.
"""
import pytest


class TestAnonymousAccess:
    def test_anonymous_cannot_dashboard(self, client):
        """Anonymous user tidak dapat akses dashboard."""
        r = client.get("/dashboard")
        assert r.status_code == 302  # redirect to login

    def test_anonymous_cannot_admin(self, client):
        """Anonymous user tidak dapat akses admin panel."""
        r = client.get("/admin")
        assert r.status_code == 403

    def test_anonymous_cannot_watchlist_add(self, client):
        """Anonymous tidak dapat tambah watchlist."""
        r = client.post("/watchlist/add/bitcoin")
        assert r.status_code == 302  # redirect to login

    def test_anonymous_cannot_profile(self, client):
        """Anonymous tidak dapat akses profile."""
        r = client.get("/profile")
        assert r.status_code == 302

    def test_public_routes_work(self, client):
        """Route publik dapat diakses anonymous."""
        assert client.get("/").status_code == 200
        assert client.get("/market").status_code == 200
        assert client.get("/about").status_code == 200
        assert client.get("/login").status_code == 200
        assert client.get("/register").status_code == 200


class TestUserAccess:
    def test_user_cannot_admin(self, user_client):
        """User biasa tidak dapat akses admin."""
        r = user_client.get("/admin")
        assert r.status_code == 403

    def test_user_can_dashboard(self, user_client):
        """User dapat akses dashboard."""
        r = user_client.get("/dashboard")
        assert r.status_code == 200

    def test_user_can_profile(self, user_client):
        """User dapat akses profile."""
        r = user_client.get("/profile")
        assert r.status_code == 200

    def test_user_can_watchlist_add(self, user_client):
        """User dapat tambah watchlist."""
        r = user_client.post("/watchlist/add/bitcoin")
        # Will redirect even if API fails (watchlist add is DB op)
        assert r.status_code in (302, 200)


class TestAdminAccess:
    def test_admin_can_admin(self, admin_client):
        """Admin dapat akses admin panel."""
        r = admin_client.get("/admin")
        assert r.status_code == 200

    def test_admin_can_dashboard(self, admin_client):
        """Admin dapat akses dashboard."""
        r = admin_client.get("/dashboard")
        assert r.status_code == 200
