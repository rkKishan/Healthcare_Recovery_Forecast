"""
Shared test fixtures.

Every test gets a fresh app on an in-memory database, so tests cannot leak
state into each other or touch the developer's real `data/app.db`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app import create_app  # noqa: E402
from backend.config import Config  # noqa: E402
from backend.models import User, db  # noqa: E402


class TestConfig(Config):
    TESTING = True
    DEBUG = True  # keeps verify_production_config out of the way

    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

    # Building the SHAP explainer costs about a second and no auth test needs
    # it; the ML tests construct the predictor themselves.
    WARM_EXPLAINER = False

    # Rate limits are asserted explicitly in test_auth.py by re-enabling them
    # on a dedicated app. Leaving them on globally would make any test that
    # logs in more than five times fail for the wrong reason.
    RATELIMIT_ENABLED = False

    # Config reads these from the environment, so a developer with a real
    # .env would otherwise run a different suite from CI -- configuring
    # Google sign-in locally made two "disabled by default" tests fail on
    # that machine alone. Pin them; the tests that need either one configured
    # set it explicitly on their own app.
    GOOGLE_CLIENT_ID = ""
    GOOGLE_ALLOWED_DOMAINS: list[str] = []
    ASSISTANT_API_KEY = ""


@pytest.fixture
def app(tmp_path):
    class _Config(TestConfig):
        UPLOAD_DIR = tmp_path / "uploads"

    application = create_app(_Config)
    yield application

    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def demo_credentials(app):
    return {
        "email": app.config["DEMO_EMAIL"].lower(),
        "password": app.config["DEMO_PASSWORD"],
    }


@pytest.fixture
def auth_headers(client, demo_credentials):
    """Authorization header for the seeded demo (admin) account."""
    response = client.post("/api/auth/login", json=demo_credentials)
    assert response.status_code == 200, response.get_json()
    return {"Authorization": f"Bearer {response.get_json()['access_token']}"}


def _login(client, email: str, password: str) -> dict:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.get_json()
    return {"Authorization": f"Bearer {response.get_json()['access_token']}"}


@pytest.fixture
def doctor_headers(client, app):
    """Auth header for the seeded doctor account."""
    return _login(
        client, app.config["DEMO_DOCTOR_EMAIL"].lower(), app.config["DEMO_PASSWORD"]
    )


@pytest.fixture
def analyst_headers(client, app):
    """Auth header for the seeded analyst account."""
    return _login(
        client, app.config["DEMO_ANALYST_EMAIL"].lower(), app.config["DEMO_PASSWORD"]
    )


@pytest.fixture
def other_user(app, client):
    """
    A second, unrelated account plus its auth header.

    Used to prove that one user cannot reach another user's data.
    """
    payload = {
        "email": "second.clinician@hospital.org",
        "password": "another-password",
        "full_name": "Dr. Sam Reyes",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201, response.get_json()
    body = response.get_json()
    return {
        "user": body["user"],
        "headers": {"Authorization": f"Bearer {body['access_token']}"},
    }


@pytest.fixture
def sample_csv() -> bytes:
    """A small, valid admissions extract matching the training schema."""
    path = Path(__file__).resolve().parent.parent / "data" / "sample_admissions.csv"
    lines = path.read_text().splitlines()
    return ("\n".join(lines[:41]) + "\n").encode()


def user_count() -> int:
    return User.query.count()
