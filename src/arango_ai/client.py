"""Top-level SDK client.

One Client per platform deployment. Service namespaces hang off it
(client.autograph in the ACP layer PR); the client owns the shared httpx
client and the JWT lifecycle.
"""

from __future__ import annotations

from types import TracebackType
from typing import Any, Mapping

import httpx

from .config import ClientConfig
from .http import build_http_client, raise_for_status


class Client:
    """Entry point: authenticated access to one platform deployment."""

    def __init__(
        self,
        url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        *,
        database: str = "_system",
        verify_tls: bool = True,
        timeout: float = 30.0,
        config: ClientConfig | None = None,
    ) -> None:
        if config is None:
            config = ClientConfig(
                base_url=url or "",
                username=username or "",
                password=password or "",
                database=database,
                verify_tls=verify_tls,
                timeout=timeout,
            )
        self.config = config
        self._http: httpx.Client = build_http_client(config)

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Client":
        """Construct from ARANGO_URL / ARANGO_USERNAME / ARANGO_PASSWORD /
        ARANGO_DATABASE (+ optional ARANGO_VERIFY_TLS)."""
        return cls(config=ClientConfig.from_env(env))

    @property
    def http(self) -> httpx.Client:
        """The shared, JWT-authenticated httpx client (gateway base URL)."""
        return self._http

    def whoami(self) -> str:
        """Logged-in user, from the gateway identity endpoint."""
        response = raise_for_status(self._http.get("/_identity"))
        payload: dict[str, Any] = response.json()
        return str(payload.get("user", ""))

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "Client":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()
