"""Python SDK for the Arango AI Suite (alpha).

Alpha notice: APIs may change without backward compatibility before 1.0.
"""

from importlib.metadata import PackageNotFoundError, version

from .autograph import (
    AsyncAutoGraphProject,
    AsyncCorpusBuildRun,
    AsyncOrchestrationRun,
    AutoGraphProject,
    CorpusBuildRun,
    OrchestrationRun,
)
from .autograph.ingestion import CorpusBuild
from .client import AsyncClient, Client
from .config import ClientConfig
from .exceptions import (
    APIConnectionError,
    ApiError,
    APITimeoutError,
    ArangoAIError,
    AuthenticationError,
    BadRequestError,
    BuildFailedError,
    BuildInProgressError,
    ConfigError,
    ConflictError,
    InternalServerError,
    NotFoundError,
    OrchestrationError,
    PermissionDeniedError,
    QueryError,
    RateLimitError,
    ServiceNotReadyError,
    UnauthorizedError,
    UnprocessableEntityError,
    WaitTimeoutError,
)
from .filemanager import FileUpload, UploadResult
from .retrieval import Final, Progress, QueryEvent, QueryResult, TokenDelta

try:
    __version__ = version("arango-ai")
except PackageNotFoundError:  # pragma: no cover - package not installed
    __version__ = "0.0.0"

__all__ = [
    "APIConnectionError",
    "APITimeoutError",
    "ApiError",
    "ArangoAIError",
    "AsyncAutoGraphProject",
    "AsyncClient",
    "AsyncCorpusBuildRun",
    "AsyncOrchestrationRun",
    "AuthenticationError",
    "AutoGraphProject",
    "BadRequestError",
    "BuildFailedError",
    "BuildInProgressError",
    "Client",
    "ClientConfig",
    "ConfigError",
    "ConflictError",
    "CorpusBuild",
    "CorpusBuildRun",
    "FileUpload",
    "Final",
    "InternalServerError",
    "NotFoundError",
    "OrchestrationError",
    "OrchestrationRun",
    "PermissionDeniedError",
    "Progress",
    "QueryError",
    "QueryEvent",
    "QueryResult",
    "RateLimitError",
    "ServiceNotReadyError",
    "TokenDelta",
    "UnauthorizedError",
    "UnprocessableEntityError",
    "UploadResult",
    "WaitTimeoutError",
    "__version__",
]
