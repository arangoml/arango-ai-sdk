"""Exception hierarchy for the SDK.

Every error the SDK raises itself derives from ArangoAIError so callers can
catch one type. HTTP-level failures carry the status code and the backend's
own message (`error`/`message` on grpc-gateway services, `detail` on FastAPI
ones). Network-level failures are wrapped as APIConnectionError /
APITimeoutError on the long-running paths (uploads, polling waits, query
streams, login); short one-shot calls may still surface httpx transport
errors directly at alpha.
"""

from __future__ import annotations


class ArangoAIError(Exception):
    """Base class for all SDK errors."""


class ConfigError(ArangoAIError):
    """Client configuration is incomplete or invalid."""


class AuthenticationError(ArangoAIError):
    """Login against /_open/auth failed."""


class APIConnectionError(ArangoAIError):
    """The gateway could not be reached (DNS, TLS, refused, reset)."""


class APITimeoutError(APIConnectionError):
    """A request to the gateway timed out (a timeout is-a connection error,
    matching the convention of the OpenAI/Anthropic SDKs)."""


class ApiError(ArangoAIError):
    """A gateway call returned a non-success status.

    Instances are per-status subclasses where one exists (NotFoundError,
    ConflictError, ...) so callers can catch precisely; catching ApiError
    always works.
    """

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(f"HTTP {status_code}: {detail}")
        self.status_code = status_code
        self.detail = detail


class BadRequestError(ApiError):
    """HTTP 400."""


class UnauthorizedError(ApiError):
    """HTTP 401 (an expired/invalid token that survived the auth retry)."""


class PermissionDeniedError(ApiError):
    """HTTP 403."""


class NotFoundError(ApiError):
    """HTTP 404."""


class ConflictError(ApiError):
    """HTTP 409."""


class UnprocessableEntityError(ApiError):
    """HTTP 422."""


class RateLimitError(ApiError):
    """HTTP 429."""


class InternalServerError(ApiError):
    """HTTP 5xx."""


_STATUS_ERRORS: dict[int, type[ApiError]] = {
    400: BadRequestError,
    401: UnauthorizedError,
    403: PermissionDeniedError,
    404: NotFoundError,
    409: ConflictError,
    422: UnprocessableEntityError,
    429: RateLimitError,
}


def api_error_for(status_code: int, detail: str) -> ApiError:
    """The most specific ApiError subclass for a status code."""
    if status_code >= 500:
        return InternalServerError(status_code, detail)
    return _STATUS_ERRORS.get(status_code, ApiError)(status_code, detail)


class BuildInProgressError(ApiError):
    """A corpus build is already running for this project (HTTP 409).

    The stock gateway may surface this as a 400 with BUILD_IN_PROGRESS in the
    message; the SDK normalizes both to this type.
    """


class BuildFailedError(ArangoAIError):
    """A corpus build or strategizer run reported a terminal failure.

    Carries the service's machine-readable failure code (spec §3 catalog,
    e.g. LLM_AUTHENTICATION_FAILED) when one was reported, so callers can
    route recovery without parsing the message.
    """

    def __init__(self, message: str, error_code: str | None = None) -> None:
        super().__init__(f"{message} [{error_code}]" if error_code else message)
        self.error_code = error_code


class ServiceNotReadyError(ArangoAIError):
    """A deployed service did not become healthy within the deadline."""


class OrchestrationError(ArangoAIError):
    """Knowledge-graph orchestration failed or was rejected."""


class QueryError(ArangoAIError):
    """The retriever reported an error for a query (including in-stream
    error codes delivered inside an HTTP 200 stream)."""


class WaitTimeoutError(ArangoAIError):
    """A polling wait exceeded its deadline before reaching a terminal state."""
