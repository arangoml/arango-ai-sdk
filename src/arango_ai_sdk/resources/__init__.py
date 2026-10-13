"""Client-wide platform resources."""

from arango_ai_sdk.resources.files import FileManager
from arango_ai_sdk.resources.secret_profiles import SecretProfileManager

__all__ = ["FileManager", "SecretProfileManager"]
