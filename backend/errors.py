"""
Uniform JSON error handling.

Every failure leaving the API has the same shape, so the frontend can render
one error component everywhere:

    {"error": "<sentence>", "details": [...], "hint": "<what to do>"}
"""

from __future__ import annotations

import logging
import traceback

from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


class ApiError(Exception):
    """An expected, client-facing failure with a specific HTTP status."""

    def __init__(self, message: str, status: int = 400,
                 details: list[str] | None = None, hint: str | None = None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.details = details or []
        self.hint = hint

    def to_dict(self) -> dict:
        payload: dict = {"error": self.message}
        if self.details:
            payload["details"] = self.details
        if self.hint:
            payload["hint"] = self.hint
        return payload


def register_error_handlers(app) -> None:
    from ml.validator import DatasetValidationError

    @app.errorhandler(ApiError)
    def _api_error(exc: ApiError):
        return exc.to_dict(), exc.status

    @app.errorhandler(DatasetValidationError)
    def _validation_error(exc: DatasetValidationError):
        # 422: the file parsed, but its contents do not meet the schema.
        return exc.to_dict(), 422

    @app.errorhandler(413)
    def _too_large(_):
        limit = app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
        return {
            "error": f"The uploaded file exceeds the {limit} MB limit.",
            "hint": "Split the export into smaller files.",
        }, 413

    @app.errorhandler(HTTPException)
    def _http_error(exc: HTTPException):
        return {
            "error": exc.description or exc.name,
            "status": exc.code,
        }, exc.code or 500

    @app.errorhandler(Exception)
    def _unexpected(exc: Exception):
        # Log the trace server-side; never leak it to the client.
        logger.error("Unhandled error: %s\n%s", exc, traceback.format_exc())
        return {
            "error": "An unexpected server error occurred.",
            "hint": "Check the server logs for details.",
        }, 500
