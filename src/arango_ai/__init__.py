"""Python SDK for the Arango AI Suite (alpha).

Alpha notice: APIs may change without backward compatibility before 1.0.
"""

from importlib.metadata import PackageNotFoundError, version

from .autograph import AutoGraphProject
from .client import Client
from .config import ClientConfig
from .exceptions import (
    ApiError,
    ArangoAIError,
    AuthenticationError,
    BuildFailedError,
    BuildInProgressError,
    ConfigError,
    OrchestrationError,
    QueryError,
    ServiceNotReadyError,
    WaitTimeoutError,
)
from .filemanager import FileUpload, UploadResult
from .retrieval import Final, Progress, QueryResult, TokenDelta

try:
    __version__ = version("arango-ai")
except PackageNotFoundError:  # pragma: no cover - package not installed
    __version__ = "0.0.0"

__all__ = [
    "ApiError",
    "ArangoAIError",
    "AuthenticationError",
    "AutoGraphProject",
    "BuildFailedError",
    "BuildInProgressError",
    "Client",
    "ClientConfig",
    "ConfigError",
    "FileUpload",
    "Final",
    "OrchestrationError",
    "Progress",
    "QueryError",
    "QueryResult",
    "ServiceNotReadyError",
    "TokenDelta",
    "UploadResult",
    "WaitTimeoutError",
    "__version__",
]
