"""
pytest configuration and fixtures for CryptoTracker BMZ.
Uses :memory: SQLite for complete test isolation.
"""
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from extensions import db
from models import User, Watchlist


@pytest.fixture(scope="function")
def app():
    """Create test app with in-memory SQLite database per test."""
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-12345"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["COINGECKO_API_KEY"] = ""
    os.environ["AUTO_CREATE_DEFAULT_ADMIN"] = "false"
    os.environ["FLASK_DEBUG"] = "false"

    with patch("app.ensure_default_admin"):
        from app import create_app
        application = create_app()

    application.config["TESTING"] = True
    # Disable CSRF after create_app() via Flask-WTF extension method
    application.extensions["csrf"]._csrf_protected = False

    with application.app_context():
        db.create_all()

        admin = User(username="testadmin", email="testadmin@example.com")
        admin.set_password("AdminPass1")
        admin.is_admin = True
        admin.is_approved = True
        db.session.add(admin)

        user = User(username="testuser", email="testuser@example.com")
        user.set_password("UserPass123")
        user.is_admin = False
        user.is_approved = True
        db.session.add(user)

        pending = User(username="pendinguser", email="pending@example.com")
        pending.set_password("Pending123")
        pending.is_admin = False
        pending.is_approved = False
        db.session.add(pending)

        db.session.commit()

    yield application

    try:
        with application.app_context():
            from sqlalchemy.orm import close_all_sessions
            close_all_sessions()
            db.engine.dispose()
    except Exception:
        pass


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_client(client):
    client.post("/login", data={
        "username": "testadmin",
        "password": "AdminPass1",
    })
    return client


@pytest.fixture
def user_client(client):
    client.post("/login", data={
        "username": "testuser",
        "password": "UserPass123",
    })
    return client
