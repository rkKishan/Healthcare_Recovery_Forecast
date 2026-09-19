"""
The conversation loop.

One turn is: send the history to Groq with the caller's permitted tools ->
if it asks for tools, run them here and send the results back -> repeat until
it answers in prose. The loop is bounded, because a model that keeps calling
tools forever is a billing incident rather than a conversation.

Nothing in this module decides what the assistant is allowed to do. That lives
in `tools.py`, keyed off the caller's role, and is applied twice: once when
building the offer list and again before any call runs.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from flask import current_app

from ..errors import ApiError
from .prompts import system_prompt
from .tools import dispatch, tools_for

logger = logging.getLogger(__name__)

# A question needing more than this many rounds of tool calls is one the
# assistant is not going to answer well anyway.
MAX_ROUNDS = 5

# How much conversation is replayed. The API is stateless, so the whole thing
# is re-sent every turn; this caps what a long session costs.
MAX_HISTORY_MESSAGES = 20

# Tool results are JSON-encoded into the prompt. A cohort payload with a 60-day
# forecast is large, and the model does not read better for having all of it.
MAX_TOOL_RESULT_CHARS = 12_000


class AssistantUnavailable(ApiError):
    """Raised when the assistant cannot run at all, rather than failing a turn."""

    def __init__(self, message: str, hint: str | None = None):
        super().__init__(message, 503, hint=hint)


# What each upstream status actually means for whoever has to fix it. Without
# this the panel said "could not be reached" for a wrong model name, a dead
# key and an unactivated account alike -- three different problems with three
# different fixes, all reported identically.
_STATUS_HINTS: dict[int, str] = {
    401: "GROQ_API_KEY was rejected. Check the key in .env, then restart "
         "the server -- config is read once at startup.",
    403: "This key is not permitted to use that model. Check the model your "
         "plan covers, then set GROQ_MODEL in .env.",
    404: "No such model. GROQ_MODEL must match an id the provider actually "
         "serves, which is not always how the docs pages spell it.",
    422: "The request was rejected as malformed, which is a bug here rather "
         "than a configuration problem.",
    429: "Rate limited. Check the response headers -- a "
         "x-ratelimit-limit-req-minute of 0 means the account has no quota "
         "allocated at all, which no retry will fix.",
}


def _upstream_error(exc: Exception, model: str) -> AssistantUnavailable:
    """Turn a provider exception into something actionable."""
    status = getattr(exc, "status_code", None)

    if status in _STATUS_HINTS:
        return AssistantUnavailable(
            f"The assistant could not be reached ({status}).",
            hint=_STATUS_HINTS[status],
        )
    if status is not None and status >= 500:
        return AssistantUnavailable(
            f"The assistant provider returned a server error ({status}).",
            hint="This is upstream and usually transient — retry shortly.",
        )
    return AssistantUnavailable(
        "The assistant could not be reached.",
        hint=f"Check GROQ_API_KEY, that GROQ_MODEL ({model}) is a model your "
             "account can use, and the service status.",
    )


def _client():
    """
    Build the provider client, or explain precisely what is missing.

    Constructed per call rather than held as a module global: the key is read
    from app config, and a cached client would outlive a config change and
    survive into tests that never set one.
    """
    api_key = (current_app.config.get("ASSISTANT_API_KEY") or "").strip()
    if not api_key:
        raise AssistantUnavailable(
            "The assistant is not configured.",
            hint="Set GROQ_API_KEY in .env and restart the server.",
        )

    try:
        from groq import Groq
    except ImportError as exc:  # pragma: no cover - dependency is declared
        raise AssistantUnavailable(
            "The Groq SDK is not installed.",
            hint="pip install -r requirements.txt",
        ) from exc

    return Groq(api_key=api_key)


def _encode(result: dict) -> str:
    """Serialise a tool result, truncating rather than blowing the context."""
    text = json.dumps(result, default=str)
    if len(text) <= MAX_TOOL_RESULT_CHARS:
        return text
    return (
        text[:MAX_TOOL_RESULT_CHARS]
        + '..."[truncated: ask for a narrower slice if you need the rest]"'
    )


def _arguments(raw: Any) -> dict:
    """
    Tool arguments arrive as a JSON string, or occasionally already parsed.

    Malformed JSON is handed back to the model as a tool error rather than
    raised -- it can usually fix its own call on the next round.
    """
    if isinstance(raw, dict):
        return raw
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return {"__malformed__": True}
    return parsed if isinstance(parsed, dict) else {"__malformed__": True}


def _trim(history: list[dict]) -> list[dict]:
    """
    Keep the tail of the conversation, starting on a user message.

    A window that opens on an assistant tool call whose results were trimmed
    away is rejected by the API, so the cut is moved forward to the next user
    turn rather than landing mid-exchange.
    """
    window = history[-MAX_HISTORY_MESSAGES:]
    for index, message in enumerate(window):
        if message.get("role") == "user":
            return window[index:]
    return []


def converse(role: str, history: list[dict], message: str) -> dict:
    """
    Run one user turn to completion.

    `history` is prior `{"role", "content"}` pairs from the client. Returns the
    reply plus the names of the tools that produced it, which the UI shows so a
    clinician can see the answer came from the model and the log rather than
    from a sentence generator.
    """
    client = _client()
    model = current_app.config["ASSISTANT_MODEL"]
    offered = tools_for(role)

    messages: list[dict] = [{"role": "system", "content": system_prompt(role)}]
    messages.extend(_trim(history))
    messages.append({"role": "user", "content": message})

    used: list[str] = []

    for _ in range(MAX_ROUNDS):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=offered or None,
                tool_choice="auto" if offered else None,
                temperature=0.2,
                max_tokens=1200,
            )
        except Exception as exc:  # noqa: BLE001 - upstream failure, not ours
            logger.warning("Assistant call failed: %s", exc)
            raise _upstream_error(exc, model) from exc

        choice = response.choices[0].message
        calls = getattr(choice, "tool_calls", None)

        if not calls:
            return {
                "reply": (choice.content or "").strip(),
                "tools_used": used,
                "model": model,
            }

        # Echo the assistant's tool-call turn back verbatim; the API rejects
        # tool results that do not answer a call it can see.
        messages.append(
            {
                "role": "assistant",
                "content": choice.content or "",
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments
                            if isinstance(call.function.arguments, str)
                            else json.dumps(call.function.arguments),
                        },
                    }
                    for call in calls
                ],
            }
        )

        for call in calls:
            name = call.function.name
            args = _arguments(call.function.arguments)

            if args.pop("__malformed__", False):
                result: dict = {
                    "error": "Your arguments were not valid JSON. Retry the call."
                }
            else:
                result = dispatch(role, name, args)
                if "error" not in result:
                    used.append(name)

            messages.append(
                {
                    "role": "tool",
                    "name": name,
                    "tool_call_id": call.id,
                    "content": _encode(result),
                }
            )

    # Out of rounds. Saying so is better than returning the last tool dump.
    return {
        "reply": (
            "I wasn't able to settle that one — it took more lookups than I "
            "can do in a single turn. Try asking for one thing at a time."
        ),
        "tools_used": used,
        "model": model,
    }
