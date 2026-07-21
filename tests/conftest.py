"""
pytest configuration and fixtures for CryptoTracker BMZ.
Uses temporary SQLite database per test for complete isolation.
"""
import os
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from extensions import db
from models import User, Watchlist


@pytest.fixture(scope="function")
def app(tmp_path):
    """Create test app with temporary SQLite database per test."""
    # Create temporary database file
    db_path = tmp_path / "test.db"

    with patch("app.ensure_default_admin"):
        from app import create_app
        application = create_app()

    application.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{db_path}",
        SERVER_NAME="localhost",
        SECRET_KEY="test-secret-key-for-testing-only-12345",
        COINGECKO_API_KEY="",
        AUTO_CREATE_DEFAULT_ADMIN="false",
        FLASK_DEBUG="false",
    )

    with application.app_context():
        db.drop_all()
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

    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def app_context(app):
    with app.app_context():
        yield


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
