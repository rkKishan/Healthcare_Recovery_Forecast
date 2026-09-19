"""
Google Sign-In verification.

The browser runs Google Identity Services and hands us a signed ID token. The
only thing that makes that token trustworthy is verifying it *here*, against
Google's public keys and against our own client id -- a token minted for some
other application is a perfectly valid Google token, and accepting one would
let any site that can get a user to sign in impersonate them on this API.

`google-auth` performs the signature, issuer, audience and expiry checks; the
extra checks below are the ones specific to this deployment.
"""

from __future__ import annotations

from flask import current_app

from .errors import ApiError

GOOGLE_ISSUERS = frozenset({"accounts.google.com", "https://accounts.google.com"})


def google_enabled() -> bool:
    return bool(current_app.config.get("GOOGLE_CLIENT_ID"))


def verify_google_token(credential: object) -> dict:
    """
    Return the verified claims for a Google ID token, or raise ApiError.

    Never returns unverified claims: every failure path raises.
    """
    if not isinstance(credential, str) or not credential.strip():
        raise ApiError(
            "No Google credential was provided.", 400,
            hint="POST the `credential` string returned by Google Identity Services.",
        )

    client_id = current_app.config.get("GOOGLE_CLIENT_ID")
    if not client_id:
        raise ApiError(
            "Google sign-in is not configured on this server.", 503,
            hint="Set GOOGLE_CLIENT_ID in the environment and restart the API.",
        )

    try:
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token
    except ImportError as exc:  # pragma: no cover - depends on the environment
        raise ApiError(
            "Google sign-in is unavailable: the verification library is not installed.",
            503,
            hint="pip install google-auth",
        ) from exc

    try:
        claims = id_token.verify_oauth2_token(
            credential.strip(), google_requests.Request(), client_id
        )
    except ValueError as exc:
        # Covers a bad signature, the wrong audience, and an expired token.
        # The specific reason is logged by the caller's handler, not returned:
        # it tells an attacker which half of a forged token to fix.
        raise ApiError(
            "That Google sign-in could not be verified.", 401,
            hint="Try signing in again.",
        ) from exc

    if claims.get("iss") not in GOOGLE_ISSUERS:
        raise ApiError("That Google sign-in could not be verified.", 401)

    email = str(claims.get("email") or "").strip().lower()
    if not email:
        raise ApiError(
            "That Google account did not share an email address.", 403,
            hint="Grant the email permission when signing in.",
        )

    # An unverified address is one the account holder never proved they own,
    # so treating it as an identity would let anyone claim a colleague's email.
    if not claims.get("email_verified"):
        raise ApiError(
            "That Google account's email address is not verified.", 403,
            hint="Verify the address with Google, then sign in again.",
        )

    allowed = current_app.config.get("GOOGLE_ALLOWED_DOMAINS") or []
    if allowed:
        domain = str(claims.get("hd") or email.rsplit("@", 1)[-1]).lower()
        if domain not in allowed:
            raise ApiError(
                "That Google account is outside this hospital's domain.", 403,
                details=[f"'{domain}' is not an allowed sign-in domain."],
                hint=f"Sign in with an account at {' or '.join(sorted(allowed))}.",
            )

    claims["email"] = email
    return claims
