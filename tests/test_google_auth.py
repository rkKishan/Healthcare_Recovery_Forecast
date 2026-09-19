"""
Google Sign-In.

The ID token itself is never faked past the verifier: these tests stub
`verify_oauth2_token`, which is exactly the boundary where Google's signature
is checked, and then assert on everything this application does with the
claims it gets back.
"""

from __future__ import annotations

import pytest

from backend.app import create_app
from backend.models import User
from backend.roles import ANALYST, DEFAULT_ROLE, DOCTOR

from .conftest import TestConfig

CLIENT_ID = "1234567890-example.apps.googleusercontent.com"


def claims(**overrides) -> dict:
    base = {
        "iss": "https://accounts.google.com",
        "aud": CLIENT_ID,
        "sub": "108234567890123456789",
        "email": "dr.rivera@hospital.org",
        "email_verified": True,
        "name": "Dr. Ana Rivera",
        "picture": "https://lh3.googleusercontent.com/a/example",
    }
    base.update(overrides)
    return base


@pytest.fixture
def google_app(tmp_path):
    class _Config(TestConfig):
        UPLOAD_DIR = tmp_path / "uploads"
        GOOGLE_CLIENT_ID = CLIENT_ID
        GOOGLE_ALLOWED_DOMAINS = []

    application = create_app(_Config)
    yield application

    from backend.models import db

    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def google_client(google_app):
    return google_app.test_client()


@pytest.fixture
def verified(monkeypatch):
    """Stub Google's verifier; the returned claims are what the route sees."""
    from google.oauth2 import id_token

    def install(payload: dict | None = None):
        result = payload if payload is not None else claims()

        def fake_verify(credential, request, audience=None, **kwargs):
            assert credential, "the route must pass the credential through"
            assert audience == CLIENT_ID, "the token must be checked against our client id"
            return result

        monkeypatch.setattr(id_token, "verify_oauth2_token", fake_verify)
        return result

    return install


class TestAuthConfig:
    def test_reports_google_as_enabled_when_configured(self, google_client):
        body = google_client.get("/api/auth/config").get_json()
        assert body["google_enabled"] is True
        assert body["google_client_id"] == CLIENT_ID

    def test_reports_google_as_disabled_by_default(self, client):
        body = client.get("/api/auth/config").get_json()
        assert body["google_enabled"] is False
        assert body["google_client_id"] is None

    def test_lists_the_selectable_roles(self, client):
        body = client.get("/api/auth/config").get_json()
        assert [r["value"] for r in body["roles"]] == [DOCTOR, ANALYST]
        assert body["default_role"] == DEFAULT_ROLE

    def test_needs_no_authentication(self, client):
        """It is what the sign-in page reads before anyone has a token."""
        assert client.get("/api/auth/config").status_code == 200


class TestGoogleSignIn:
    def test_first_sign_in_creates_the_account(self, google_client, verified):
        verified()
        response = google_client.post(
            "/api/auth/google", json={"credential": "a-signed-google-token"}
        )

        assert response.status_code == 201, response.get_json()
        body = response.get_json()
        assert body["access_token"]
        assert body["user"]["email"] == "dr.rivera@hospital.org"
        assert body["user"]["full_name"] == "Dr. Ana Rivera"
        assert body["user"]["auth_provider"] == "google"

    def test_a_first_time_user_may_pick_a_clinical_role(self, google_client, verified):
        verified()
        body = google_client.post(
            "/api/auth/google",
            json={"credential": "a-signed-google-token", "role": ANALYST},
        ).get_json()
        assert body["user"]["role"] == ANALYST

    def test_a_first_time_user_cannot_pick_admin(self, google_client, verified):
        """The role whitelist is the same one /register goes through."""
        verified()
        body = google_client.post(
            "/api/auth/google",
            json={"credential": "a-signed-google-token", "role": "admin"},
        ).get_json()
        assert body["user"]["role"] == DEFAULT_ROLE

    def test_signing_in_twice_reuses_the_account(self, google_app, google_client, verified):
        verified()
        first = google_client.post("/api/auth/google", json={"credential": "t"})
        second = google_client.post("/api/auth/google", json={"credential": "t"})

        assert first.status_code == 201
        assert second.status_code == 200
        with google_app.app_context():
            assert User.query.filter_by(email="dr.rivera@hospital.org").count() == 1

    def test_the_role_is_not_reassigned_on_a_later_sign_in(self, google_client, verified):
        """Otherwise anyone could flip their own role by re-authenticating."""
        verified()
        google_client.post(
            "/api/auth/google", json={"credential": "t", "role": ANALYST}
        )
        body = google_client.post(
            "/api/auth/google", json={"credential": "t", "role": "admin"}
        ).get_json()

        assert body["user"]["role"] == ANALYST

    def test_google_links_to_an_existing_password_account(
        self, google_app, google_client, verified
    ):
        google_client.post(
            "/api/auth/register",
            json={
                "email": "dr.rivera@hospital.org",
                "password": "a-good-password",
                "full_name": "Dr. Ana Rivera",
                "role": DOCTOR,
            },
        )

        verified()
        response = google_client.post("/api/auth/google", json={"credential": "t"})

        assert response.status_code == 200
        with google_app.app_context():
            user = User.query.filter_by(email="dr.rivera@hospital.org").first()
            assert user.google_sub == claims()["sub"]
            # The password still works: linking adds an identity, it does not
            # take the original one away.
            assert user.password_hash

    def test_a_different_google_subject_on_the_same_email_is_refused(
        self, google_client, verified
    ):
        """
        A reassigned workspace address must not inherit the old account.

        The email is the same; the Google `sub` is not, which means it is a
        different person.
        """
        verified()
        google_client.post("/api/auth/google", json={"credential": "t"})

        verified(claims(sub="999999999999999999999"))
        response = google_client.post("/api/auth/google", json={"credential": "t"})

        assert response.status_code == 409


class TestGoogleRejections:
    def test_a_missing_credential_is_400(self, google_client):
        assert google_client.post("/api/auth/google", json={}).status_code == 400

    def test_an_unverified_email_is_refused(self, google_client, verified):
        """An unverified address was never proved to belong to the signer."""
        verified(claims(email_verified=False))
        response = google_client.post("/api/auth/google", json={"credential": "t"})
        assert response.status_code == 403

    def test_a_bad_signature_is_401(self, google_client, monkeypatch):
        from google.oauth2 import id_token

        def reject(*args, **kwargs):
            raise ValueError("Token has wrong audience")

        monkeypatch.setattr(id_token, "verify_oauth2_token", reject)

        response = google_client.post("/api/auth/google", json={"credential": "forged"})
        assert response.status_code == 401
        # The specific reason stays server-side: it tells a forger which half
        # of the token to fix.
        assert "audience" not in response.get_json()["error"].lower()

    def test_no_account_is_created_by_a_rejected_token(
        self, google_app, google_client, verified
    ):
        verified(claims(email_verified=False))
        google_client.post("/api/auth/google", json={"credential": "t"})

        with google_app.app_context():
            assert User.query.filter_by(email="dr.rivera@hospital.org").first() is None

    def test_sign_in_is_503_when_google_is_not_configured(self, client):
        """A server with no client id cannot verify anything, and says so."""
        response = client.post("/api/auth/google", json={"credential": "t"})
        assert response.status_code == 503
        assert "hint" in response.get_json()


class TestDomainRestriction:
    @pytest.fixture
    def hospital_only(self, tmp_path):
        class _Config(TestConfig):
            UPLOAD_DIR = tmp_path / "uploads"
            GOOGLE_CLIENT_ID = CLIENT_ID
            GOOGLE_ALLOWED_DOMAINS = ["hospital.org"]

        application = create_app(_Config)
        yield application.test_client()

        from backend.models import db

        with application.app_context():
            db.session.remove()
            db.drop_all()

    def test_an_in_domain_account_is_accepted(self, hospital_only, verified):
        verified(claims(hd="hospital.org"))
        assert (
            hospital_only.post("/api/auth/google", json={"credential": "t"}).status_code
            == 201
        )

    def test_an_outside_account_is_refused(self, hospital_only, verified):
        verified(claims(email="someone@gmail.com", hd=None))
        response = hospital_only.post("/api/auth/google", json={"credential": "t"})
        assert response.status_code == 403
        assert "gmail.com" in " ".join(response.get_json()["details"])
