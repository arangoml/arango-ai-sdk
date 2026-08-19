"""Top-level SDK clients.

One Client (or AsyncClient) per platform deployment. Service namespaces hang
off it (client.autograph, client.files, client.retrievers); the client owns
the shared httpx client and the JWT lifecycle. The two are twins in the
OpenAI/Anthropic dual-client pattern: identical construction and namespaces,
sync vs awaited I/O.
"""

from __future__ import annotations

from types import TracebackType
from typing import Any, Mapping

import httpx

from .acp import AcpAPI, AsyncAcpAPI
from .autograph import AsyncAutoGraphAPI, AutoGraphAPI
from .config import ClientConfig
from .filemanager import AsyncFileManagerAPI, FileManagerAPI
from .http import build_async_http_client, build_http_client, raise_for_status
from .retrieval import AsyncRetrieverAPI, RetrieverAPI


def _resolve_config(
    url: str | None,
    username: str | None,
    password: str | None,
    database: str,
    verify_tls: bool,
    timeout: float,
    config: ClientConfig | None,
) -> ClientConfig:
    """Constructor-argument handling shared by Client and AsyncClient."""
    if config is not None:
        return config
    return ClientConfig(
        base_url=url or "",
        username=username or "",
        password=password or "",
        database=database,
        verify_tls=verify_tls,
        timeout=timeout,
    )


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
        self.config = _resolve_config(
            url, username, password, database, verify_tls, timeout, config
        )
        self._http: httpx.Client = build_http_client(self.config)
        self.acp = AcpAPI(self._http, self.config.database)
        self.autograph = AutoGraphAPI(self)
        self.files = FileManagerAPI(self._http, self.config.database)
        self.retrievers = RetrieverAPI(self)

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


class AsyncClient:
    """Async twin of Client: same namespaces and semantics, awaited I/O."""

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
        self.config = _resolve_config(
            url, username, password, database, verify_tls, timeout, config
        )
        self._http: httpx.AsyncClient = build_async_http_client(self.config)
        self.acp = AsyncAcpAPI(self._http, self.config.database)
        self.autograph = AsyncAutoGraphAPI(self)
        self.files = AsyncFileManagerAPI(self._http, self.config.database)
        self.retrievers = AsyncRetrieverAPI(self)

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "AsyncClient":
        """Construct from ARANGO_URL / ARANGO_USERNAME / ARANGO_PASSWORD /
        ARANGO_DATABASE (+ optional ARANGO_VERIFY_TLS)."""
        return cls(config=ClientConfig.from_env(env))

    @property
    def http(self) -> httpx.AsyncClient:
        """The shared, JWT-authenticated httpx client (gateway base URL)."""
        return self._http

    async def whoami(self) -> str:
        """Logged-in user, from the gateway identity endpoint."""
        response = raise_for_status(await self._http.get("/_identity"))
        payload: dict[str, Any] = response.json()
        return str(payload.get("user", ""))

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "AsyncClient":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()
