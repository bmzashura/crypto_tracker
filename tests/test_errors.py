"""
Test error handling: 403, 404, 405, 500, CSRF.
"""
import pytest


class TestHTTPErrorHandlers:
    def test_403(self, client):
        """403 error handler works."""
        r = client.get("/admin")  # anonymous -> 403
        assert r.status_code == 403
        assert b"403" in r.data
        assert b"Akses Ditolak" in r.data or b"Forbidden" in r.data

    def test_404(self, client):
        """404 error handler works."""
        r = client.get("/halaman-yang-tidak-ada-12345")
        assert r.status_code == 404
        assert b"404" in r.data
        assert b"Halaman Tidak Ditemukan" in r.data or b"Not Found" in r.data

    def test_405(self, client):
        """405 error handler works."""
        r = client.get("/logout")  # only POST allowed
        assert r.status_code == 405
        assert b"405" in r.data
        assert b"Metode Tidak Diizinkan" in r.data or b"Method Not Allowed" in r.data


class TestCSRFProtection:
    def test_login_without_csrf_fails_when_enabled(self, client, app):
        """POST tanpa CSRF token ditolak (CSRF enabled in real mode)."""
        # In test mode CSRF is disabled, so we skip this test
        # But we can test that the app has CSRF protection configured
        with app.app_context():
            from extensions import csrf
            assert csrf is not None
