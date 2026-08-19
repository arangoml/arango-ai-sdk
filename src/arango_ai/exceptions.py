"""Exception hierarchy for the SDK.

Every error raised by the SDK derives from ArangoAIError so callers can catch
one type. HTTP-level failures carry the status code and the backend's own
message (the gateway services put it in `error` or `message`).
"""

from __future__ import annotations


class ArangoAIError(Exception):
    """Base class for all SDK errors."""


class ConfigError(ArangoAIError):
    """Client configuration is incomplete or invalid."""


class AuthenticationError(ArangoAIError):
    """Login against /_open/auth failed."""


class ApiError(ArangoAIError):
    """A gateway call returned a non-success status."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(f"HTTP {status_code}: {detail}")
        self.status_code = status_code
        self.detail = detail


class BuildInProgressError(ApiError):
    """A corpus build is already running for this project (HTTP 409).

    The stock gateway may surface this as a 400 with BUILD_IN_PROGRESS in the
    message; the SDK normalizes both to this type.
    """


class ServiceNotReadyError(ArangoAIError):
    """A deployed service did not become healthy within the deadline."""


class OrchestrationError(ArangoAIError):
    """Knowledge-graph orchestration failed or was rejected."""


class QueryError(ArangoAIError):
    """The retriever reported an error for a query (including in-stream
    error codes delivered inside an HTTP 200 stream)."""


class WaitTimeoutError(ArangoAIError):
    """A polling wait exceeded its deadline before reaching a terminal state."""
