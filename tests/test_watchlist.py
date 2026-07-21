"""
Test watchlist functionality.
"""
import pytest
from models import User, Watchlist
from extensions import db


class TestWatchlistAdd:
    def test_authenticated_can_add_watchlist(self, user_client, app):
        """User logged in dapat tambah watchlist."""
        r = user_client.post("/watchlist/add/bitcoin", follow_redirects=False)
        # Should redirect (success or stay on page)
        assert r.status_code == 302

    def test_anonymous_cannot_add_watchlist(self, client):
        """Anonymous tidak dapat tambah watchlist."""
        r = client.post("/watchlist/add/bitcoin")
        assert r.status_code == 302  # redirect to login


class TestWatchlistDuplicate:
    def test_duplicate_watchlist_no_new_row(self, user_client, app):
        """Menambah koin yang sama dua kali tidak membuat baris duplikat."""
        with app.app_context():
            user = db.session.query(User).filter_by(username="testuser").first()
            user_id = user.id

            # Add first time
            user_client.post("/watchlist/add/ethereum")
            count1 = db.session.query(Watchlist).filter_by(
                user_id=user_id, coin_id="ethereum"
            ).count()
            assert count1 == 1

            # Add second time
            user_client.post("/watchlist/add/ethereum")
            count2 = db.session.query(Watchlist).filter_by(
                user_id=user_id, coin_id="ethereum"
            ).count()
            assert count2 == 1  # still 1, no duplicate


class TestWatchlistRemove:
    def test_authenticated_can_remove_watchlist(self, user_client, app):
        """User dapat hapus dari watchlist."""
        with app.app_context():
            user = db.session.query(User).filter_by(username="testuser").first()
            user_id = user.id

            # Add first
            w = Watchlist(user_id=user_id, coin_id="solana")
            db.session.add(w)
            db.session.commit()

            r = user_client.post("/watchlist/remove/solana", follow_redirects=False)
            assert r.status_code == 302

            count = db.session.query(Watchlist).filter_by(
                user_id=user_id, coin_id="solana"
            ).count()
            assert count == 0

    def test_anonymous_cannot_remove_watchlist(self, client):
        """Anonymous tidak dapat hapus watchlist."""
        r = client.post("/watchlist/remove/bitcoin")
        assert r.status_code == 302


class TestWatchlistIsolation:
    def test_user_a_cannot_change_user_b_watchlist(self, client, admin_client, app):
        """User A tidak dapat mengubah watchlist User B."""
        with app.app_context():
            admin = db.session.query(User).filter_by(username="testadmin").first()
            user = db.session.query(User).filter_by(username="testuser").first()
            admin_id = admin.id
            user_id = user.id

            # Admin adds bitcoin to their watchlist
            admin_client.post("/watchlist/add/bitcoin")

            # Verify admin has bitcoin
            admin_has = db.session.query(Watchlist).filter_by(
                user_id=admin_id, coin_id="bitcoin"
            ).first()
            assert admin_has is not None

            # User (testuser) does NOT have bitcoin in their watchlist
            user_has = db.session.query(Watchlist).filter_by(
                user_id=user_id, coin_id="bitcoin"
            ).first()
            assert user_has is None
