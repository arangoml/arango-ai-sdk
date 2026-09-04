"""Exceptions raised by the SDK.

Every exception the SDK raises descends from :class:`ArangoAIError`, so one
``except`` always catches everything. Nothing from an underlying library
(``python-arango``, ``requests``, JSON parsing) is allowed to escape, it is
translated into one of the types below first.

Exception capture happens in the corresponding namespace, so when a request to service A
returns an error, none of the central modules should classify that error.
This keeps the imports in the central communication and client modules clean.

The tree is deliberately shallow -- a root, a few families, concrete errors
underneath -- so callers pick how precisely to catch::

    except ArangoAIError            # anything the SDK can raise
    except AuthenticationError      # any authentication problem
    except InvalidCredentialsError  # exactly wrong username or password

The whole tree, in one place::

    ArangoAIError
    |-- AuthenticationError
    |   |-- InvalidCredentialsError
    |   `-- TokenRefreshError
    `-- CommunicationError
        |-- PlatformUnreachableError
        `-- ServiceError
            |-- DatabaseNotFoundError
            `-- InvalidProjectNameError
"""

__all__ = [
    "ArangoAIError",
    "AuthenticationError",
    "CommunicationError",
    "DatabaseNotFoundError",
    "InvalidCredentialsError",
    "InvalidProjectNameError",
    "PlatformUnreachableError",
    "ServiceError",
    "TokenRefreshError",
]


class ArangoAIError(Exception):
    """Base class for every exception raised by the SDK."""


class AuthenticationError(ArangoAIError):
    """Base class for authentication problems."""


class InvalidCredentialsError(AuthenticationError):
    """The platform rejected the username or password.

    Never retried: repeating a rejected login cannot succeed, and against some
    backends it counts towards a lockout.
    """


class TokenRefreshError(AuthenticationError):
    """A token was needed but could not be obtained or renewed."""


class CommunicationError(ArangoAIError):
    """Base class for problems reaching the platform or reading its reply."""


class PlatformUnreachableError(CommunicationError):
    """The platform could not be reached within the retry budget.

    Distinct from :class:`InvalidCredentialsError`: the platform never got the
    chance to reject anything.
    """


class ServiceError(CommunicationError):
    """A service was reached and answered with an error.

    The catch-all for error responses that is used if there is no named
    per-condition exception.

    Parameters
    ----------
    message : str
        Human-readable description of the failure.
    status_code : int, optional
        HTTP status code returned by the service.
    error_code : int, optional
        Service-specific error number, where one was supplied.
    """

    status_code: int | None
    error_code: int | None

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        error_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code


class DatabaseNotFoundError(ServiceError):
    """The database named at construction does not exist on the platform."""


class InvalidProjectNameError(ServiceError):
    """The service rejected the project name.

    Raised from the projects namespace when create is called with a name the
    endpoint will not accept (empty, too long, or characters outside the
    allowed set).
    """
