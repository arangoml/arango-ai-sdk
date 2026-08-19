import pytest

from arango_ai import ClientConfig, ConfigError


def test_from_env_reads_all_variables() -> None:
    cfg = ClientConfig.from_env(
        {
            "ARANGO_URL": "https://gw.example.com/",
            "ARANGO_USERNAME": "root",
            "ARANGO_PASSWORD": "pw",
            "ARANGO_DATABASE": "db1",
            "ARANGO_VERIFY_TLS": "false",
        }
    )
    assert cfg.base_url == "https://gw.example.com"  # trailing slash normalized
    assert cfg.username == "root"
    assert cfg.database == "db1"
    assert cfg.verify_tls is False


def test_from_env_missing_variables_are_named() -> None:
    with pytest.raises(ConfigError) as excinfo:
        ClientConfig.from_env({"ARANGO_URL": "https://gw"})
    message = str(excinfo.value)
    assert "ARANGO_USERNAME" in message
    assert "ARANGO_PASSWORD" in message


def test_from_env_database_defaults_to_system() -> None:
    cfg = ClientConfig.from_env(
        {
            "ARANGO_URL": "https://gw",
            "ARANGO_USERNAME": "u",
            "ARANGO_PASSWORD": "p",
        }
    )
    # Matches the constructor's default so both entry points agree.
    assert cfg.database == "_system"


def test_verify_tls_defaults_to_true() -> None:
    cfg = ClientConfig.from_env(
        {
            "ARANGO_URL": "https://gw",
            "ARANGO_USERNAME": "u",
            "ARANGO_PASSWORD": "p",
            "ARANGO_DATABASE": "d",
        }
    )
    assert cfg.verify_tls is True


def test_password_not_in_repr() -> None:
    cfg = ClientConfig(base_url="https://gw", username="u", password="topsecret")
    assert "topsecret" not in repr(cfg)


def test_empty_base_url_rejected() -> None:
    with pytest.raises(ConfigError):
        ClientConfig(base_url="", username="u", password="p")
