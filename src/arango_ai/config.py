"""Client configuration.

One platform base URL plus credentials: the only thing that differs across
air-gapped, on-prem, and AMP deployments. Every call the SDK makes is a
gateway path under this base URL, never a direct pod address.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Mapping

from .exceptions import ConfigError

_ENV_URL = "ARANGO_URL"
_ENV_USERNAME = "ARANGO_USERNAME"
_ENV_PASSWORD = "ARANGO_PASSWORD"  # nosec B105 - env var name, not a secret
_ENV_DATABASE = "ARANGO_DATABASE"
_ENV_VERIFY_TLS = "ARANGO_VERIFY_TLS"

_FALSY = {"0", "false", "no", "off"}


@dataclass(frozen=True)
class ClientConfig:
    """Connection settings for one platform deployment."""

    base_url: str
    username: str
    password: str = field(repr=False)
    database: str = "_system"
    verify_tls: bool = True
    timeout: float = 30.0

    def __post_init__(self) -> None:
        if not self.base_url:
            raise ConfigError("base_url must not be empty")
        # Normalize once so path joins never double the slash.
        object.__setattr__(self, "base_url", self.base_url.rstrip("/"))

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "ClientConfig":
        """Build a config from ARANGO_* environment variables.

        Required: ARANGO_URL, ARANGO_USERNAME, ARANGO_PASSWORD, ARANGO_DATABASE.
        Optional: ARANGO_VERIFY_TLS (0/false/no/off to disable).
        """
        source = os.environ if env is None else env
        missing = [
            name
            for name in (_ENV_URL, _ENV_USERNAME, _ENV_PASSWORD, _ENV_DATABASE)
            if not source.get(name)
        ]
        if missing:
            raise ConfigError(
                "missing required environment variables: " + ", ".join(missing)
            )
        verify_raw = source.get(_ENV_VERIFY_TLS, "true").strip().lower()
        return cls(
            base_url=source[_ENV_URL],
            username=source[_ENV_USERNAME],
            password=source[_ENV_PASSWORD],
            database=source[_ENV_DATABASE],
            verify_tls=verify_raw not in _FALSY,
        )
