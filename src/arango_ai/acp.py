"""Arango Control Plane (ACP) wrappers: projects, secret profiles, services.

Gateway prefix /_platform/acp/v1 (ArangoRoute `/_platform/acp/` in the
arango-control-plane chart). Requests are snake_case on the wire, responses
come back camelCase (grpc-gateway proto3 JSON).

Secret handling rule: services are always deployed with secret PROFILE IDS,
never raw keys. Raw keys exist only long enough to create a profile.

AcpAPI and AsyncAcpAPI are twins: every request body, query parameter, and
response shape comes from the shared module-level helpers, so the two can
never drift apart on the wire.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

from ._polling import async_wait_until, wait_until
from .exceptions import ConfigError, ServiceNotReadyError
from .http import raise_for_status

ACP_BASE = "/_platform/acp/v1"

# The UI maps short service kinds to helm chart names client-side; the SDK
# does the same so callers say "autograph", the wire says the chart name.
SERVICE_CHART_NAMES = {
    "autograph": "arangodb-autograph",
    "graphragretriever": "arangodb-graphrag-retriever",
}

_TERMINAL_SERVICE_STATUS = {"DEPLOYED", "FAILED"}


def require_service_id(info: dict[str, Any]) -> str:
    """serviceId out of a start_service response.

    A missing id means the deploy cannot be tracked at all: without it the
    status poll and health gate would target a broken URL and burn the whole
    timeout. Fail loudly instead.
    """
    service_id = str(info.get("serviceId", ""))
    if not service_id:
        raise ServiceNotReadyError(
            "service deploy response did not contain a serviceId"
        )
    return service_id


def _project_body(
    database: str, name: str, project_type: str, description: str | None
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "project_name": name,
        "project_type": project_type,
        "project_db_name": database,
    }
    if description is not None:
        body["project_description"] = description
    return body


def _secret_profile_body(
    name: str,
    secret_data: str,
    profile_type: str,
    provider: str | None,
    description: str | None,
    metadata: dict[str, str] | None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "name": name,
        "profile_type": profile_type,
        "secret_data": secret_data,
    }
    if provider is not None:
        body["provider"] = provider
    if description is not None:
        body["description"] = description
    if metadata is not None:
        body["metadata"] = metadata
    return body


def _secret_list_params(
    profile_type: str | None,
    provider: str | None,
    name_contains: str | None,
    limit: int | None,
    offset: int | None,
) -> dict[str, Any]:
    # Truthiness matches the backend's own check: it rejects provider
    # filtering combined with nonzero pagination with an HTTP 400, so the
    # SDK surfaces the constraint before any request is sent.
    if provider is not None and (limit or offset):
        raise ConfigError(
            "provider cannot be combined with limit/offset: the backend "
            "rejects provider filtering together with pagination"
        )
    params: dict[str, Any] = {}
    for key, value in (
        ("profile_type", profile_type),
        ("provider", provider),
        ("name_contains", name_contains),
        ("limit", limit),
        ("offset", offset),
    ):
        if value is not None:
            params[key] = value
    return params


def _quoted(segment: str) -> str:
    """Caller-supplied path segments are percent-encoded (the Studio's
    encodeURIComponent): unquoted, a '?' or '#' in a name would truncate the
    path and target a DIFFERENT project's resource."""
    return quote(segment, safe="")


def _service_body(kind: str, env: dict[str, str]) -> dict[str, Any]:
    return {"service_name": SERVICE_CHART_NAMES.get(kind, kind), "env": env}


def _service_info(payload: dict[str, Any]) -> dict[str, Any]:
    return dict(payload.get("serviceInfo") or {})


def _deployment_tick(info: dict[str, Any]) -> dict[str, Any] | None:
    """One deployment poll: the info once terminal, None while in flight."""
    status = str(info.get("status", ""))
    return info if status in _TERMINAL_SERVICE_STATUS else None


def _ensure_deployed(info: dict[str, Any], service_id: str) -> dict[str, Any]:
    if info.get("status") == "FAILED":
        raise ServiceNotReadyError(
            f"service {service_id} failed to deploy: "
            f"{info.get('description') or 'no description'}"
        )
    return info


class AcpAPI:
    """Low-level ACP calls, one method per endpoint."""

    def __init__(self, http: httpx.Client, database: str) -> None:
        self._http = http
        self._database = database

    @property
    def database(self) -> str:
        return self._database

    # -- projects ----------------------------------------------------------

    def create_project(
        self,
        name: str,
        *,
        project_type: str,
        description: str | None = None,
    ) -> dict[str, Any]:
        body = _project_body(self._database, name, project_type, description)
        response = raise_for_status(self._http.post(f"{ACP_BASE}/project", json=body))
        return dict(response.json())

    def list_projects(self) -> dict[str, dict[str, Any]]:
        response = raise_for_status(
            self._http.get(f"{ACP_BASE}/all_projects/{self._database}")
        )
        projects = response.json().get("projects") or {}
        return dict(projects)

    def get_project(self, name: str) -> dict[str, Any]:
        response = raise_for_status(
            self._http.get(
                f"{ACP_BASE}/project_by_name/{self._database}/{_quoted(name)}"
            )
        )
        return dict(response.json())

    def delete_project(self, name: str) -> dict[str, Any]:
        response = raise_for_status(
            self._http.delete(f"{ACP_BASE}/project/{self._database}/{_quoted(name)}")
        )
        return dict(response.json())

    # -- secret profiles ----------------------------------------------------

    def create_secret_profile(
        self,
        name: str,
        secret_data: str,
        *,
        profile_type: str = "LLM",
        provider: str | None = None,
        description: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        body = _secret_profile_body(
            name, secret_data, profile_type, provider, description, metadata
        )
        response = raise_for_status(self._http.post(f"{ACP_BASE}/secrets", json=body))
        profile = response.json().get("profile") or {}
        return dict(profile)

    def list_secret_profiles(
        self,
        *,
        profile_type: str | None = None,
        provider: str | None = None,
        name_contains: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        params = _secret_list_params(
            profile_type, provider, name_contains, limit, offset
        )
        response = raise_for_status(
            self._http.get(f"{ACP_BASE}/secrets", params=params)
        )
        return dict(response.json())

    # -- services -----------------------------------------------------------

    def start_service(self, kind: str, env: dict[str, str]) -> dict[str, Any]:
        response = raise_for_status(
            self._http.post(f"{ACP_BASE}/service", json=_service_body(kind, env))
        )
        return _service_info(response.json())

    def get_service(self, service_id: str) -> dict[str, Any]:
        response = raise_for_status(self._http.get(f"{ACP_BASE}/service/{service_id}"))
        return _service_info(response.json())

    def delete_service(self, service_id: str) -> dict[str, Any]:
        response = raise_for_status(
            self._http.delete(f"{ACP_BASE}/service/{service_id}")
        )
        return _service_info(response.json())

    def wait_service_deployed(
        self,
        service_id: str,
        *,
        timeout: float = 300.0,
        interval: float = 5.0,
    ) -> dict[str, Any]:
        """Poll until Helm reports DEPLOYED.

        DEPLOYED only means the install was accepted; callers that need the
        pod answering must additionally run the health-streak gate.
        """

        def check() -> dict[str, Any] | None:
            return _deployment_tick(self.get_service(service_id))

        info = wait_until(
            check,
            timeout=timeout,
            interval=interval,
            description=f"service {service_id} deployment",
            tolerate_transient=True,
        )
        return _ensure_deployed(info, service_id)


class AsyncAcpAPI:
    """Async twin of AcpAPI: same endpoints, bodies, and response shapes."""

    def __init__(self, http: httpx.AsyncClient, database: str) -> None:
        self._http = http
        self._database = database

    @property
    def database(self) -> str:
        return self._database

    # -- projects ----------------------------------------------------------

    async def create_project(
        self,
        name: str,
        *,
        project_type: str,
        description: str | None = None,
    ) -> dict[str, Any]:
        body = _project_body(self._database, name, project_type, description)
        response = raise_for_status(
            await self._http.post(f"{ACP_BASE}/project", json=body)
        )
        return dict(response.json())

    async def list_projects(self) -> dict[str, dict[str, Any]]:
        response = raise_for_status(
            await self._http.get(f"{ACP_BASE}/all_projects/{self._database}")
        )
        projects = response.json().get("projects") or {}
        return dict(projects)

    async def get_project(self, name: str) -> dict[str, Any]:
        response = raise_for_status(
            await self._http.get(
                f"{ACP_BASE}/project_by_name/{self._database}/{_quoted(name)}"
            )
        )
        return dict(response.json())

    async def delete_project(self, name: str) -> dict[str, Any]:
        response = raise_for_status(
            await self._http.delete(
                f"{ACP_BASE}/project/{self._database}/{_quoted(name)}"
            )
        )
        return dict(response.json())

    # -- secret profiles ----------------------------------------------------

    async def create_secret_profile(
        self,
        name: str,
        secret_data: str,
        *,
        profile_type: str = "LLM",
        provider: str | None = None,
        description: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        body = _secret_profile_body(
            name, secret_data, profile_type, provider, description, metadata
        )
        response = raise_for_status(
            await self._http.post(f"{ACP_BASE}/secrets", json=body)
        )
        profile = response.json().get("profile") or {}
        return dict(profile)

    async def list_secret_profiles(
        self,
        *,
        profile_type: str | None = None,
        provider: str | None = None,
        name_contains: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        params = _secret_list_params(
            profile_type, provider, name_contains, limit, offset
        )
        response = raise_for_status(
            await self._http.get(f"{ACP_BASE}/secrets", params=params)
        )
        return dict(response.json())

    # -- services -----------------------------------------------------------

    async def start_service(self, kind: str, env: dict[str, str]) -> dict[str, Any]:
        response = raise_for_status(
            await self._http.post(f"{ACP_BASE}/service", json=_service_body(kind, env))
        )
        return _service_info(response.json())

    async def get_service(self, service_id: str) -> dict[str, Any]:
        response = raise_for_status(
            await self._http.get(f"{ACP_BASE}/service/{service_id}")
        )
        return _service_info(response.json())

    async def delete_service(self, service_id: str) -> dict[str, Any]:
        response = raise_for_status(
            await self._http.delete(f"{ACP_BASE}/service/{service_id}")
        )
        return _service_info(response.json())

    async def wait_service_deployed(
        self,
        service_id: str,
        *,
        timeout: float = 300.0,
        interval: float = 5.0,
    ) -> dict[str, Any]:
        """Async twin of AcpAPI.wait_service_deployed."""

        async def check() -> dict[str, Any] | None:
            return _deployment_tick(await self.get_service(service_id))

        info = await async_wait_until(
            check,
            timeout=timeout,
            interval=interval,
            description=f"service {service_id} deployment",
            tolerate_transient=True,
        )
        return _ensure_deployed(info, service_id)
