"""
Rate limiting for the unauthenticated auth endpoints.

Login and register are the only routes a stranger can call, which makes them
the only ones worth brute-forcing. Everything else already sits behind
`@requires_auth`, so a global limit would mostly punish legitimate dashboard
traffic without adding protection.

The default storage is in-process memory, which is correct for a single
worker and *per worker* under gunicorn -- each process keeps its own counter,
so the effective limit multiplies by the worker count. Point
RATELIMIT_STORAGE_URI at Redis for a shared, accurate limit in production.
"""

from __future__ import annotations

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from .errors import ApiError

# No default_limits: routes opt in explicitly.
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
)


def rate_limited(_exc) -> tuple[dict, int]:
    """Render a 429 in the same envelope as every other API error."""
    return (
        ApiError(
            "Too many attempts. Please wait before trying again.",
            429,
            hint="This limit protects the account from password guessing.",
        ).to_dict(),
        429,
    )
