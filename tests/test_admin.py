"""
Test admin CRUD operations.
"""
import pytest
from models import User, Watchlist
from extensions import db


class TestAdminPanel:
    def test_admin_sees_pending_users(self, admin_client):
        """Admin panel menampilkan user pending."""
        r = admin_client.get("/admin")
        assert r.status_code == 200
        assert b"pendinguser" in r.data  # pending user visible

    def test_admin_sees_approved_users(self, admin_client):
        """Admin panel menampilkan user approved."""
        r = admin_client.get("/admin")
        assert r.status_code == 200
        assert b"testuser" in r.data


class TestAdminCreateUser:
    def test_admin_create_user_success(self, admin_client, app_context):
        """Admin dapat membuat user baru."""
        r = admin_client.post("/admin/create-user", data={
            "username": "newadmin",
            "email": "newadmin@example.com",
            "password": "NewAdmin123",
            "make_admin": "",
        }, follow_redirects=False)
        assert r.status_code == 302
        user = db.session.query(User).filter_by(username="newadmin").first()
        assert user is not None
        assert user.is_approved is True

    def test_admin_create_user_as_admin(self, admin_client, app_context):
        """Admin dapat membuat user dengan role admin."""
        r = admin_client.post("/admin/create-user", data={
            "username": "superadmin",
            "email": "superadmin@example.com",
            "password": "SuperAdmin123",
            "make_admin": "on",
        }, follow_redirects=False)
        assert r.status_code == 302
        user = db.session.query(User).filter_by(username="superadmin").first()
        assert user.is_admin is True


class TestAdminApprove:
    def test_admin_approve_pending_user(self, admin_client, app_context):
        """Admin dapat approve user pending."""
        pending = db.session.query(User).filter_by(username="pendinguser").first()
        assert pending.is_approved is False

        r = admin_client.post(f"/admin/approve/{pending.id}")
        assert r.status_code == 302

        db.session.expire(pending)
        assert pending.is_approved is True


class TestAdminReject:
    def test_admin_reject_pending_user(self, admin_client, app_context):
        """Admin dapat reject dan hapus user pending."""
        pending = db.session.query(User).filter_by(username="pendinguser").first()
        pending_id = pending.id

        r = admin_client.post(f"/admin/reject/{pending_id}")
        assert r.status_code == 302

        assert db.session.get(User, pending_id) is None


class TestAdminDelete:
    def test_admin_delete_user(self, admin_client, app_context):
        """Admin dapat menghapus user."""
        # Buat user untuk dihapus
        user = User(username="todelete", email="todelete@example.com")
        user.set_password("Delete123")
        user.is_approved = True
        db.session.add(user)
        db.session.commit()
        user_id = user.id

        r = admin_client.post(f"/admin/delete-user/{user_id}")
        assert r.status_code == 302
        assert db.session.get(User, user_id) is None

    def test_admin_cannot_delete_self(self, admin_client, app_context):
        """Admin tidak dapat menghapus dirinya sendiri."""
        admin = db.session.query(User).filter_by(username="testadmin").first()
        admin_id = admin.id

        r = admin_client.post(f"/admin/delete-user/{admin_id}")
        assert r.status_code == 302  # stays on admin (flash error)
        assert db.session.get(User, admin_id) is not None


class TestAdminLastProtection:
    def test_cannot_demote_last_admin(self, admin_client, app_context):
        """Admin terakhir tidak dapat di-demote."""
        admin = db.session.query(User).filter_by(username="testadmin").first()
        # testadmin is the only admin in this test setup
        r = admin_client.post(f"/admin/toggle-admin/{admin.id}")
        # Should redirect with error
        assert r.status_code == 302
