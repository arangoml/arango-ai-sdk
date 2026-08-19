"""HTTP core: the shared gateway client and error normalization."""

from __future__ import annotations

import json
from importlib.metadata import PackageNotFoundError, version
from typing import Any

import httpx

from .auth import AsyncJwtAuth, JwtAuth
from .config import ClientConfig
from .exceptions import api_error_for

# Retries at the transport level cover CONNECT failures only (DNS, refused,
# reset before the request was sent) — safe for any method because nothing
# was delivered yet. Status-code retry policies are a post-alpha decision.
_CONNECT_RETRIES = 2


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
        # A tight connect budget fails fast on unreachable gateways while the
        # overall timeout stays generous for slow responses (reference-SDK
        # convention).
        "timeout": httpx.Timeout(config.timeout, connect=5.0),
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
    return httpx.Client(
        auth=auth,
        transport=httpx.HTTPTransport(
            retries=_CONNECT_RETRIES, verify=config.verify_tls
        ),
        **_client_options(config),
    )


def build_async_http_client(config: ClientConfig) -> httpx.AsyncClient:
    """Async twin of build_http_client (AsyncJwtAuth, same options)."""
    auth = AsyncJwtAuth(
        config.base_url,
        config.username,
        config.password,
        verify_tls=config.verify_tls,
        timeout=config.timeout,
    )
    return httpx.AsyncClient(
        auth=auth,
        transport=httpx.AsyncHTTPTransport(
            retries=_CONNECT_RETRIES, verify=config.verify_tls
        ),
        **_client_options(config),
    )


def error_detail(response: httpx.Response) -> str:
    """Backend error text: body.error / body.message / body.detail.

    `error`/`message` mirror the Studio UI's extraction for the grpc-gateway
    services; `detail` covers the FastAPI ones (File Manager), including the
    list shape FastAPI uses for validation errors.
    """
    try:
        body = response.json()
    except (json.JSONDecodeError, ValueError):
        body = None
    if isinstance(body, dict):
        for key in ("error", "message", "detail"):
            value = body.get(key)
            if isinstance(value, str) and value:
                return value
        detail = body.get("detail")
        if isinstance(detail, list) and detail:
            messages = [
                str(item.get("msg"))
                for item in detail
                if isinstance(item, dict) and item.get("msg")
            ]
            if messages:
                return "; ".join(messages[:5])
    return f"Request failed: {response.status_code}"


def raise_for_status(response: httpx.Response) -> httpx.Response:
    """Raise the per-status ApiError subclass on any non-2xx status.

    3xx counts as failure too: the SDK never follows redirects, so a
    redirect body would otherwise be parsed as if it were the answer.
    """
    if not 200 <= response.status_code < 300:
        raise api_error_for(response.status_code, error_detail(response))
    return response
