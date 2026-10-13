"""Python SDK for the ArangoDB AI Suite."""

from importlib.metadata import PackageNotFoundError, version

from arango_ai_sdk.managers.client import ArangoAIClient
from arango_ai_sdk.managers.project_handle import AiProjectHandle

try:
    __version__ = version("arango-ai-sdk")
except PackageNotFoundError:  # pragma: no cover - source tree without an install
    __version__ = "0.0.0.dev0"

__all__ = ["AiProjectHandle", "ArangoAIClient", "__version__"]
