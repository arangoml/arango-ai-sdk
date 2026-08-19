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

IngestionAPI and AsyncIngestionAPI are twins: request bodies, validation
gates, terminal-state handling, and the mirror normalization live in shared
module helpers; the twins add only the I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, NoReturn
from urllib.parse import quote

import httpx

from .._polling import async_wait_until, wait_until
from ..exceptions import (
    ApiError,
    BuildFailedError,
    BuildInProgressError,
    ConfigError,
    OrchestrationError,
)
from ..http import raise_for_status
from .project import AsyncAutoGraphProject, AutoGraphProject, _mirror_of

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


def _corpus_build_body(
    project: str, categories: list[str] | None, incremental: bool
) -> dict[str, Any]:
    body: dict[str, Any] = {"project": project, "incremental": incremental}
    if categories is not None:
        body["categories"] = list(categories)
    return body


def _raise_build_start_error(err: ApiError) -> NoReturn:
    # Target contract is 409, but the stock gateway sometimes surfaces it
    # as 400 with the intent only in the message.
    if err.status_code == 409 or "BUILD_IN_PROGRESS" in err.detail:
        raise BuildInProgressError(err.status_code, err.detail) from err
    raise err


def _corpus_build_of(project: str, payload: dict[str, Any]) -> CorpusBuild:
    # Older services don't return the real graph name yet, so fall back to
    # the naming convention.
    graph_name = payload.get("graphName") or f"{project}_CorpusGraph"
    return CorpusBuild(
        build_id=str(payload.get("corpusBuildId", "")),
        graph_name=str(graph_name),
    )


def _build_tick(status: dict[str, Any]) -> dict[str, Any] | None:
    """Terminal handling for one corpus-build poll.

    Returns the completed status dict as-is — including a set errorCode
    (e.g. FILE_PARSER_PARTIAL_FAILURE): partial success is the caller's
    call, the SDK must not swallow it. Raises BuildFailedError on "failed"
    or a non-empty error field.
    """
    state = str(status.get("status", "")).lower()
    if state == "completed":
        return status
    if state == "failed" or status.get("error"):
        # On "failed", `message` carries the real cause and `error` is the
        # service's generic compatibility text; mid-run `message` is only a
        # progress line, so `error` leads there.
        if state == "failed":
            cause = status.get("message") or status.get("error")
        else:
            cause = status.get("error") or status.get("message")
        raise BuildFailedError(
            str(cause or "corpus build failed"),
            error_code=status.get("errorCode"),
        )
    return None


def _strategize_body(
    project: str,
    complexity: str,
    extract_images: bool,
    categories: list[str] | None,
) -> dict[str, Any]:
    """Strategizer request body with the client-side gates applied."""
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
    body: dict[str, Any] = {"project": project, "complexity": complexity}
    if extract_images:
        body["extractImagesDefault"] = True
    if categories:
        body["categories"] = list(categories)
    return body


def _strategy_patch_body(
    graph_rag: bool, entity_types: list[str] | None, extract_images: bool
) -> dict[str, Any]:
    return {
        "strategyType": "FullGraphRAG" if graph_rag else "VectorRAG",
        "entityTypes": list(entity_types or []),
        "extractImages": extract_images,
    }


def _check_replicas(replicas: int) -> None:
    if not 1 <= replicas <= 10:
        raise ConfigError(f"replicas must be between 1 and 10, got {replicas}")


def _fill_secrets_from_settings(
    chat_ids: list[str] | None,
    embedding_id: str | None,
    settings: dict[str, Any],
) -> tuple[list[str] | None, str | None]:
    if not chat_ids:
        settings_chat = settings.get("chatSecretProfileId")
        chat_ids = [str(settings_chat)] if settings_chat else None
    if not embedding_id:
        settings_embedding = settings.get("embeddingSecretProfileId")
        embedding_id = str(settings_embedding) if settings_embedding else None
    return chat_ids, embedding_id


def _finalize_orchestration_secrets(
    chat_ids: list[str] | None, embedding_id: str | None
) -> tuple[list[str], str | None]:
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
    # No chat-id fallback for embedding (UI parity: conditional spread).
    # Sending the chat id would make the orchestrator discard the service's
    # own inline embedding credentials and embed with the chat secret.
    return list(chat_ids), embedding_id


def _orchestrate_body(
    project: str,
    replicas: int,
    max_retries: int,
    categories: list[str] | None,
    chat_ids: list[str],
    embedding_id: str | None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "project": project,
        "replicas": replicas,
        "maxRetries": max_retries,
        "chatSecretProfileIds": chat_ids,
    }
    if embedding_id:
        body["embeddingSecretProfileId"] = embedding_id
    if categories:
        body["categories"] = list(categories)
    return body


def _orchestration_started(payload: dict[str, Any]) -> str | None:
    """The started run's id; an explicit success=false is a synchronous
    rejection — the run never started, so there is nothing to watch."""
    if payload.get("success") is False:
        raise OrchestrationError(
            str(
                payload.get("message")
                or "the knowledge-graph build could not be started"
            )
        )
    orchestration_id = payload.get("orchestrationId")
    return str(orchestration_id) if orchestration_id else None


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


def _orchestration_tick(status: dict[str, Any]) -> dict[str, Any] | None:
    """Terminal handling shared by both orchestration tiers."""
    state = str(status.get("status", "")).lower()
    if state == "completed":
        return status
    if state == "failed":
        lines = [str(status.get("message") or "knowledge-graph orchestration failed")]
        # Per-job causes exist only while the status endpoint answers;
        # include them so a partial failure is diagnosable from the error.
        for job in status.get("jobs") or []:
            error = job.get("errorMessage")
            if str(job.get("status", "")).lower() == "failed" and error:
                label = job.get("category") or job.get("ragPartitionId") or "job"
                lines.append(f"{label}: {error}")
        raise OrchestrationError("\n".join(lines))
    return None


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


_TERMINAL_MIRROR_STATES = {"completed", "failed"}


class _MirrorEchoGuard:
    """Suppresses a PREVIOUS run's terminal echo on the metadata-mirror tier.

    The mirror is a project-level slot, not a per-run record: right after
    triggering it may still hold the previous run's terminal state, which an
    id-less wait (or one whose status endpoint 404s before the run was ever
    observed) would otherwise return instantly. While the mirror still
    equals the pre-trigger baseline AND shows a terminal status, it is
    treated as "not yet"; once it changes or is seen non-terminal, terminal
    states are trusted (the UI's baseline contract). Without a baseline the
    guard is inert, keeping standalone waiter calls unchanged.
    """

    def __init__(self, baseline: dict[str, Any] | None) -> None:
        self._baseline = baseline

    def is_stale_echo(self, mirror: dict[str, Any]) -> bool:
        if self._baseline is None:
            return False
        state = str(mirror.get("status", "")).lower()
        if mirror != self._baseline or state not in _TERMINAL_MIRROR_STATES:
            self._baseline = None
            return False
        return True


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

        `categories` are category labels the service resolves against the
        project's File Manager files; None = every category the project has.
        The categories field is ALWAYS sent explicitly (the Studio UI does
        the same): omitting it drops the deployed service into a legacy
        partition-directory path that rejects File-Manager projects with
        "No partition directories found" (observed live on QA). The backend
        supports incremental builds but nothing exercises them yet (the UI
        always sends false), hence the alpha default.
        """
        if categories is None:
            categories = self._all_categories()
        body = _corpus_build_body(self._project.name, categories, incremental)
        try:
            response = raise_for_status(
                self._http.post(f"{self._service_path()}/v1/corpus/builds", json=body)
            )
        except ApiError as err:
            _raise_build_start_error(err)
        return _corpus_build_of(self._project.name, dict(response.json()))

    def _all_categories(self) -> list[str]:
        found = self._project._client.files.list_categories(self._project.name)
        if not found:
            raise ConfigError(
                f"project {self._project.name!r} has no uploaded files yet; "
                "add_files() before building the corpus"
            )
        return [segment for segment, _count in found]

    def corpus_build_status(self, build_id: str) -> dict[str, Any]:
        """GET v1/corpus/builds/{id} — one progress snapshot, raw."""
        response = raise_for_status(
            self._http.get(
                f"{self._service_path()}/v1/corpus/builds/{quote(build_id, safe='')}"
            )
        )
        return dict(response.json())

    def wait_for_build(
        self,
        build_id: str,
        *,
        timeout: float = 1800.0,
        interval: float = 5.0,
    ) -> dict[str, Any]:
        """Poll a corpus build to its terminal state (see _build_tick)."""

        def check() -> dict[str, Any] | None:
            return _build_tick(self.corpus_build_status(build_id))

        return wait_until(
            check,
            timeout=timeout,
            interval=interval,
            description=f"corpus build {build_id} of project {self._project.name!r}",
            tolerate_transient=True,
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
        body = _strategize_body(
            self._project.name, complexity, extract_images, categories
        )
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
            f"{self._service_path()}/v1/rag-strategizer/jobs/{quote(job_id, safe='')}"
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
        baseline: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Poll a strategizer run to its terminal state (two-tier).

        The jobs endpoint is trusted while it answers; without a job id, or
        once it 404s, the wait falls back to the ragstrategizer mirror in
        ACP project metadata. `baseline` is the mirror snapshot captured
        just before triggering; while the mirror still equals it and shows a
        terminal status, that terminal state is the PREVIOUS run's echo, not
        this run's result. Raises BuildFailedError on "failed".


        Limitation: the mirror carries no run id or timestamp, so without a `baseline` snapshot (captured pre-trigger; the facade passes one automatically) a terminal state left by a PREVIOUS run is indistinguishable from this run's result.
        """
        live_job_id = job_id
        guard = _MirrorEchoGuard(baseline)

        def check() -> dict[str, Any] | None:
            nonlocal live_job_id
            if live_job_id is not None:
                status = self.strategize_status(live_job_id)
                if status is not None:
                    return _strategize_tick(status)
                # An evicted id never comes back — stay on the mirror.
                live_job_id = None
            mirror = _mirror_of(self._project.metadata(), "ragstrategizer")
            if mirror is None or guard.is_stale_echo(mirror):
                return None
            return _strategize_tick(mirror)

        return wait_until(
            check,
            timeout=timeout,
            interval=interval,
            description=f"strategy generation of project {self._project.name!r}",
            tolerate_transient=True,
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
        body = _strategy_patch_body(graph_rag, entity_types, extract_images)
        response = raise_for_status(
            self._http.patch(
                f"{self._service_path()}/v1/rag-strategizer/strategy/{quote(cluster_id, safe='')}",
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
        otherwise they come from the project's persisted model settings.
        Without an embedding id the field is omitted and the service
        resolves its own embedding credentials (never the chat secret).
        """
        _check_replicas(replicas)
        chat_ids = chat_secret_profile_ids
        embedding_id = embedding_secret_profile_id
        if not (chat_ids and embedding_id):
            chat_ids, embedding_id = _fill_secrets_from_settings(
                chat_ids, embedding_id, self._project.model_settings()
            )
        final_chat_ids, final_embedding_id = _finalize_orchestration_secrets(
            chat_ids, embedding_id
        )
        body = _orchestrate_body(
            self._project.name,
            replicas,
            max_retries,
            categories,
            final_chat_ids,
            final_embedding_id,
        )
        response = raise_for_status(
            self._http.post(f"{self._service_path()}/v1/orchestrate", json=body)
        )
        return _orchestration_started(dict(response.json()))

    def orchestration_status(self, orchestration_id: str) -> dict[str, Any] | None:
        """GET v1/orchestrate/{id}; None when the id is gone.

        The endpoint is the only place a failed job's cause survives (the
        metadata mirror carries just the counts), but the id lives in
        service memory only — a 404 after a pod restart is the signal to
        fall back to the mirror, not an error.
        """
        response = self._http.get(
            f"{self._service_path()}/v1/orchestrate/{quote(orchestration_id, safe='')}"
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
        baseline: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Poll an orchestration run to its terminal state (two-tier).

        "completed" means every job succeeded; a partially failed run is
        reported as "failed" and raises OrchestrationError — with per-job
        causes when the status endpoint's jobs[] data is still available.
        The returned dict always uses the endpoint's field names
        (completedJobs/failedJobs), also on the metadata-mirror path.
        `baseline` is the raw mirror snapshot captured just before
        triggering; while the mirror still equals it and shows a terminal
        status, that terminal state is the PREVIOUS run's echo.


        Limitation: the mirror carries no run id or timestamp, so without a `baseline` snapshot (captured pre-trigger; the facade passes one automatically) a terminal state left by a PREVIOUS run is indistinguishable from this run's result.
        """
        live_id = orchestration_id
        guard = _MirrorEchoGuard(baseline)

        def check() -> dict[str, Any] | None:
            nonlocal live_id
            if live_id is not None:
                status = self.orchestration_status(live_id)
                if status is not None:
                    return _orchestration_tick(status)
                live_id = None
            mirror = _mirror_of(self._project.metadata(), "importerOrchestration")
            if mirror is None or guard.is_stale_echo(mirror):
                return None
            return _orchestration_tick(_normalize_mirror(mirror))

        return wait_until(
            check,
            timeout=timeout,
            interval=interval,
            description=(
                f"knowledge-graph orchestration of project {self._project.name!r}"
            ),
            tolerate_transient=True,
        )

    # -- overview -------------------------------------------------------------

    def overview(self) -> dict[str, Any]:
        """GET v1/projects/{name}/overview — the aggregate overview read, raw.

        Corpus/KG cards, strategy staleness and per-category needs flags
        exactly as the service computes them server-side (AIS-1494 §5.2).
        """
        name = quote(self._project.name, safe="")
        response = raise_for_status(
            self._http.get(f"{self._service_path()}/v1/projects/{name}/overview")
        )
        return dict(response.json())


class AsyncIngestionAPI:
    """Async twin of IngestionAPI: same endpoints, bodies, and waiters."""

    def __init__(self, project: AsyncAutoGraphProject) -> None:
        self._project = project

    @property
    def _http(self) -> httpx.AsyncClient:
        # Deliberately shares the project handle's client: ingestion is a
        # facet of the same session, not a second connection.
        return self._project._client.http

    async def _service_path(self) -> str:
        return await self._project.require_service_path()

    # -- corpus build ---------------------------------------------------------

    async def build_corpus(
        self,
        *,
        categories: list[str] | None = None,
        incremental: bool = False,
    ) -> CorpusBuild:
        """Async twin of IngestionAPI.build_corpus (see its docstring for
        why categories are always resolved and sent explicitly)."""
        if categories is None:
            categories = await self._all_categories()
        body = _corpus_build_body(self._project.name, categories, incremental)
        path = await self._service_path()
        try:
            response = raise_for_status(
                await self._http.post(f"{path}/v1/corpus/builds", json=body)
            )
        except ApiError as err:
            _raise_build_start_error(err)
        return _corpus_build_of(self._project.name, dict(response.json()))

    async def _all_categories(self) -> list[str]:
        found = await self._project._client.files.list_categories(self._project.name)
        if not found:
            raise ConfigError(
                f"project {self._project.name!r} has no uploaded files yet; "
                "add_files() before building the corpus"
            )
        return [segment for segment, _count in found]

    async def corpus_build_status(self, build_id: str) -> dict[str, Any]:
        """Async twin of IngestionAPI.corpus_build_status."""
        path = await self._service_path()
        response = raise_for_status(
            await self._http.get(f"{path}/v1/corpus/builds/{quote(build_id, safe='')}")
        )
        return dict(response.json())

    async def wait_for_build(
        self,
        build_id: str,
        *,
        timeout: float = 1800.0,
        interval: float = 5.0,
    ) -> dict[str, Any]:
        """Async twin of IngestionAPI.wait_for_build (see _build_tick)."""

        async def check() -> dict[str, Any] | None:
            return _build_tick(await self.corpus_build_status(build_id))

        return await async_wait_until(
            check,
            timeout=timeout,
            interval=interval,
            description=f"corpus build {build_id} of project {self._project.name!r}",
            tolerate_transient=True,
        )

    # -- RAG strategizer ------------------------------------------------------

    async def strategize(
        self,
        *,
        complexity: str,
        extract_images: bool = False,
        categories: list[str] | None = None,
    ) -> str | None:
        """Async twin of IngestionAPI.strategize."""
        body = _strategize_body(
            self._project.name, complexity, extract_images, categories
        )
        path = await self._service_path()
        response = raise_for_status(
            await self._http.post(f"{path}/v1/rag-strategizer/analyze", json=body)
        )
        job_id = response.json().get("strategizeJobId")
        return str(job_id) if job_id else None

    async def strategize_status(self, job_id: str) -> dict[str, Any] | None:
        """Async twin of IngestionAPI.strategize_status (404 = fall back)."""
        path = await self._service_path()
        response = await self._http.get(
            f"{path}/v1/rag-strategizer/jobs/{quote(job_id, safe='')}"
        )
        if response.status_code == 404:
            return None
        return dict(raise_for_status(response).json())

    async def wait_for_strategize(
        self,
        job_id: str | None,
        *,
        timeout: float = 1800.0,
        interval: float = 5.0,
        baseline: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Async twin of IngestionAPI.wait_for_strategize (two-tier,
        same baseline/echo contract).

        Limitation: the mirror carries no run id or timestamp, so without a `baseline` snapshot (captured pre-trigger; the facade passes one automatically) a terminal state left by a PREVIOUS run is indistinguishable from this run's result.
        """
        live_job_id = job_id
        guard = _MirrorEchoGuard(baseline)

        async def check() -> dict[str, Any] | None:
            nonlocal live_job_id
            if live_job_id is not None:
                status = await self.strategize_status(live_job_id)
                if status is not None:
                    return _strategize_tick(status)
                # An evicted id never comes back — stay on the mirror.
                live_job_id = None
            mirror = _mirror_of(await self._project.metadata(), "ragstrategizer")
            if mirror is None or guard.is_stale_echo(mirror):
                return None
            return _strategize_tick(mirror)

        return await async_wait_until(
            check,
            timeout=timeout,
            interval=interval,
            description=f"strategy generation of project {self._project.name!r}",
            tolerate_transient=True,
        )

    async def strategies(self) -> dict[str, Any]:
        """Async twin of IngestionAPI.strategies."""
        path = await self._service_path()
        response = raise_for_status(
            await self._http.get(f"{path}/v1/rag-strategizer/strategy")
        )
        return dict(response.json())

    async def update_strategy(
        self,
        cluster_id: str,
        *,
        graph_rag: bool,
        entity_types: list[str] | None = None,
        extract_images: bool = False,
    ) -> dict[str, Any]:
        """Async twin of IngestionAPI.update_strategy."""
        body = _strategy_patch_body(graph_rag, entity_types, extract_images)
        path = await self._service_path()
        response = raise_for_status(
            await self._http.patch(
                f"{path}/v1/rag-strategizer/strategy/{quote(cluster_id, safe='')}",
                json=body,
            )
        )
        strategy = response.json().get("strategy") or {}
        return dict(strategy)

    # -- orchestration (the knowledge-graph build) -----------------------------

    async def orchestrate(
        self,
        *,
        replicas: int = 1,
        max_retries: int = 3,
        categories: list[str] | None = None,
        chat_secret_profile_ids: list[str] | None = None,
        embedding_secret_profile_id: str | None = None,
    ) -> str | None:
        """Async twin of IngestionAPI.orchestrate."""
        _check_replicas(replicas)
        chat_ids = chat_secret_profile_ids
        embedding_id = embedding_secret_profile_id
        if not (chat_ids and embedding_id):
            chat_ids, embedding_id = _fill_secrets_from_settings(
                chat_ids, embedding_id, await self._project.model_settings()
            )
        final_chat_ids, final_embedding_id = _finalize_orchestration_secrets(
            chat_ids, embedding_id
        )
        body = _orchestrate_body(
            self._project.name,
            replicas,
            max_retries,
            categories,
            final_chat_ids,
            final_embedding_id,
        )
        path = await self._service_path()
        response = raise_for_status(
            await self._http.post(f"{path}/v1/orchestrate", json=body)
        )
        return _orchestration_started(dict(response.json()))

    async def orchestration_status(
        self, orchestration_id: str
    ) -> dict[str, Any] | None:
        """Async twin of IngestionAPI.orchestration_status (404 = fall back)."""
        path = await self._service_path()
        response = await self._http.get(
            f"{path}/v1/orchestrate/{quote(orchestration_id, safe='')}"
        )
        if response.status_code == 404:
            return None
        return dict(raise_for_status(response).json())

    async def wait_for_orchestration(
        self,
        orchestration_id: str | None,
        *,
        timeout: float = 7200.0,
        interval: float = 5.0,
        baseline: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Async twin of IngestionAPI.wait_for_orchestration (two-tier,
        same baseline/echo contract).

        Limitation: the mirror carries no run id or timestamp, so without a `baseline` snapshot (captured pre-trigger; the facade passes one automatically) a terminal state left by a PREVIOUS run is indistinguishable from this run's result.
        """
        live_id = orchestration_id
        guard = _MirrorEchoGuard(baseline)

        async def check() -> dict[str, Any] | None:
            nonlocal live_id
            if live_id is not None:
                status = await self.orchestration_status(live_id)
                if status is not None:
                    return _orchestration_tick(status)
                live_id = None
            mirror = _mirror_of(await self._project.metadata(), "importerOrchestration")
            if mirror is None or guard.is_stale_echo(mirror):
                return None
            return _orchestration_tick(_normalize_mirror(mirror))

        return await async_wait_until(
            check,
            timeout=timeout,
            interval=interval,
            description=(
                f"knowledge-graph orchestration of project {self._project.name!r}"
            ),
            tolerate_transient=True,
        )

    # -- overview -------------------------------------------------------------

    async def overview(self) -> dict[str, Any]:
        """Async twin of IngestionAPI.overview."""
        path = await self._service_path()
        name = quote(self._project.name, safe="")
        response = raise_for_status(
            await self._http.get(f"{path}/v1/projects/{name}/overview")
        )
        return dict(response.json())
