"""HTTP core: the shared gateway client and error normalization."""

from __future__ import annotations

import json
from importlib.metadata import PackageNotFoundError, version
from typing import Any

import httpx

from .auth import AsyncJwtAuth, JwtAuth
from .config import ClientConfig
from .exceptions import ApiError


def _user_agent() -> str:
    try:
        return f"arango-ai/{version('arango-ai')}"
    except PackageNotFoundError:  # pragma: no cover - package not installed
        return "arango-ai/dev"


def _client_options(config: ClientConfig) -> dict[str, Any]:
    """Constructor kwargs shared by the sync and async client builders."""
    return {
        "base_url": config.base_url,
        "verify": config.verify_tls,
        "timeout": config.timeout,
        "headers": {"User-Agent": _user_agent()},
    }


def build_http_client(config: ClientConfig) -> httpx.Client:
    """One httpx client for every gateway call, JWT auth attached."""
    auth = JwtAuth(
        config.base_url,
        config.username,
        config.password,
        verify_tls=config.verify_tls,
        timeout=config.timeout,
    )
    return httpx.Client(auth=auth, **_client_options(config))


def build_async_http_client(config: ClientConfig) -> httpx.AsyncClient:
    """Async twin of build_http_client (AsyncJwtAuth, same options)."""
    auth = AsyncJwtAuth(
        config.base_url,
        config.username,
        config.password,
        verify_tls=config.verify_tls,
        timeout=config.timeout,
    )
    return httpx.AsyncClient(auth=auth, **_client_options(config))


def error_detail(response: httpx.Response) -> str:
    """Backend error text: first string among body.error / body.message.

    Mirrors the Studio UI's extraction so SDK and UI report the same message
    for the same failure.
    """
    try:
        body = response.json()
    except (json.JSONDecodeError, ValueError):
        body = None
    if isinstance(body, dict):
        for key in ("error", "message"):
            value = body.get(key)
            if isinstance(value, str) and value:
                return value
    return f"Request failed: {response.status_code}"


def raise_for_status(response: httpx.Response) -> httpx.Response:
    """Raise ApiError on any non-success status; pass the response through."""
    if response.status_code >= 400:
        raise ApiError(response.status_code, error_detail(response))
    return response
