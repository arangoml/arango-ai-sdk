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
            |-- InvalidProjectNameError
            |-- ProjectNotFoundError
            |-- InvalidSecretNameError
            |-- InvalidSecretValueError
            |-- SecretProfileNotFoundError
            |-- InvalidScopeError
            |-- InvalidFileMetadataError
            |-- EmptyFileError
            |-- BatchTooLargeError
            `-- FileUploadFailedError
"""

__all__ = [
    "ArangoAIError",
    "AuthenticationError",
    "BatchTooLargeError",
    "CommunicationError",
    "DatabaseNotFoundError",
    "EmptyFileError",
    "FileUploadFailedError",
    "InvalidCredentialsError",
    "InvalidFileMetadataError",
    "InvalidProjectNameError",
    "InvalidScopeError",
    "InvalidSecretNameError",
    "InvalidSecretValueError",
    "PlatformUnreachableError",
    "ProjectNotFoundError",
    "SecretProfileNotFoundError",
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


class ProjectNotFoundError(ServiceError):
    """The project requested does not exist.

    Raised from the projects namespace when get is called with a name where
    there is no such project with that name.
    """


class InvalidSecretNameError(ServiceError):
    """The service rejected the secret profile name.

    Raised from the secret profile namespace when create is called with a name
    the endpoint will not accept (empty, too long, or characters outside
    letters, digits, spaces, underscores and hyphens).
    """


class InvalidSecretValueError(ServiceError):
    """The service rejected the secret itself.

    Raised from the secret profile namespace when create is called with a
    secret that is empty, whitespace only, or longer than 4096 characters. The
    message never contains the secret.
    """


class SecretProfileNotFoundError(ServiceError):
    """No secret profile with the given ID exists on the platform."""


class InvalidScopeError(ServiceError):
    """A file scope breaks the platform's rules.

    A scope has at most five labels, each 1 to 128 characters of letters,
    digits, underscores and hyphens, and at most 256 characters combined. The
    files namespace checks this before sending, so the error is raised without
    transferring the file; the platform applies the same rules on its side.
    """


class InvalidFileMetadataError(ServiceError):
    """The platform rejected the custom metadata attached to an upload.

    Metadata is a flat string-to-string mapping with at most 32 keys, keys up
    to 64 characters, values up to 2048, and 16 KiB serialised in total.
    """


class EmptyFileError(ServiceError):
    """The file to upload has no content.

    The platform refuses empty files. Raised from the files namespace before
    sending a single file whose size on disk is zero, or when the platform
    reports it.
    """


class BatchTooLargeError(ServiceError):
    """One request would exceed what the platform accepts.

    The platform takes at most 100 files and 2 GiB per request. The files
    namespace sends every multi-file upload as one request and checks these
    limits first, so the error is raised before anything is transferred; split
    the files across several calls.
    """


class FileUploadFailedError(ServiceError):
    """The platform could not store the file or its metadata.

    Raised only when the platform itself reports the failure, in which case it
    has rolled the upload back, so nothing is left behind and no cleanup is
    needed before retrying.
    """
