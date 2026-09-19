"""The assistant endpoint."""

from __future__ import annotations

from flask import Blueprint, current_app, g, request

from ..auth import requires_auth
from ..chat.service import converse
from ..chat.tools import tool_names_for
from ..errors import ApiError
from ..ratelimit import limiter

bp = Blueprint("chat", __name__, url_prefix="/api/chat")

MAX_MESSAGE_CHARS = 2000

# Every turn costs money and runs real queries. The limit is per authenticated
# user, not per IP: a shared hospital NAT would otherwise let one enthusiastic
# user lock out a ward.
CHAT_RATE_LIMIT = "20 per minute"


@bp.get("/config")
@requires_auth
def config():
    """
    Whether the assistant is usable, and what it can reach for this caller.

    The frontend asks before rendering the panel -- an assistant with no API
    key configured should be absent, not a button that errors when pressed.
    """
    role = g.current_user.role
    return {
        "enabled": bool((current_app.config.get("ASSISTANT_API_KEY") or "").strip()),
        "tools": tool_names_for(role),
        "role": role,
    }


@bp.post("")
@requires_auth
@limiter.limit(CHAT_RATE_LIMIT, key_func=lambda: str(g.current_user.id))
def chat():
    payload = request.get_json(silent=True) or {}

    message = (payload.get("message") or "").strip()
    if not message:
        raise ApiError("A message is required.", 400)
    if len(message) > MAX_MESSAGE_CHARS:
        raise ApiError(
            f"That message is too long ({len(message):,} characters).",
            400,
            hint=f"The limit is {MAX_MESSAGE_CHARS:,}.",
        )

    history = payload.get("history")
    if not isinstance(history, list):
        history = []

    # Only the two plain conversational roles are accepted back from the
    # browser. Tool calls and their results are reconstructed server-side each
    # turn, so a client cannot forge a tool result and put words in the
    # model's mouth about what the model supposedly returned.
    cleaned = [
        {"role": item["role"], "content": str(item["content"])[:MAX_MESSAGE_CHARS]}
        for item in history
        if isinstance(item, dict)
        and item.get("role") in {"user", "assistant"}
        and item.get("content")
    ]

    return converse(g.current_user.role, cleaned, message)
