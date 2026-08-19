"""Arango Control Plane (ACP) wrappers: projects, secret profiles, services.

Gateway prefix /_platform/acp/v1 (ArangoRoute `/_platform/acp/` in the
arango-control-plane chart). Requests are snake_case on the wire, responses
come back camelCase (grpc-gateway proto3 JSON).

Secret handling rule: services are always deployed with secret PROFILE IDS,
never raw keys. Raw keys exist only long enough to create a profile.
"""

from __future__ import annotations

from typing import Any

import httpx

from ._polling import wait_until
from .exceptions import ServiceNotReadyError
from .http import raise_for_status

ACP_BASE = "/_platform/acp/v1"

# The UI maps short service kinds to helm chart names client-side; the SDK
# does the same so callers say "autograph", the wire says the chart name.
SERVICE_CHART_NAMES = {
    "autograph": "arangodb-autograph",
    "graphragretriever": "arangodb-graphrag-retriever",
}

_TERMINAL_SERVICE_STATUS = {"DEPLOYED", "FAILED"}


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
        body: dict[str, Any] = {
            "project_name": name,
            "project_type": project_type,
            "project_db_name": self._database,
        }
        if description is not None:
            body["project_description"] = description
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
            self._http.get(f"{ACP_BASE}/project_by_name/{self._database}/{name}")
        )
        return dict(response.json())

    def delete_project(self, name: str) -> dict[str, Any]:
        response = raise_for_status(
            self._http.delete(f"{ACP_BASE}/project/{self._database}/{name}")
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
        response = raise_for_status(
            self._http.get(f"{ACP_BASE}/secrets", params=params)
        )
        return dict(response.json())

    # -- services -----------------------------------------------------------

    def start_service(self, kind: str, env: dict[str, str]) -> dict[str, Any]:
        chart = SERVICE_CHART_NAMES.get(kind, kind)
        response = raise_for_status(
            self._http.post(
                f"{ACP_BASE}/service",
                json={"service_name": chart, "env": env},
            )
        )
        info = response.json().get("serviceInfo") or {}
        return dict(info)

    def get_service(self, service_id: str) -> dict[str, Any]:
        response = raise_for_status(self._http.get(f"{ACP_BASE}/service/{service_id}"))
        info = response.json().get("serviceInfo") or {}
        return dict(info)

    def delete_service(self, service_id: str) -> dict[str, Any]:
        response = raise_for_status(
            self._http.delete(f"{ACP_BASE}/service/{service_id}")
        )
        info = response.json().get("serviceInfo") or {}
        return dict(info)

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
            info = self.get_service(service_id)
            status = str(info.get("status", ""))
            return info if status in _TERMINAL_SERVICE_STATUS else None

        info = wait_until(
            check,
            timeout=timeout,
            interval=interval,
            description=f"service {service_id} deployment",
        )
        if info.get("status") == "FAILED":
            raise ServiceNotReadyError(
                f"service {service_id} failed to deploy: "
                f"{info.get('description') or 'no description'}"
            )
        return info
