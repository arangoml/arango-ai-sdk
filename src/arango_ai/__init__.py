"""Python SDK for the Arango AI Suite (alpha).

Alpha notice: APIs may change without backward compatibility before 1.0.
"""

from importlib.metadata import PackageNotFoundError, version

from .client import Client
from .config import ClientConfig
from .exceptions import (
    ApiError,
    ArangoAIError,
    AuthenticationError,
    BuildInProgressError,
    ConfigError,
    OrchestrationError,
    QueryError,
    ServiceNotReadyError,
    WaitTimeoutError,
)

try:
    __version__ = version("arango-ai")
except PackageNotFoundError:  # pragma: no cover - package not installed
    __version__ = "0.0.0"

__all__ = [
    "ApiError",
    "ArangoAIError",
    "AuthenticationError",
    "BuildInProgressError",
    "Client",
    "ClientConfig",
    "ConfigError",
    "OrchestrationError",
    "QueryError",
    "ServiceNotReadyError",
    "WaitTimeoutError",
    "__version__",
]
