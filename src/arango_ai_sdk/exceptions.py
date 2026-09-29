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
            |-- InvalidFileScopeError
            |-- InvalidFileMetadataError
            |-- EmptyFileError
            |-- FileBatchTooLargeError
            `-- FileUploadFailedError
            |-- SecretProfileNotFoundError
            |-- InvalidServiceParametersError
            |-- ServiceNotFoundError
            |-- ServiceNotDeletableError
            |-- AutoGraphAlreadyDeployedError
            |-- AutoGraphNotDeployedError
            |-- ModelConfigNotReadyError
            |-- AutoGraphBusyError
            |-- IngestionFailedError
            |-- JobStatusLostError
            `-- JobTimeoutError
"""

from typing import Any

__all__ = [
    "ArangoAIError",
    "AuthenticationError",
    "AutoGraphAlreadyDeployedError",
    "AutoGraphBusyError",
    "AutoGraphNotDeployedError",
    "CommunicationError",
    "DatabaseNotFoundError",
    "EmptyFileError",
    "FileBatchTooLargeError",
    "FileUploadFailedError",
    "IngestionFailedError",
    "InvalidCredentialsError",
    "InvalidFileMetadataError",
    "InvalidFileScopeError",
    "InvalidProjectNameError",
    "InvalidSecretNameError",
    "InvalidSecretValueError",
    "InvalidServiceParametersError",
    "JobStatusLostError",
    "JobTimeoutError",
    "ModelConfigNotReadyError",
    "PlatformUnreachableError",
    "ProjectNotFoundError",
    "SecretProfileNotFoundError",
    "ServiceError",
    "ServiceNotDeletableError",
    "ServiceNotFoundError",
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

    Raised when get is called with a name that has no project, and when
    AutoGraph install is asked for a project that is not there.
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


class InvalidFileScopeError(ServiceError):
    """A file scope breaks the file service's rules.

    Raised from the files namespace, normally before anything is sent.
    """


class InvalidFileMetadataError(ServiceError):
    """The file service rejected the custom metadata attached to an upload."""


class EmptyFileError(ServiceError):
    """The file to upload has no content.

    Raised from the files namespace, normally before anything is sent.
    """


class FileBatchTooLargeError(ServiceError):
    """A multi-file upload exceeds what the file service accepts in one request.

    Raised from the files namespace, normally before anything is sent. Split
    the files across several calls.
    """


class FileUploadFailedError(ServiceError):
    """The file service could not store the file and rolled the upload back.

    Nothing is left behind, so no cleanup is needed before retrying.
    """


class InvalidServiceParametersError(ServiceError):
    """ACP rejected an AutoGraph install parameter."""


class ServiceNotFoundError(ServiceError):
    """No ACP service with the given ID exists on the platform."""


class ServiceNotDeletableError(ServiceError):
    """ACP refused to delete a service managed by another entity."""


class AutoGraphAlreadyDeployedError(ServiceError):
    """The project already has an AutoGraph service; a project can have only one."""


class AutoGraphNotDeployedError(ServiceError):
    """The project has no AutoGraph service to act on."""


class ModelConfigNotReadyError(ServiceError):
    """AutoGraph refused a job because its model configuration is not usable.

    Either a startup probe found the chat or embedding settings invalid, or the
    service is still reloading them. Fix the settings or retry shortly.
    """


class AutoGraphBusyError(ServiceError):
    """AutoGraph refused a job because another one holds the slot.

    A build, strategizer run, orchestration or delete is already in progress
    for the project. Wait for it to finish and retry.
    """


class IngestionFailedError(ServiceError):
    """An AutoGraph job ended as failed or cancelled.

    Parameters
    ----------
    message : str
        Human-readable description of the failure.
    job_status : Any
        The last status object the service returned for the job.
    status_code : int, optional
        HTTP status code returned by the service.
    """

    job_status: Any

    def __init__(self, message: str, *, job_status: Any, status_code: int | None = None) -> None:
        super().__init__(message, status_code=status_code)
        self.job_status = job_status


class JobStatusLostError(ServiceError):
    """AutoGraph no longer knows the job it was polled for.

    The status record lives in pod memory and is gone after a restart, the job
    itself may still be running.

    Parameters
    ----------
    message : str
        Human-readable description of the failure.
    job_id : str
        Id of the job whose status is gone.
    status_code : int, optional
        HTTP status code returned by the service.
    """

    job_id: str

    def __init__(self, message: str, *, job_id: str, status_code: int | None = None) -> None:
        super().__init__(message, status_code=status_code)
        self.job_id = job_id


class JobTimeoutError(ServiceError):
    """The caller's deadline passed before the job reached a terminal state."""
