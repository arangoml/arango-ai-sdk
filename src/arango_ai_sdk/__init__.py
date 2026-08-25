"""Python SDK for the ArangoDB AI Suite."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("arango-ai-sdk")
except PackageNotFoundError:  # pragma: no cover - source tree without an install
    __version__ = "0.0.0.dev0"

__all__ = ["__version__"]
