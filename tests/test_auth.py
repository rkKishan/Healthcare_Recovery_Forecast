"""Authentication, token handling, and the guarantees around account roles."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
import pytest

from backend.app import create_app
from backend.models import User
from backend.roles import (
    ANALYST,
    ANALYST_CAPABILITIES,
    DEFAULT_ROLE,
    DOCTOR,
)

from .conftest import TestConfig


class TestLogin:
    def test_valid_credentials_return_a_token_and_user(self, client, demo_credentials):
        response = client.post("/api/auth/login", json=demo_credentials)
        body = response.get_json()

        assert response.status_code == 200
        assert body["token_type"] == "bearer"
        assert body["access_token"]
        assert body["user"]["email"] == demo_credentials["email"]
        assert "password_hash" not in body["user"]

    def test_wrong_password_is_rejected(self, client, demo_credentials):
        response = client.post(
            "/api/auth/login",
            json={**demo_credentials, "password": "not-the-password"},
        )
        assert response.status_code == 401

    def test_unknown_email_is_rejected(self, client):
        response = client.post(
            "/api/auth/login",
            json={"email": "nobody@hospital.org", "password": "whatever12"},
        )
        assert response.status_code == 401

    def test_unknown_email_and_wrong_password_are_indistinguishable(
        self, client, demo_credentials
    ):
        """A differing message would let an attacker enumerate valid accounts."""
        wrong_password = client.post(
            "/api/auth/login",
            json={**demo_credentials, "password": "not-the-password"},
        ).get_json()
        unknown_email = client.post(
            "/api/auth/login",
            json={"email": "nobody@hospital.org", "password": "whatever12"},
        ).get_json()

        assert wrong_password["error"] == unknown_email["error"]

    def test_missing_fields_are_a_400_not_a_500(self, client):
        response = client.post("/api/auth/login", json={})
        assert response.status_code == 400
        assert "details" in response.get_json()


class TestProtectedRoutes:
    def test_me_returns_the_current_user(self, client, auth_headers, demo_credentials):
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        assert response.get_json()["user"]["email"] == demo_credentials["email"]

    def test_me_without_a_token_is_401(self, client):
        assert client.get("/api/auth/me").status_code == 401

    def test_malformed_header_is_401(self, client, auth_headers):
        token = auth_headers["Authorization"].removeprefix("Bearer ")
        # No "Bearer " scheme prefix.
        assert client.get("/api/auth/me", headers={"Authorization": token}).status_code == 401

    def test_garbage_token_is_401(self, client):
        response = client.get(
            "/api/auth/me", headers={"Authorization": "Bearer not-a-real-jwt"}
        )
        assert response.status_code == 401

    def test_expired_token_is_401(self, app, client):
        with app.app_context():
            expired = jwt.encode(
                {
                    "sub": "1",
                    "email": app.config["DEMO_EMAIL"],
                    "role": "admin",
                    "iat": datetime.now(UTC) - timedelta(hours=24),
                    "exp": datetime.now(UTC) - timedelta(hours=1),
                },
                app.config["SECRET_KEY"],
                algorithm=app.config["JWT_ALGORITHM"],
            )

        response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired}"})
        assert response.status_code == 401
        assert "expired" in response.get_json()["error"].lower()

    @pytest.mark.parametrize("subject", ["not-a-number", "", None, ["1"]])
    def test_malformed_subject_claim_is_401_not_500(self, app, client, subject):
        """A validly signed token can still carry a nonsense `sub`."""
        with app.app_context():
            token = jwt.encode(
                {
                    "sub": subject,
                    "iat": datetime.now(UTC),
                    "exp": datetime.now(UTC) + timedelta(hours=1),
                },
                app.config["SECRET_KEY"],
                algorithm=app.config["JWT_ALGORITHM"],
            )

        response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401

    def test_token_for_a_deleted_account_is_401(self, app, client, auth_headers):
        """The token outlives the row; the guard must notice."""
        from backend.models import User, db

        with app.app_context():
            user = db.session.get(User, 1)
            db.session.delete(user)
            db.session.commit()

        assert client.get("/api/auth/me", headers=auth_headers).status_code == 401

    def test_token_signed_with_another_key_is_401(self, app, client):
        """The signature is what makes the token trustworthy -- prove it is checked."""
        forged = jwt.encode(
            {
                "sub": "1",
                "email": "admin@hospital.org",
                "role": "admin",
                "iat": datetime.now(UTC),
                "exp": datetime.now(UTC) + timedelta(hours=1),
            },
            "a-different-signing-key",
            algorithm="HS256",
        )
        response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {forged}"})
        assert response.status_code == 401


class TestRegistration:
    def test_registration_creates_a_usable_account(self, client):
        response = client.post(
            "/api/auth/register",
            json={
                "email": "New.Clinician@Hospital.org",
                "password": "a-good-password",
                "full_name": "Dr. Robin Vale",
            },
        )
        assert response.status_code == 201
        # Email is normalised so it cannot be registered twice in two cases.
        assert response.get_json()["user"]["email"] == "new.clinician@hospital.org"

    def test_duplicate_email_is_rejected(self, client, demo_credentials):
        response = client.post(
            "/api/auth/register",
            json={
                "email": demo_credentials["email"],
                "password": "a-good-password",
                "full_name": "Impersonator",
            },
        )
        assert response.status_code == 409

    def test_short_password_is_rejected(self, client):
        response = client.post(
            "/api/auth/register",
            json={"email": "x@hospital.org", "password": "short", "full_name": "X"},
        )
        assert response.status_code == 400

    @pytest.mark.parametrize("claimed_role", ["admin", "superuser", "ADMIN"])
    def test_registrant_cannot_choose_a_privileged_role(self, app, client, claimed_role):
        """
        Regression test: `role` used to be read straight from the request body,
        so anyone able to reach /register could mint themselves an admin.

        A registrant may now pick between the two clinical roles, but anything
        outside that whitelist still falls back to the default rather than
        being honoured.
        """
        response = client.post(
            "/api/auth/register",
            json={
                "email": f"escalate-{claimed_role}@example.com",
                "password": "a-good-password",
                "full_name": "Mallory",
                "role": claimed_role,
            },
        )

        assert response.status_code == 201
        assert response.get_json()["user"]["role"] == DEFAULT_ROLE

        # The response body is not the only thing that matters -- check the row.
        # Registration normalises the address, so look it up the same way.
        with app.app_context():
            stored = User.query.filter_by(
                email=f"escalate-{claimed_role}@example.com".lower()
            ).first()
            assert stored is not None
            assert stored.role == DEFAULT_ROLE

    def test_escalated_role_does_not_leak_into_the_token(self, client):
        """The JWT carries the role, so it must not carry the claimed one."""
        body = client.post(
            "/api/auth/register",
            json={
                "email": "token-escalation@example.com",
                "password": "a-good-password",
                "full_name": "Mallory",
                "role": "admin",
            },
        ).get_json()

        claims = jwt.decode(body["access_token"], options={"verify_signature": False})
        assert claims["role"] == DEFAULT_ROLE
        assert claims["role"] != "admin"

    @pytest.mark.parametrize("chosen", [DOCTOR, ANALYST])
    def test_registrant_may_choose_a_clinical_role(self, client, chosen):
        response = client.post(
            "/api/auth/register",
            json={
                "email": f"{chosen}-signup@hospital.org",
                "password": "a-good-password",
                "full_name": "Sam Taylor",
                "role": chosen,
            },
        )

        assert response.status_code == 201
        assert response.get_json()["user"]["role"] == chosen

    def test_omitted_role_falls_back_to_the_default(self, client):
        response = client.post(
            "/api/auth/register",
            json={
                "email": "no-role@hospital.org",
                "password": "a-good-password",
                "full_name": "Sam Taylor",
            },
        )
        assert response.get_json()["user"]["role"] == DEFAULT_ROLE

    def test_the_user_payload_carries_its_capabilities(self, client):
        """The frontend builds its navigation from these, so they must ship."""
        body = client.post(
            "/api/auth/register",
            json={
                "email": "caps@hospital.org",
                "password": "a-good-password",
                "full_name": "Sam Taylor",
                "role": ANALYST,
            },
        ).get_json()

        assert set(body["user"]["capabilities"]) == set(ANALYST_CAPABILITIES)
        assert body["user"]["role_label"] == "Analyst"


class TestRateLimiting:
    """
    Rate limits are disabled for the rest of the suite, so this class builds
    its own app with them switched back on.

    These tests deliberately do NOT use the shared `app`/`demo_credentials`
    fixtures. Flask-Limiter's `enabled` flag lives on the module-level limiter
    singleton rather than on the app, so creating a second app with
    RATELIMIT_ENABLED=False would switch limiting off for this app too.
    """

    ATTEMPT = {"email": "admin@hospital.org", "password": "wrong-password"}

    @pytest.fixture
    def limited_client(self, tmp_path):
        class _Limited(TestConfig):
            UPLOAD_DIR = tmp_path / "uploads"
            RATELIMIT_ENABLED = True
            LOGIN_RATE_LIMIT = "3 per minute"

        return create_app(_Limited).test_client()

    def test_repeated_failed_logins_are_throttled(self, limited_client):
        statuses = [
            limited_client.post("/api/auth/login", json=self.ATTEMPT).status_code
            for _ in range(5)
        ]

        assert statuses[:3] == [401, 401, 401]
        assert statuses[3:] == [429, 429]

    def test_throttled_response_uses_the_standard_error_envelope(self, limited_client):
        for _ in range(4):
            response = limited_client.post("/api/auth/login", json=self.ATTEMPT)

        assert response.status_code == 429
        # The frontend's <ErrorBlock> renders `error`; a bare Werkzeug 429
        # page would give it nothing to show.
        assert "error" in response.get_json()
