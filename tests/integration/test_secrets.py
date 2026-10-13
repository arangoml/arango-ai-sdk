"""Integration tests for :class:`SecretProfileManager`, against a live platform.

Marker and credentials skip come from ``tests/integration/conftest.py``. Values
can come from the process environment or from a ``.env`` file in the repo root
(see ``.env.example``). These tests send real HTTP requests through
``SecretProfileManager`` and clean up what they create.
"""

from datetime import datetime

import pytest

from arango_ai_sdk._naming import AcpPath, SecretProfileKey
from arango_ai_sdk.communication import Communication
from arango_ai_sdk.exceptions import (
    InvalidSecretNameError,
    InvalidSecretValueError,
    SecretProfileNotFoundError,
)
from arango_ai_sdk.models import ProfileType
from arango_ai_sdk.resources.secret_profiles import SecretProfileManager


def test_create_secret_profile_through_the_manager(
    communication: Communication, secret_profile_name: str, fake_secret: str
) -> None:
    """A user-facing create call stores a real secret profile on the platform."""
    manager = SecretProfileManager(communication)
    created = manager.create(
        secret_profile_name,
        fake_secret,
        provider="openai",
        description="Created by the SDK integration tests.",
    )
    try:
        assert created.profile_id
        assert created.name == secret_profile_name
        assert created.description == "Created by the SDK integration tests."
        assert created.profile_type is ProfileType.LLM
        assert created.metadata[SecretProfileKey.PROVIDER_METADATA] == "openai"
        # The secret never round-trips: only an obfuscated copy comes back
        # (first two and last two characters kept, the rest replaced by dots).
        obfuscated = created.secret_data[SecretProfileKey.SECRET_DATA]
        assert obfuscated != fake_secret
        assert obfuscated.startswith(fake_secret[:2])
        assert obfuscated.endswith(fake_secret[-2:])
        assert created.version == 1
        assert isinstance(created.created_at, datetime)
        assert created.created_at == created.updated_at

        fetched = manager.get(created.profile_id)
        assert fetched.profile_id == created.profile_id
        assert fetched.name == secret_profile_name
    finally:
        communication.send_request("delete", f"{AcpPath.SECRETS}/{created.profile_id}")


def test_create_with_empty_name_raises_invalid_secret_name(
    communication: Communication, fake_secret: str
) -> None:
    """An empty name is rejected by the endpoint and surfaced as a named error."""
    manager = SecretProfileManager(communication)
    with pytest.raises(InvalidSecretNameError, match="Secret name can only contain"):
        manager.create("", fake_secret)


def test_create_with_invalid_name_raises_invalid_secret_name(
    communication: Communication, fake_secret: str
) -> None:
    """A name that breaks ACP naming rules is surfaced as a named error with its 400."""
    manager = SecretProfileManager(communication)
    with pytest.raises(InvalidSecretNameError, match="Secret name can only contain") as exc_info:
        manager.create("Not A Valid Name!", fake_secret)
    assert exc_info.value.status_code == 400


def test_create_with_empty_secret_raises_invalid_secret_value(
    communication: Communication, secret_profile_name: str
) -> None:
    """An empty secret is rejected by the endpoint and surfaced as a named error."""
    manager = SecretProfileManager(communication)
    with pytest.raises(InvalidSecretValueError, match="Secret value cannot be empty"):
        manager.create(secret_profile_name, "")


def test_create_with_too_long_secret_raises_invalid_secret_value(
    communication: Communication, secret_profile_name: str
) -> None:
    """A secret over 4096 characters is rejected, and the message never echoes it."""
    manager = SecretProfileManager(communication)
    too_long = "x" * 4097
    with pytest.raises(InvalidSecretValueError, match="must not exceed 4096") as exc_info:
        manager.create(secret_profile_name, too_long)
    assert too_long not in str(exc_info.value)


def test_get_unknown_id_raises_secret_profile_not_found(
    communication: Communication,
) -> None:
    """An id the service does not know is surfaced as a named error."""
    manager = SecretProfileManager(communication)
    with pytest.raises(SecretProfileNotFoundError) as exc_info:
        manager.get("no-such-profile-id")
    assert exc_info.value.status_code == 404


def test_get_empty_id_raises_secret_profile_not_found(
    communication: Communication,
) -> None:
    """An empty id is rejected without calling the endpoint."""
    manager = SecretProfileManager(communication)
    with pytest.raises(SecretProfileNotFoundError):
        manager.get("")
