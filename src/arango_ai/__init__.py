"""Python SDK for the Arango AI Suite (alpha).

Alpha notice: APIs may change without backward compatibility before 1.0.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("arango-ai")
except PackageNotFoundError:  # pragma: no cover - package not installed
    __version__ = "0.0.0"
