import pytest

from arango_ai import Client, ClientConfig, ConfigError

from .conftest import BASE


def test_client_rejects_config_combined_with_explicit_credentials() -> None:
    config = ClientConfig(base_url=BASE, username="u", password="p")

    # Silently ignoring explicit credentials next to config= would hide a
    # real caller mistake; the constructor fails loud instead.
    with pytest.raises(ConfigError, match="config"):
        Client(BASE, config=config)
    with pytest.raises(ConfigError, match="config"):
        Client(username="u", config=config)
    with pytest.raises(ConfigError, match="config"):
        Client(password="p", config=config)


def test_client_accepts_config_alone() -> None:
    config = ClientConfig(base_url=BASE, username="u", password="p")

    client = Client(config=config)

    assert client.config is config
    client.close()
