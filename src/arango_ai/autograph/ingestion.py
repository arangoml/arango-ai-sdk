"""Ingestion workflow on a deployed AutoGraph service.

Corpus build -> RAG strategizer -> orchestration (the knowledge-graph build),
plus the aggregate overview read. Every call goes directly to the project's
own service instance; its gateway path is re-resolved per call because the
URL appears only after deploy and can move on redeploys (the Studio UI
re-reads it each time too). The service speaks camelCase JSON in both
directions (grpc-gateway proto3).

Long runs are watched two-tier where the service offers a per-run status
endpoint (strategize jobs, orchestrations): the run id lives in service
memory only, so after a pod restart or eviction the endpoint 404s and the
ACP project-metadata mirror is all that's left. The waiters trust the
endpoint while it answers and fall back to the mirror on a 404.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from .._polling import wait_until
from ..exceptions import (
    ApiError,
    BuildFailedError,
    BuildInProgressError,
    ConfigError,
    OrchestrationError,
)
from ..http import raise_for_status
from .project import AutoGraphProject

# Strategizer complexity sets the FullGraphRAG share across clusters
# (very_low = 0% ... very_high = 100%); the service rejects other values.
COMPLEXITY_LEVELS = ("very_low", "low", "moderate", "high", "very_high")

# Image-extraction profiles only exist at these levels; the service rejects
# extractImagesDefault=true below "high", so the SDK mirrors that gate.
_IMAGE_CAPABLE_COMPLEXITY = ("high", "very_high")


@dataclass(frozen=True)
class CorpusBuild:
    """Handle of a started corpus build."""

    build_id: str
    graph_name: str


class IngestionAPI:
    """Corpus build, strategizer, and orchestration for one AutoGraph project."""

    def __init__(self, project: AutoGraphProject) -> None:
        self._project = project

    @property
    def _http(self) -> httpx.Client:
        # Deliberately shares the project handle's client: ingestion is a
        # facet of the same session, not a second connection.
        return self._project._client.http

    def _service_path(self) -> str:
        return self._project.require_service_path()

    # -- corpus build ---------------------------------------------------------

    def build_corpus(
        self,
        *,
        categories: list[str] | None = None,
        incremental: bool = False,
    ) -> CorpusBuild:
        """POST v1/corpus/builds — start a corpus build.

        `categories` are module labels the service resolves against the
        project's File Manager files itself; None = the whole project. The
        backend supports incremental builds but nothing exercises them yet
        (the Studio UI always sends false), hence the alpha default.
        """
        body: dict[str, Any] = {
            "project": self._project.name,
            "incremental": incremental,
        }
        if categories is not None:
            body["categories"] = list(categories)
        try:
            response = raise_for_status(
                self._http.post(f"{self._service_path()}/v1/corpus/builds", json=body)
            )
        except ApiError as err:
            # Target contract is 409, but the stock gateway sometimes
            # surfaces it as 400 with the intent only in the message.
            if err.status_code == 409 or "BUILD_IN_PROGRESS" in err.detail:
                raise BuildInProgressError(err.status_code, err.detail) from err
            raise
        payload = dict(response.json())
        # [EXTEND] field: older services don't return the real graph name
        # yet, so fall back to the naming convention.
        graph_name = payload.get("graphName") or f"{self._project.name}_CorpusGraph"
        return CorpusBuild(
            build_id=str(payload.get("corpusBuildId", "")),
            graph_name=str(graph_name),
        )

    def corpus_build_status(self, build_id: str) -> dict[str, Any]:
        """GET v1/corpus/builds/{id} — one progress snapshot, raw."""
        response = raise_for_status(
            self._http.get(f"{self._service_path()}/v1/corpus/builds/{build_id}")
        )
        return dict(response.json())

    def wait_for_build(
        self,
        build_id: str,
        *,
        timeout: float = 1800.0,
        interval: float = 5.0,
    ) -> dict[str, Any]:
        """Poll a corpus build to its terminal state.

        Returns the completed status dict as-is — including a set errorCode
        (e.g. FILE_PARSER_PARTIAL_FAILURE): partial success is the caller's
        call, the SDK must not swallow it. Raises BuildFailedError on
        "failed" or a non-empty error field.
        """

        def check() -> dict[str, Any] | None:
            status = self.corpus_build_status(build_id)
            state = str(status.get("status", "")).lower()
            if state == "completed":
                return status
            if state == "failed" or status.get("error"):
                # On "failed", `message` carries the real cause and `error`
                # is the service's generic compatibility text; mid-run
                # `message` is only a progress line, so `error` leads there.
                if state == "failed":
                    cause = status.get("message") or status.get("error")
                else:
                    cause = status.get("error") or status.get("message")
                raise BuildFailedError(
                    str(cause or "corpus build failed"),
                    error_code=status.get("errorCode"),
                )
            return None

        return wait_until(
            check,
            timeout=timeout,
            interval=interval,
            description=f"corpus build {build_id} of project {self._project.name!r}",
        )

    # -- RAG strategizer ------------------------------------------------------

    def strategize(
        self,
        *,
        complexity: str,
        extract_images: bool = False,
        categories: list[str] | None = None,
    ) -> str | None:
        """POST v1/rag-strategizer/analyze — start the async strategizer job.

        Returns the run's job id when the service hands one out (older
        services don't); pass it — or None — to wait_for_strategize.
        `categories` scopes re-generation to those modules, leaving other
        modules' stored strategies (and review edits) untouched.
        """
        if complexity not in COMPLEXITY_LEVELS:
            raise ConfigError(
                f"complexity must be one of {', '.join(COMPLEXITY_LEVELS)}; "
                f"got {complexity!r}"
            )
        if extract_images and complexity not in _IMAGE_CAPABLE_COMPLEXITY:
            raise ConfigError(
                "extract_images=True requires complexity 'high' or 'very_high': "
                "image-extraction profiles only exist at those levels, and the "
                "service rejects the request below 'high'"
            )
        body: dict[str, Any] = {
            "project": self._project.name,
            "complexity": complexity,
        }
        if extract_images:
            body["extractImagesDefault"] = True
        if categories:
            body["categories"] = list(categories)
        response = raise_for_status(
            self._http.post(
                f"{self._service_path()}/v1/rag-strategizer/analyze", json=body
            )
        )
        job_id = response.json().get("strategizeJobId")
        return str(job_id) if job_id else None

    def strategize_status(self, job_id: str) -> dict[str, Any] | None:
        """GET v1/rag-strategizer/jobs/{id}; None when the id is gone.

        Terminal snapshots are retained in service memory for a bounded
        window only and don't survive a pod restart — a 404 is the signal
        to fall back to the metadata mirror, not an error.
        """
        response = self._http.get(
            f"{self._service_path()}/v1/rag-strategizer/jobs/{job_id}"
        )
        if response.status_code == 404:
            return None
        return dict(raise_for_status(response).json())

    def wait_for_strategize(
        self,
        job_id: str | None,
        *,
        timeout: float = 1800.0,
        interval: float = 5.0,
    ) -> dict[str, Any]:
        """Poll a strategizer run to its terminal state (two-tier).

        The jobs endpoint is trusted while it answers; without a job id, or
        once it 404s, the wait falls back to the ragstrategizer mirror in
        ACP project metadata. Raises BuildFailedError on "failed".
        """
        live_job_id = job_id

        def check() -> dict[str, Any] | None:
            nonlocal live_job_id
            if live_job_id is not None:
                status = self.strategize_status(live_job_id)
                if status is not None:
                    return self._strategize_tick(status)
                # An evicted id never comes back — stay on the mirror.
                live_job_id = None
            mirror = self._strategizer_mirror()
            if mirror is None:
                return None
            return self._strategize_tick(mirror)

        return wait_until(
            check,
            timeout=timeout,
            interval=interval,
            description=f"strategy generation of project {self._project.name!r}",
        )

    def strategies(self) -> dict[str, Any]:
        """GET v1/rag-strategizer/strategy — every generated strategy, raw."""
        response = raise_for_status(
            self._http.get(f"{self._service_path()}/v1/rag-strategizer/strategy")
        )
        return dict(response.json())

    def update_strategy(
        self,
        cluster_id: str,
        *,
        graph_rag: bool,
        entity_types: list[str] | None = None,
        extract_images: bool = False,
    ) -> dict[str, Any]:
        """PATCH v1/rag-strategizer/strategy/{cluster_id} — edit one cluster.

        The server normalizes (VectorRAG forces entityTypes empty and images
        off, entity types are uppercased) — the SDK passes values through
        instead of duplicating those rules. A 409 means an orchestration is
        running; the ApiError's detail says so.
        """
        body = {
            "strategyType": "FullGraphRAG" if graph_rag else "VectorRAG",
            "entityTypes": list(entity_types or []),
            "extractImages": extract_images,
        }
        response = raise_for_status(
            self._http.patch(
                f"{self._service_path()}/v1/rag-strategizer/strategy/{cluster_id}",
                json=body,
            )
        )
        strategy = response.json().get("strategy") or {}
        return dict(strategy)

    # -- orchestration (the knowledge-graph build) -----------------------------

    def orchestrate(
        self,
        *,
        replicas: int = 1,
        max_retries: int = 3,
        categories: list[str] | None = None,
        chat_secret_profile_ids: list[str] | None = None,
        embedding_secret_profile_id: str | None = None,
    ) -> str | None:
        """POST v1/orchestrate — start the async knowledge-graph build.

        Import jobs (one per strategy profile) are distributed across
        `replicas` importer workers. Explicit secret profile ids win;
        otherwise they come from the project's persisted model settings,
        with the embedding id falling back to the chat id.
        """
        if not 1 <= replicas <= 10:
            raise ConfigError(f"replicas must be between 1 and 10, got {replicas}")
        chat_ids, embedding_id = self._resolve_orchestration_secrets(
            chat_secret_profile_ids, embedding_secret_profile_id
        )
        body: dict[str, Any] = {
            "project": self._project.name,
            "replicas": replicas,
            "maxRetries": max_retries,
            "chatSecretProfileIds": chat_ids,
            "embeddingSecretProfileId": embedding_id,
        }
        if categories:
            body["categories"] = list(categories)
        response = raise_for_status(
            self._http.post(f"{self._service_path()}/v1/orchestrate", json=body)
        )
        payload = dict(response.json())
        # An explicit false is a synchronous rejection — the run never
        # started, so there is nothing to watch.
        if payload.get("success") is False:
            raise OrchestrationError(
                str(
                    payload.get("message")
                    or "the knowledge-graph build could not be started"
                )
            )
        orchestration_id = payload.get("orchestrationId")
        return str(orchestration_id) if orchestration_id else None

    def orchestration_status(self, orchestration_id: str) -> dict[str, Any] | None:
        """GET v1/orchestrate/{id}; None when the id is gone.

        The endpoint is the only place a failed job's cause survives (the
        metadata mirror carries just the counts), but the id lives in
        service memory only — a 404 after a pod restart is the signal to
        fall back to the mirror, not an error.
        """
        response = self._http.get(
            f"{self._service_path()}/v1/orchestrate/{orchestration_id}"
        )
        if response.status_code == 404:
            return None
        return dict(raise_for_status(response).json())

    def wait_for_orchestration(
        self,
        orchestration_id: str | None,
        *,
        timeout: float = 7200.0,
        interval: float = 5.0,
    ) -> dict[str, Any]:
        """Poll an orchestration run to its terminal state (two-tier).

        "completed" means every job succeeded; a partially failed run is
        reported as "failed" and raises OrchestrationError — with per-job
        causes when the status endpoint's jobs[] data is still available.
        The returned dict always uses the endpoint's field names
        (completedJobs/failedJobs), also on the metadata-mirror path.
        """
        live_id = orchestration_id

        def check() -> dict[str, Any] | None:
            nonlocal live_id
            if live_id is not None:
                status = self.orchestration_status(live_id)
                if status is not None:
                    return self._orchestration_tick(status)
                live_id = None
            mirror = self._orchestration_mirror()
            if mirror is None:
                return None
            return self._orchestration_tick(self._normalize_mirror(mirror))

        return wait_until(
            check,
            timeout=timeout,
            interval=interval,
            description=(
                f"knowledge-graph orchestration of project {self._project.name!r}"
            ),
        )

    # -- overview -------------------------------------------------------------

    def overview(self) -> dict[str, Any]:
        """GET v1/projects/{name}/overview — the aggregate overview read, raw.

        Corpus/KG cards, strategy staleness and per-category needs flags
        exactly as the service computes them server-side (AIS-1494 §5.2).
        """
        response = raise_for_status(
            self._http.get(
                f"{self._service_path()}/v1/projects/{self._project.name}/overview"
            )
        )
        return dict(response.json())

    # -- internals --------------------------------------------------------------

    def _resolve_orchestration_secrets(
        self,
        chat_ids: list[str] | None,
        embedding_id: str | None,
    ) -> tuple[list[str], str]:
        """Secret profile ids the importer workers resolve credentials with."""
        if not (chat_ids and embedding_id):
            settings = self._project.model_settings()
            if not chat_ids:
                settings_chat = settings.get("chatSecretProfileId")
                chat_ids = [str(settings_chat)] if settings_chat else None
            if not embedding_id:
                settings_embedding = settings.get("embeddingSecretProfileId")
                embedding_id = str(settings_embedding) if settings_embedding else None
        if not chat_ids:
            raise ConfigError(
                "orchestration needs a chat secret profile id: the graphrag "
                "importer is a separate service that resolves its own LLM "
                "credentials via the secret manager (the request fails with "
                "HTTP 400 without one). Pass chat_secret_profile_ids, or "
                "create the project through create_project's key handling "
                "(openai_api_key / chat_secret_profile_id) so the ids are "
                "persisted in the project's model settings."
            )
        # One key serving both roles is the common case — embedding falls
        # back to the chat id, mirroring create_project's env building.
        return list(chat_ids), embedding_id or chat_ids[0]

    def _autograph_service_meta(self) -> dict[str, Any]:
        meta = self._project.metadata().get("projectMetadata") or {}
        service = meta.get("autographService") or {}
        return dict(service)

    def _strategizer_mirror(self) -> dict[str, Any] | None:
        mirror = self._autograph_service_meta().get("ragstrategizer")
        return dict(mirror) if isinstance(mirror, dict) else None

    def _orchestration_mirror(self) -> dict[str, Any] | None:
        mirror = self._autograph_service_meta().get("importerOrchestration")
        return dict(mirror) if isinstance(mirror, dict) else None

    @staticmethod
    def _strategize_tick(status: dict[str, Any]) -> dict[str, Any] | None:
        """Terminal handling shared by both strategize tiers."""
        state = str(status.get("status", "")).lower()
        if state == "completed":
            return status
        if state == "failed":
            # The jobs endpoint carries no message; the mirror does.
            raise BuildFailedError(
                str(status.get("message") or "strategy generation failed")
            )
        return None

    @staticmethod
    def _orchestration_tick(status: dict[str, Any]) -> dict[str, Any] | None:
        """Terminal handling shared by both orchestration tiers."""
        state = str(status.get("status", "")).lower()
        if state == "completed":
            return status
        if state == "failed":
            lines = [
                str(status.get("message") or "knowledge-graph orchestration failed")
            ]
            # Per-job causes exist only while the status endpoint answers;
            # include them so a partial failure is diagnosable from the error.
            for job in status.get("jobs") or []:
                error = job.get("errorMessage")
                if str(job.get("status", "")).lower() == "failed" and error:
                    label = job.get("category") or job.get("ragPartitionId") or "job"
                    lines.append(f"{label}: {error}")
            raise OrchestrationError("\n".join(lines))
        return None

    @staticmethod
    def _normalize_mirror(mirror: dict[str, Any]) -> dict[str, Any]:
        """The mirror's field names differ from the endpoint's (completed vs
        completedJobs) — callers always get the endpoint's shape back."""
        return {
            "status": mirror.get("status"),
            "totalJobs": mirror.get("totalJobs"),
            "completedJobs": mirror.get("completed"),
            "failedJobs": mirror.get("failed"),
            "message": mirror.get("message"),
        }
