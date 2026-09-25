"""Authentication endpoints: password login, registration, and Google Sign-In."""

from __future__ import annotations

import logging

from flask import Blueprint, current_app, g, request

from ..auth import create_token, hash_password, requires_auth, verify_password
from ..errors import ApiError
from ..google_auth import google_enabled, verify_google_token
from ..models import User, db
from ..ratelimit import limiter
from ..roles import (
    ADMIN,
    ANALYST,
    DEFAULT_ROLE,
    DOCTOR,
    demo_admin_role,
    is_admin_email,
    public_roles,
    role_for_signup,
)
from ..roles import (
    label as role_label,
)

logger = logging.getLogger(__name__)

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# Shown on every failed password login. It is deliberately independent of
# whether the account exists, so it cannot be used to enumerate addresses --
# a Google-only account and an unknown one produce the identical response.
LOGIN_HINT = "If you signed up with Google, use the Google button instead."


def _sync_admin(user: User) -> None:
    """
    Reconcile one account's role with the ADMIN_EMAILS list.

    Run whenever a session is minted, so the list is the whole truth about who
    administers this deployment: adding an address promotes that person on
    their next sign-in, and removing one demotes them, without anyone touching
    the database. Demotion returns them to the default clinical role rather
    than guessing which one they had before being elevated.

    An empty list means the feature is unconfigured, not that nobody should
    administer anything, so it promotes and demotes nobody -- otherwise
    deploying this change would quietly strip admin from every existing
    installation, including the seeded demo account on a laptop.

    Only ever driven by server configuration -- nothing from the request
    reaches this.
    """
    configured = current_app.config.get("ADMIN_EMAILS") or []
    if not configured:
        return

    allowlisted = is_admin_email(user.email)

    if allowlisted and user.role != ADMIN:
        user.role = ADMIN
    elif not allowlisted and user.role == ADMIN:
        user.role = DEFAULT_ROLE
    else:
        return

    db.session.commit()
    logger.info("Role for %s is now %s (from ADMIN_EMAILS).", user.email, user.role)


def _demo_accounts() -> list[dict]:
    """
    The seeded demo logins the sign-in page may offer, empty unless this
    deployment actually seeds them.

    The page used to hard-code these. That meant the public landing page
    advertised an administrator's address and password on a deployment where
    seeding was off and the account did not exist -- naming a real admin
    address to anyone who loaded the page, and inviting sign-ins that could
    only fail. It also went stale the moment DEMO_PASSWORD was overridden.

    Serving the password is only reasonable because it is a published demo
    credential and this returns nothing at all once seeding is off.
    """
    if not current_app.config.get("SEED_DEMO_USERS"):
        return []

    seeded = (
        (current_app.config["DEMO_DOCTOR_EMAIL"], DOCTOR),
        (current_app.config["DEMO_ANALYST_EMAIL"], ANALYST),
        (
            current_app.config["DEMO_EMAIL"],
            demo_admin_role(current_app.config.get("ADMIN_EMAILS")),
        ),
    )

    accounts, seen = [], set()
    for email, role in seeded:
        address = str(email).strip().lower()
        # The demo admin becomes a doctor once ADMIN_EMAILS is set, which would
        # otherwise list the same role twice.
        if not address or role in seen:
            continue
        seen.add(role)
        accounts.append(
            {"email": address, "role": role, "label": role_label(role)}
        )
    return accounts


def _session(user: User, status: int = 200):
    _sync_admin(user)
    token, expires_in = create_token(user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "user": user.to_dict(),
    }, status


@bp.get("/config")
def config():
    """
    What the sign-in page needs before anyone has authenticated.

    The Google client id is public by design; serving it from here rather than
    baking it into the bundle means the same build works against a server that
    has Google configured and one that does not.
    """
    return {
        "google_enabled": google_enabled(),
        "google_client_id": current_app.config.get("GOOGLE_CLIENT_ID") or None,
        "roles": public_roles(),
        "default_role": DEFAULT_ROLE,
        "demo_accounts": _demo_accounts(),
        "demo_password": (
            current_app.config["DEMO_PASSWORD"]
            if current_app.config.get("SEED_DEMO_USERS")
            else None
        ),
    }


@bp.post("/login")
@limiter.limit(lambda: current_app.config["LOGIN_RATE_LIMIT"])
def login():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))

    missing = [f for f, v in (("email", email), ("password", password)) if not v]
    if missing:
        raise ApiError(
            "Email and password are both required.", 400,
            details=[f"'{f}' was not provided." for f in missing],
        )

    user = User.query.filter_by(email=email).first()
    if user is None or not verify_password(password, user.password_hash):
        # Deliberately identical for unknown email, wrong password, and an
        # account that only has a Google identity.
        raise ApiError("Incorrect email or password.", 401, hint=LOGIN_HINT)

    return _session(user)


@bp.post("/register")
@limiter.limit(lambda: current_app.config["REGISTER_RATE_LIMIT"])
def register():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))
    full_name = str(payload.get("full_name", "")).strip()

    if not email or "@" not in email:
        raise ApiError("A valid email address is required.", 400)
    if len(password) < 8:
        raise ApiError("Password must be at least 8 characters long.", 400)
    if not full_name:
        raise ApiError("Full name is required.", 400)

    if User.query.filter_by(email=email).first():
        raise ApiError("An account with that email already exists.", 409)

    # A registrant picks between the two clinical roles and nothing else:
    # `role_for_signup` silently drops "admin" and anything unrecognised back
    # to the default, so reaching /register can never mint a privileged
    # account no matter what the body claims. The one way to become an
    # administrator is to be on the server's ADMIN_EMAILS list, which no
    # request can reach.
    user = User(
        email=email,
        full_name=full_name,
        role=role_for_signup(email, payload.get("role")),
        password_hash=hash_password(password),
        auth_provider="password",
    )
    db.session.add(user)
    db.session.commit()

    return _session(user, 201)


@bp.post("/google")
@limiter.limit(lambda: current_app.config["LOGIN_RATE_LIMIT"])
def google_login():
    """
    Sign in (or sign up) with a Google ID token.

    The browser gets the token from Google Identity Services and posts it here
    as `credential`. Everything that makes it trustworthy happens in
    `verify_google_token` -- nothing in the request body is believed except
    the role a first-time user picked, and that goes through the same
    whitelist as ordinary registration.
    """
    payload = request.get_json(silent=True) or {}
    claims = verify_google_token(payload.get("credential") or payload.get("id_token"))

    email = claims["email"]
    subject = str(claims["sub"])

    user = User.query.filter_by(email=email).first()

    if user is None:
        user = User(
            email=email,
            full_name=str(claims.get("name") or "").strip() or email.split("@")[0],
            role=role_for_signup(email, payload.get("role")),
            password_hash=None,
            auth_provider="google",
            google_sub=subject,
            avatar_url=str(claims.get("picture") or "") or None,
        )
        db.session.add(user)
        db.session.commit()
        return _session(user, 201)

    # An existing local account signing in with Google for the first time gets
    # linked. Re-linking to a *different* Google subject is refused: that means
    # the address was reassigned, and silently handing the new owner the old
    # account's data is exactly the failure to avoid.
    if user.google_sub and user.google_sub != subject:
        raise ApiError(
            "That email is already linked to a different Google account.", 409,
            hint="Sign in with the Google account you first used, or use a password.",
        )

    user.google_sub = subject
    if claims.get("picture"):
        user.avatar_url = str(claims["picture"])
    db.session.commit()

    return _session(user)


@bp.get("/me")
@requires_auth
def me():
    return {"user": g.current_user.to_dict()}
