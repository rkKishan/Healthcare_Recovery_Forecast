"""JWT issuing and the `@requires_auth` route guard."""

from __future__ import annotations

import functools
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from flask import current_app, g, request

from .errors import ApiError
from .models import User, db
from .roles import has_capability
from .roles import label as role_label


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str | None) -> bool:
    # A Google-only account has no hash at all. Returning False keeps that
    # indistinguishable from a wrong password at this layer.
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        return False


def create_token(user: User) -> tuple[str, int]:
    """Return a signed JWT and its lifetime in seconds."""
    hours = current_app.config["JWT_EXPIRATION_HOURS"]
    expires_at = datetime.now(UTC) + timedelta(hours=hours)

    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "iat": datetime.now(UTC),
        "exp": expires_at,
    }
    token = jwt.encode(
        payload,
        current_app.config["SECRET_KEY"],
        algorithm=current_app.config["JWT_ALGORITHM"],
    )
    return token, hours * 3600


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            current_app.config["SECRET_KEY"],
            algorithms=[current_app.config["JWT_ALGORITHM"]],
        )
    except jwt.ExpiredSignatureError:
        raise ApiError("Your session has expired. Please sign in again.", 401) from None
    except jwt.InvalidTokenError:
        raise ApiError("Invalid authentication token.", 401) from None


def requires_auth(view):
    """Reject the request unless it carries a valid bearer token."""

    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            raise ApiError(
                "Authentication required.", 401,
                hint="Send an 'Authorization: Bearer <token>' header.",
            )

        payload = decode_token(header.removeprefix("Bearer ").strip())

        # `sub` is attacker-influenced only in the sense that a forged token
        # would have failed signature verification above -- but a malformed
        # subject must still not become a 500.
        try:
            user_id = int(payload["sub"])
        except (KeyError, TypeError, ValueError):
            raise ApiError("Invalid authentication token.", 401) from None

        user = db.session.get(User, user_id)
        if user is None:
            raise ApiError("The account for this token no longer exists.", 401)

        g.current_user = user
        return view(*args, **kwargs)

    return wrapper


def require_capability(capability: str) -> None:
    """
    Imperative form of the guard, for routes that must resolve a resource
    before deciding on access.

    Ordering matters in a couple of places: probing another user's dataset id
    has to look the same whether or not the caller's role could have viewed a
    cohort, so the 404 is raised first and this is called afterwards.
    """
    user = getattr(g, "current_user", None)
    if user is None:
        raise ApiError("Authentication required.", 401)

    if not has_capability(user.role, capability):
        raise ApiError(
            f"This is not available to {role_label(user.role).lower()} accounts.",
            403,
            hint="Ask an administrator if you need access to this area.",
        )


def requires_capability(capability: str):
    """
    Route guard. Stacks under @requires_auth, which is what populates
    `g.current_user`:

        @bp.post("/upload")
        @requires_auth
        @requires_capability(DATASET_UPLOAD)
        def upload(): ...
    """

    def decorator(view):
        @functools.wraps(view)
        def wrapper(*args, **kwargs):
            require_capability(capability)
            return view(*args, **kwargs)

        return wrapper

    return decorator
