"""The AutoGraphProject handle: everything scoped to one project.

The AutoGraph service has no fixed gateway prefix: each instance gets its own
ArangoRoute (/autograph/{postfix}/), recorded in ACP project metadata as
autographService.serviceUrl. The SDK keeps only that URL's path and joins it
onto the configured gateway base, so calls stay deployment-parity safe.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from .._polling import wait_for_streak
from ..exceptions import ServiceNotReadyError
from ..http import raise_for_status

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ..client import Client

# Gateway routes flap while propagating; require this many consecutive 200s
# before treating the service as serving (UI: SERVING_CONSECUTIVE_OK).
SERVING_CONSECUTIVE_OK = 3


class AutoGraphProject:
    """Handle for one AutoGraph project (name + configured database)."""

    def __init__(self, client: "Client", name: str) -> None:
        self._client = client
        self.name = name

    @property
    def database(self) -> str:
        return self._client.acp.database

    def __repr__(self) -> str:
        return f"AutoGraphProject(name={self.name!r}, database={self.database!r})"

    # -- metadata ------------------------------------------------------------

    def metadata(self) -> dict[str, Any]:
        """Fresh ACP project record (metadata appears asynchronously)."""
        return self._client.acp.get_project(self.name)

    def model_settings(self) -> dict[str, Any]:
        """Persisted model settings (secret profile ids, never raw keys)."""
        settings = self.metadata().get("modelSettings") or {}
        return dict(settings)

    def service_path(self) -> str | None:
        """Gateway path of this project's AutoGraph service, or None.

        Re-read per call (the UI does the same): the URL appears only after
        deploy and can move on redeploys.
        """
        meta = self.metadata().get("projectMetadata") or {}
        service = meta.get("autographService") or {}
        url = service.get("serviceUrl")
        if not url:
            return None
        return urlparse(str(url)).path.rstrip("/")

    def require_service_path(self) -> str:
        path = self.service_path()
        if not path:
            raise ServiceNotReadyError(
                f"project {self.name!r} has no deployed AutoGraph service yet"
            )
        return path

    # -- health --------------------------------------------------------------

    def ping_health(self) -> bool:
        """One health probe; False on any failure (route may still flap)."""
        path = self.service_path()
        if not path:
            return False
        try:
            response = self._client.http.get(f"{path}/v1/health")
        except Exception:  # noqa: BLE001 - a failed probe is just "not yet"
            return False
        return response.status_code < 400

    def wait_until_serving(
        self,
        *,
        streak: int = SERVING_CONSECUTIVE_OK,
        interval: float = 5.0,
        timeout: float = 300.0,
    ) -> None:
        """Block until the service answers `streak` consecutive health 200s."""
        wait_for_streak(
            self.ping_health,
            needed=streak,
            interval=interval,
            timeout=timeout,
            description=f"AutoGraph service of project {self.name!r} to serve",
        )

    # -- teardown --------------------------------------------------------------

    def delete(self, *, delete_files: bool = True) -> dict[str, Any]:
        """Two-phase delete, mirroring the Studio UI.

        Phase 1 (service present): DELETE {service}/v1/projects/{name} tears
        down collections, graphs, views, importer + retriever services, files,
        and the ACP entry server-side. The service returns 200 for BOTH full
        success and partial failure — callers must check `deleted` and
        `warnings`, and may simply retry (idempotent; on partial failure the
        ACP entry is kept so retry works).

        Phase 2 (no service): plain ACP project delete.
        """
        path = self.service_path()
        if path:
            response = raise_for_status(
                self._client.http.delete(
                    f"{path}/v1/projects/{self.name}",
                    params={"delete_files": str(delete_files).lower()},
                )
            )
            return dict(response.json())
        return self._client.acp.delete_project(self.name)
