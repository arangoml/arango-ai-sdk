"""The AutoGraphProject handle: everything scoped to one project.

The AutoGraph service has no fixed gateway prefix: each instance gets its own
ArangoRoute (/autograph/{postfix}/), recorded in ACP project metadata as
autographService.serviceUrl. The SDK keeps only that URL's path and joins it
onto the configured gateway base, so calls stay deployment-parity safe.

AutoGraphProject and AsyncAutoGraphProject are twins: metadata parsing,
upload-source normalization, retriever resolution, and the deploy-defaults
mapping live in shared module helpers; the twins add only the I/O.
"""

from __future__ import annotations

import glob as _glob
from pathlib import Path
from typing import TYPE_CHECKING, Any, AsyncIterator, Iterator, Sequence
from urllib.parse import quote, urlparse

import httpx

from .._polling import async_wait_for_streak, wait_for_streak
from ..exceptions import ConfigError, ServiceNotReadyError
from ..filemanager import FileUpload, UploadResult
from ..http import raise_for_status
from ..retrieval import QueryEvent, QueryResult, clean_service_id

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ..client import AsyncClient, Client
    from .ingestion import AsyncIngestionAPI, CorpusBuild, IngestionAPI

# Gateway routes flap while propagating; require this many consecutive 200s
# before treating the service as serving (UI: SERVING_CONSECUTIVE_OK).
SERVING_CONSECUTIVE_OK = 3


def _service_path_of(record: dict[str, Any]) -> str | None:
    """Gateway path of the project's AutoGraph service from its ACP record."""
    meta = record.get("projectMetadata") or {}
    service = meta.get("autographService") or {}
    url = service.get("serviceUrl")
    if not url:
        return None
    return urlparse(str(url)).path.rstrip("/")


def _mirror_of(record: dict[str, Any], key: str) -> dict[str, Any] | None:
    """One run mirror out of the ACP project record's autographService meta."""
    meta = record.get("projectMetadata") or {}
    service = meta.get("autographService") or {}
    mirror = service.get(key)
    return dict(mirror) if isinstance(mirror, dict) else None


def _retriever_ids_of(record: dict[str, Any]) -> list[str]:
    meta = record.get("projectMetadata") or {}
    services = meta.get("retrieverServices") or []
    return [
        str(service.get("serviceId", ""))
        for service in services
        if service.get("serviceId")
    ]


def _choose_retriever_id(project_name: str, ids: list[str]) -> str:
    """The single metadata retriever; 0 or >1 without an explicit id is an
    error the caller must resolve."""
    if len(ids) == 1:
        return ids[0]
    if not ids:
        raise ServiceNotReadyError(
            f"project {project_name!r} has no deployed retriever yet; "
            "call deploy_retriever() first"
        )
    cleaned = ", ".join(clean_service_id(one) for one in ids)
    raise ConfigError(
        f"project {project_name!r} has {len(ids)} retrievers ({cleaned}); "
        "pass retriever_id to pick one"
    )


def _with_citable_url(upload: FileUpload, url: str | None) -> FileUpload:
    if url is None:
        return upload
    # Merge instead of replace: FileUpload callers may carry their own
    # custom_metadata next to the citable_url. A fresh object keeps the
    # caller's input untouched.
    merged = dict(upload.custom_metadata or {})
    merged["citable_url"] = url
    return FileUpload(name=upload.name, content=upload.content, custom_metadata=merged)


def _resolve_upload_source(
    source: str | Path | Sequence[str | Path] | Sequence[FileUpload],
    citable_urls: dict[str, str] | None,
) -> tuple[Path | None, list[FileUpload]]:
    """add_files' source normalized to (folder, []) or (None, uploads).

    Local file-system work (stat, glob, read_bytes) stays synchronous also
    on the async path: alpha-scale corpora read in milliseconds and the
    uploads dominate.
    """
    entries: Sequence[str | Path | FileUpload]
    if isinstance(source, (str, Path)):
        path = Path(source)
        if path.is_dir():
            if citable_urls:
                # The folder walk renames on flatten/dedupe, so a
                # name-keyed mapping could silently miss files.
                raise ConfigError(
                    "citable_urls needs an explicit file list; "
                    "folder uploads rename files while flattening"
                )
            return path, []
        if not path.exists() and _glob.has_magic(str(source)):
            matches = sorted(_glob.glob(str(source)))
            if not matches:
                raise ConfigError(f"glob {str(path)!r} matched no files")
            entries = matches
        else:
            entries = [path]
    else:
        entries = list(source)
    mapping = citable_urls or {}
    uploads: list[FileUpload] = []
    for entry in entries:
        upload = (
            entry
            if isinstance(entry, FileUpload)
            else FileUpload(name=Path(entry).name, content=Path(entry).read_bytes())
        )
        uploads.append(_with_citable_url(upload, mapping.get(upload.name)))
    # A key that matched nothing is a caller mistake (typo, renamed file);
    # dropping it silently would ship provenance-less files.
    unmatched = sorted(set(mapping) - {upload.name for upload in uploads})
    if unmatched:
        raise ConfigError(
            "citable_urls names matched no upload: " + ", ".join(unmatched)
        )
    # The store keys a file by (scope, name): two paths with the same
    # basename would silently overwrite each other as versions of one file.
    # The folder walk dedupes; explicit lists must fail visibly instead.
    names = [upload.name for upload in uploads]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise ConfigError(
            "duplicate stored file names (" + ", ".join(duplicates) + "): "
            "same-named files overwrite each other; rename them or pass "
            "FileUpload objects with distinct names"
        )
    return None, uploads


def _retriever_deploy_args(
    settings: dict[str, Any],
    *,
    chat_model: str | None,
    chat_provider: str | None,
    embedding_model: str | None,
    embedding_provider: str | None,
    chat_secret_profile_id: str | None,
    embedding_secret_profile_id: str | None,
    chat_api_url: str | None,
    embedding_api_url: str | None,
) -> dict[str, Any]:
    """deploy_retriever arguments defaulted from persisted model settings."""
    chat_model = chat_model or settings.get("chatModel")
    if not chat_model:
        raise ConfigError(
            "no chat model: pass chat_model or deploy the AutoGraph "
            "service first so model settings are persisted"
        )
    return {
        "chat_model": chat_model,
        "chat_provider": chat_provider or settings.get("chatApiProvider") or "openai",
        "embedding_model": embedding_model or settings.get("embeddingModel"),
        "embedding_provider": (
            embedding_provider or settings.get("embeddingApiProvider")
        ),
        "chat_secret_profile_id": (
            chat_secret_profile_id or settings.get("chatSecretProfileId")
        ),
        "embedding_secret_profile_id": (
            embedding_secret_profile_id or settings.get("embeddingSecretProfileId")
        ),
        "chat_api_url": chat_api_url or settings.get("chatApiUrl"),
        "embedding_api_url": embedding_api_url or settings.get("embeddingApiUrl"),
    }


def _service_delete_result(payload: dict[str, Any]) -> dict[str, Any]:
    """Service teardown response with `deleted` and `warnings` guaranteed."""
    normalized = dict(payload)
    normalized["deleted"] = bool(payload.get("deleted", False))
    normalized["warnings"] = list(payload.get("warnings") or [])
    return normalized


def _acp_delete_result(payload: dict[str, Any]) -> dict[str, Any]:
    """The plain ACP delete answers {"success": bool}; synthesized into the
    service-teardown shape so callers never key-sniff which phase ran."""
    return {"deleted": bool(payload.get("success")), "warnings": []}


class AutoGraphProject:
    """Handle for one AutoGraph project (name + configured database)."""

    def __init__(self, client: "Client", name: str) -> None:
        self._client = client
        self.name = name
        self._ingestion_api: "IngestionAPI | None" = None
        # The retriever this handle deployed; ask() prefers it over metadata.
        self._retriever_id: str | None = None

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
        return _service_path_of(self.metadata())

    def require_service_path(self) -> str:
        path = self.service_path()
        if not path:
            raise ServiceNotReadyError(
                f"project {self.name!r} has no deployed AutoGraph service yet"
            )
        return path

    # -- health --------------------------------------------------------------

    def ping_health(self) -> bool:
        """One health probe; healthy means 2xx (route may still flap).

        Transport flaps are "not yet"; SDK-typed errors (AuthenticationError,
        APIConnectionError from the token mint) must propagate — retrying
        cannot fix bad credentials. Unlike the retriever gate this one
        deliberately keeps polling through 5xx: the AutoGraph pod answers
        errors while warming up, and the UI's pingAutographHealth only
        checks res.ok too.
        """
        path = self.service_path()
        if not path:
            return False
        try:
            response = self._client.http.get(f"{path}/v1/health")
        except httpx.HTTPError:  # a failed probe request is just "not yet"
            return False
        return 200 <= response.status_code < 300

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

    # -- files -----------------------------------------------------------------

    def add_files(
        self,
        source: str | Path | Sequence[str | Path] | Sequence[FileUpload],
        *,
        category: str | None = None,
        citable_urls: dict[str, str] | None = None,
    ) -> UploadResult:
        """Upload documents into this project.

        `source` is a folder, a file path, a glob pattern, a sequence of
        paths, or prepared FileUpload objects. `citable_urls` maps stored
        file names to the URL inline citations should link to (per-file
        custom_metadata, consumed end to end by the backend, AIS-1740).
        """
        folder, uploads = _resolve_upload_source(source, citable_urls)
        if folder is not None:
            return self._client.files.upload_folder(
                self.name, folder, category=category
            )
        return self._client.files.upload(self.name, uploads, category=category)

    def files(
        self,
        *,
        category: str | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        return self._client.files.list_files(
            self.name, category=category, search=search, limit=limit, offset=offset
        )

    def categories(self) -> list[tuple[str, int]]:
        return self._client.files.list_categories(self.name)

    # -- ingestion workflow ------------------------------------------------------

    @property
    def ingestion(self) -> "IngestionAPI":
        """The low-level ingestion API for this project (lazily bound)."""
        # Imported here, not at module top: ingestion.py imports this module.
        from .ingestion import IngestionAPI

        if self._ingestion_api is None:
            self._ingestion_api = IngestionAPI(self)
        return self._ingestion_api

    def build(
        self, *, categories: list[str] | None = None, incremental: bool = False
    ) -> "CorpusBuildRun":
        """Start a corpus build; returns a run handle (`.wait()` to block)."""
        started = self.ingestion.build_corpus(
            categories=categories, incremental=incremental
        )
        return CorpusBuildRun(self.ingestion, started)

    def strategize(
        self,
        complexity: str = "moderate",
        *,
        extract_images: bool = False,
        categories: list[str] | None = None,
        wait: bool = True,
        timeout: float = 1800.0,
    ) -> dict[str, Any] | str | None:
        """Run the RAG strategizer.

        Blocking by default: triggers the run, waits for it, and returns the
        generated strategy plan (what the Studio shows for review). With
        wait=False returns the job id (or None on older services) for a
        later wait_for_strategize.
        """
        # Pre-trigger mirror snapshot: the metadata mirror may still hold the
        # PREVIOUS run's terminal state, which the waiter must not trust.
        baseline = _mirror_of(self.metadata(), "ragstrategizer") if wait else None
        job_id = self.ingestion.strategize(
            complexity=complexity,
            extract_images=extract_images,
            categories=categories,
        )
        if not wait:
            return job_id
        self.ingestion.wait_for_strategize(job_id, timeout=timeout, baseline=baseline)
        return self.ingestion.strategies()

    def strategies(self) -> dict[str, Any]:
        return self.ingestion.strategies()

    def update_strategy(
        self,
        cluster_id: str,
        *,
        graph_rag: bool,
        entity_types: list[str] | None = None,
        extract_images: bool = False,
    ) -> dict[str, Any]:
        return self.ingestion.update_strategy(
            cluster_id,
            graph_rag=graph_rag,
            entity_types=entity_types,
            extract_images=extract_images,
        )

    def orchestrate(
        self,
        *,
        replicas: int = 1,
        categories: list[str] | None = None,
        chat_secret_profile_ids: list[str] | None = None,
        embedding_secret_profile_id: str | None = None,
    ) -> "OrchestrationRun":
        """Start the knowledge-graph build; returns a run handle."""
        # Pre-trigger mirror snapshot: the metadata mirror may still hold the
        # PREVIOUS run's terminal state, which the waiter must not trust.
        baseline = _mirror_of(self.metadata(), "importerOrchestration")
        orchestration_id = self.ingestion.orchestrate(
            replicas=replicas,
            categories=categories,
            chat_secret_profile_ids=chat_secret_profile_ids,
            embedding_secret_profile_id=embedding_secret_profile_id,
        )
        return OrchestrationRun(self.ingestion, orchestration_id, baseline=baseline)

    def overview(self) -> dict[str, Any]:
        return self.ingestion.overview()

    # -- retrieval -----------------------------------------------------------------

    def deploy_retriever(
        self,
        *,
        chat_model: str | None = None,
        chat_provider: str | None = None,
        embedding_model: str | None = None,
        embedding_provider: str | None = None,
        chat_secret_profile_id: str | None = None,
        embedding_secret_profile_id: str | None = None,
        chat_api_url: str | None = None,
        embedding_api_url: str | None = None,
        wait: bool = True,
        deploy_timeout: float = 300.0,
        health_timeout: float = 300.0,
    ) -> dict[str, Any]:
        """Deploy a retriever for this project.

        Every argument defaults from the project's persisted model settings
        (the config the AutoGraph service stored at deploy/build time), so a
        plain deploy_retriever() reuses exactly what the project was built
        with. The deployed service id is cached for ask().
        """
        args = _retriever_deploy_args(
            self.model_settings(),
            chat_model=chat_model,
            chat_provider=chat_provider,
            embedding_model=embedding_model,
            embedding_provider=embedding_provider,
            chat_secret_profile_id=chat_secret_profile_id,
            embedding_secret_profile_id=embedding_secret_profile_id,
            chat_api_url=chat_api_url,
            embedding_api_url=embedding_api_url,
        )
        info = self._client.retrievers.deploy(
            self.name,
            wait=wait,
            deploy_timeout=deploy_timeout,
            health_timeout=health_timeout,
            **args,
        )
        service_id = str(info.get("serviceId", ""))
        if service_id:
            self._retriever_id = service_id
        return info

    def retriever_ids(self) -> list[str]:
        """Service ids of this project's deployed retrievers (from metadata)."""
        return _retriever_ids_of(self.metadata())

    def ask(
        self,
        query: str,
        *,
        retriever_id: str | None = None,
        mode: str = "INSTANT",
        include_metadata: bool = True,
        use_cache: bool = False,
        show_citations: bool = False,
        response_instructions: str | None = None,
        model: str | None = None,
        timeout: float = 600.0,
    ) -> QueryResult:
        """Blocking query against this project's retriever."""
        return self._client.retrievers.query(
            self._resolve_retriever_id(retriever_id),
            query,
            mode=mode,
            include_metadata=include_metadata,
            use_cache=use_cache,
            show_citations=show_citations,
            response_instructions=response_instructions,
            model=model,
            timeout=timeout,
        )

    def ask_stream(
        self,
        query: str,
        *,
        retriever_id: str | None = None,
        mode: str = "INSTANT",
        include_metadata: bool = True,
        use_cache: bool = False,
        show_citations: bool = False,
        response_instructions: str | None = None,
        model: str | None = None,
        timeout: float = 600.0,
    ) -> Iterator[QueryEvent]:
        """Streaming query: TokenDelta / Progress events, then one Final."""
        return self._client.retrievers.query_stream(
            self._resolve_retriever_id(retriever_id),
            query,
            mode=mode,
            include_metadata=include_metadata,
            use_cache=use_cache,
            show_citations=show_citations,
            response_instructions=response_instructions,
            model=model,
            timeout=timeout,
        )

    def _resolve_retriever_id(self, explicit: str | None) -> str:
        """Explicit id > the one this handle deployed > the single one in
        metadata. Multiple retrievers without an explicit id is ambiguous."""
        if explicit:
            return explicit
        if self._retriever_id:
            return self._retriever_id
        return _choose_retriever_id(self.name, self.retriever_ids())

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

        Both phases return one shape: {"deleted": bool, "warnings": [...]}.
        """
        path = self.service_path()
        if path:
            response = raise_for_status(
                self._client.http.delete(
                    f"{path}/v1/projects/{quote(self.name, safe='')}",
                    params={"delete_files": str(delete_files).lower()},
                )
            )
            return _service_delete_result(dict(response.json()))
        return _acp_delete_result(self._client.acp.delete_project(self.name))


class CorpusBuildRun:
    """Handle of a started corpus build: poll or block on it."""

    def __init__(self, ingestion: "IngestionAPI", started: "CorpusBuild") -> None:
        self._ingestion = ingestion
        self.build_id = started.build_id
        self.graph_name = started.graph_name

    def status(self) -> dict[str, Any]:
        return self._ingestion.corpus_build_status(self.build_id)

    def wait(self, *, timeout: float = 1800.0, interval: float = 5.0) -> dict[str, Any]:
        """Block to the terminal state; the completed dict may still carry an
        errorCode (partial success) — see IngestionAPI.wait_for_build."""
        return self._ingestion.wait_for_build(
            self.build_id, timeout=timeout, interval=interval
        )


class OrchestrationRun:
    """Handle of a started knowledge-graph orchestration."""

    def __init__(
        self,
        ingestion: "IngestionAPI",
        orchestration_id: str | None,
        *,
        baseline: dict[str, Any] | None = None,
    ) -> None:
        self._ingestion = ingestion
        self.orchestration_id = orchestration_id
        # Pre-trigger mirror snapshot; wait() uses it to tell this run's
        # mirror state from the previous run's terminal echo.
        self._baseline = baseline

    def status(self) -> dict[str, Any] | None:
        if self.orchestration_id is None:
            return None
        return self._ingestion.orchestration_status(self.orchestration_id)

    def wait(self, *, timeout: float = 7200.0, interval: float = 5.0) -> dict[str, Any]:
        return self._ingestion.wait_for_orchestration(
            self.orchestration_id,
            timeout=timeout,
            interval=interval,
            baseline=self._baseline,
        )


class AsyncAutoGraphProject:
    """Async twin of AutoGraphProject: same surface, awaited I/O."""

    def __init__(self, client: "AsyncClient", name: str) -> None:
        self._client = client
        self.name = name
        self._ingestion_api: "AsyncIngestionAPI | None" = None
        # The retriever this handle deployed; ask() prefers it over metadata.
        self._retriever_id: str | None = None

    @property
    def database(self) -> str:
        return self._client.acp.database

    def __repr__(self) -> str:
        return f"AsyncAutoGraphProject(name={self.name!r}, database={self.database!r})"

    # -- metadata ------------------------------------------------------------

    async def metadata(self) -> dict[str, Any]:
        """Fresh ACP project record (metadata appears asynchronously)."""
        return await self._client.acp.get_project(self.name)

    async def model_settings(self) -> dict[str, Any]:
        """Persisted model settings (secret profile ids, never raw keys)."""
        settings = (await self.metadata()).get("modelSettings") or {}
        return dict(settings)

    async def service_path(self) -> str | None:
        """Async twin of AutoGraphProject.service_path (re-read per call)."""
        return _service_path_of(await self.metadata())

    async def require_service_path(self) -> str:
        path = await self.service_path()
        if not path:
            raise ServiceNotReadyError(
                f"project {self.name!r} has no deployed AutoGraph service yet"
            )
        return path

    # -- health --------------------------------------------------------------

    async def ping_health(self) -> bool:
        """One health probe; healthy means 2xx (route may still flap).

        Same probe contract as the sync twin: transport flaps are "not yet",
        SDK-typed errors propagate, and the gate deliberately keeps polling
        through 5xx (UI parity: pingAutographHealth only checks res.ok),
        unlike the retriever gate.
        """
        path = await self.service_path()
        if not path:
            return False
        try:
            response = await self._client.http.get(f"{path}/v1/health")
        except httpx.HTTPError:  # a failed probe request is just "not yet"
            return False
        return 200 <= response.status_code < 300

    async def wait_until_serving(
        self,
        *,
        streak: int = SERVING_CONSECUTIVE_OK,
        interval: float = 5.0,
        timeout: float = 300.0,
    ) -> None:
        """Async twin of AutoGraphProject.wait_until_serving."""
        await async_wait_for_streak(
            self.ping_health,
            needed=streak,
            interval=interval,
            timeout=timeout,
            description=f"AutoGraph service of project {self.name!r} to serve",
        )

    # -- files -----------------------------------------------------------------

    async def add_files(
        self,
        source: str | Path | Sequence[str | Path] | Sequence[FileUpload],
        *,
        category: str | None = None,
        citable_urls: dict[str, str] | None = None,
    ) -> UploadResult:
        """Async twin of AutoGraphProject.add_files (local reads stay sync)."""
        folder, uploads = _resolve_upload_source(source, citable_urls)
        if folder is not None:
            return await self._client.files.upload_folder(
                self.name, folder, category=category
            )
        return await self._client.files.upload(self.name, uploads, category=category)

    async def files(
        self,
        *,
        category: str | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        return await self._client.files.list_files(
            self.name, category=category, search=search, limit=limit, offset=offset
        )

    async def categories(self) -> list[tuple[str, int]]:
        return await self._client.files.list_categories(self.name)

    # -- ingestion workflow ------------------------------------------------------

    @property
    def ingestion(self) -> "AsyncIngestionAPI":
        """The low-level ingestion API for this project (lazily bound)."""
        # Imported here, not at module top: ingestion.py imports this module.
        from .ingestion import AsyncIngestionAPI

        if self._ingestion_api is None:
            self._ingestion_api = AsyncIngestionAPI(self)
        return self._ingestion_api

    async def build(
        self, *, categories: list[str] | None = None, incremental: bool = False
    ) -> "AsyncCorpusBuildRun":
        """Start a corpus build; returns a run handle (`await .wait()`)."""
        started = await self.ingestion.build_corpus(
            categories=categories, incremental=incremental
        )
        return AsyncCorpusBuildRun(self.ingestion, started)

    async def strategize(
        self,
        complexity: str = "moderate",
        *,
        extract_images: bool = False,
        categories: list[str] | None = None,
        wait: bool = True,
        timeout: float = 1800.0,
    ) -> dict[str, Any] | str | None:
        """Async twin of AutoGraphProject.strategize."""
        # Pre-trigger mirror snapshot: the metadata mirror may still hold the
        # PREVIOUS run's terminal state, which the waiter must not trust.
        baseline = _mirror_of(await self.metadata(), "ragstrategizer") if wait else None
        job_id = await self.ingestion.strategize(
            complexity=complexity,
            extract_images=extract_images,
            categories=categories,
        )
        if not wait:
            return job_id
        await self.ingestion.wait_for_strategize(
            job_id, timeout=timeout, baseline=baseline
        )
        return await self.ingestion.strategies()

    async def strategies(self) -> dict[str, Any]:
        return await self.ingestion.strategies()

    async def update_strategy(
        self,
        cluster_id: str,
        *,
        graph_rag: bool,
        entity_types: list[str] | None = None,
        extract_images: bool = False,
    ) -> dict[str, Any]:
        return await self.ingestion.update_strategy(
            cluster_id,
            graph_rag=graph_rag,
            entity_types=entity_types,
            extract_images=extract_images,
        )

    async def orchestrate(
        self,
        *,
        replicas: int = 1,
        categories: list[str] | None = None,
        chat_secret_profile_ids: list[str] | None = None,
        embedding_secret_profile_id: str | None = None,
    ) -> "AsyncOrchestrationRun":
        """Start the knowledge-graph build; returns a run handle."""
        # Pre-trigger mirror snapshot: the metadata mirror may still hold the
        # PREVIOUS run's terminal state, which the waiter must not trust.
        baseline = _mirror_of(await self.metadata(), "importerOrchestration")
        orchestration_id = await self.ingestion.orchestrate(
            replicas=replicas,
            categories=categories,
            chat_secret_profile_ids=chat_secret_profile_ids,
            embedding_secret_profile_id=embedding_secret_profile_id,
        )
        return AsyncOrchestrationRun(
            self.ingestion, orchestration_id, baseline=baseline
        )

    async def overview(self) -> dict[str, Any]:
        return await self.ingestion.overview()

    # -- retrieval -----------------------------------------------------------------

    async def deploy_retriever(
        self,
        *,
        chat_model: str | None = None,
        chat_provider: str | None = None,
        embedding_model: str | None = None,
        embedding_provider: str | None = None,
        chat_secret_profile_id: str | None = None,
        embedding_secret_profile_id: str | None = None,
        chat_api_url: str | None = None,
        embedding_api_url: str | None = None,
        wait: bool = True,
        deploy_timeout: float = 300.0,
        health_timeout: float = 300.0,
    ) -> dict[str, Any]:
        """Async twin of AutoGraphProject.deploy_retriever."""
        args = _retriever_deploy_args(
            await self.model_settings(),
            chat_model=chat_model,
            chat_provider=chat_provider,
            embedding_model=embedding_model,
            embedding_provider=embedding_provider,
            chat_secret_profile_id=chat_secret_profile_id,
            embedding_secret_profile_id=embedding_secret_profile_id,
            chat_api_url=chat_api_url,
            embedding_api_url=embedding_api_url,
        )
        info = await self._client.retrievers.deploy(
            self.name,
            wait=wait,
            deploy_timeout=deploy_timeout,
            health_timeout=health_timeout,
            **args,
        )
        service_id = str(info.get("serviceId", ""))
        if service_id:
            self._retriever_id = service_id
        return info

    async def retriever_ids(self) -> list[str]:
        """Service ids of this project's deployed retrievers (from metadata)."""
        return _retriever_ids_of(await self.metadata())

    async def ask(
        self,
        query: str,
        *,
        retriever_id: str | None = None,
        mode: str = "INSTANT",
        include_metadata: bool = True,
        use_cache: bool = False,
        show_citations: bool = False,
        response_instructions: str | None = None,
        model: str | None = None,
        timeout: float = 600.0,
    ) -> QueryResult:
        """Blocking query against this project's retriever."""
        return await self._client.retrievers.query(
            await self._resolve_retriever_id(retriever_id),
            query,
            mode=mode,
            include_metadata=include_metadata,
            use_cache=use_cache,
            show_citations=show_citations,
            response_instructions=response_instructions,
            model=model,
            timeout=timeout,
        )

    async def ask_stream(
        self,
        query: str,
        *,
        retriever_id: str | None = None,
        mode: str = "INSTANT",
        include_metadata: bool = True,
        use_cache: bool = False,
        show_citations: bool = False,
        response_instructions: str | None = None,
        model: str | None = None,
        timeout: float = 600.0,
    ) -> AsyncIterator[QueryEvent]:
        """Streaming query: TokenDelta / Progress events, then one Final.

        An async generator (retriever resolution needs an await), so unlike
        the sync twin argument validation surfaces at the first iteration,
        not at the call.
        """
        events = self._client.retrievers.query_stream(
            await self._resolve_retriever_id(retriever_id),
            query,
            mode=mode,
            include_metadata=include_metadata,
            use_cache=use_cache,
            show_citations=show_citations,
            response_instructions=response_instructions,
            model=model,
            timeout=timeout,
        )
        async for event in events:
            yield event

    async def _resolve_retriever_id(self, explicit: str | None) -> str:
        """Explicit id > the one this handle deployed > the single one in
        metadata. Multiple retrievers without an explicit id is ambiguous."""
        if explicit:
            return explicit
        if self._retriever_id:
            return self._retriever_id
        return _choose_retriever_id(self.name, await self.retriever_ids())

    # -- teardown --------------------------------------------------------------

    async def delete(self, *, delete_files: bool = True) -> dict[str, Any]:
        """Async twin of AutoGraphProject.delete (same two-phase contract,
        same normalized {"deleted", "warnings"} shape)."""
        path = await self.service_path()
        if path:
            response = raise_for_status(
                await self._client.http.delete(
                    f"{path}/v1/projects/{quote(self.name, safe='')}",
                    params={"delete_files": str(delete_files).lower()},
                )
            )
            return _service_delete_result(dict(response.json()))
        return _acp_delete_result(await self._client.acp.delete_project(self.name))


class AsyncCorpusBuildRun:
    """Async twin of CorpusBuildRun."""

    def __init__(self, ingestion: "AsyncIngestionAPI", started: "CorpusBuild") -> None:
        self._ingestion = ingestion
        self.build_id = started.build_id
        self.graph_name = started.graph_name

    async def status(self) -> dict[str, Any]:
        return await self._ingestion.corpus_build_status(self.build_id)

    async def wait(
        self, *, timeout: float = 1800.0, interval: float = 5.0
    ) -> dict[str, Any]:
        """Block to the terminal state; the completed dict may still carry an
        errorCode (partial success) — see IngestionAPI.wait_for_build."""
        return await self._ingestion.wait_for_build(
            self.build_id, timeout=timeout, interval=interval
        )


class AsyncOrchestrationRun:
    """Async twin of OrchestrationRun."""

    def __init__(
        self,
        ingestion: "AsyncIngestionAPI",
        orchestration_id: str | None,
        *,
        baseline: dict[str, Any] | None = None,
    ) -> None:
        self._ingestion = ingestion
        self.orchestration_id = orchestration_id
        # Pre-trigger mirror snapshot; wait() uses it to tell this run's
        # mirror state from the previous run's terminal echo.
        self._baseline = baseline

    async def status(self) -> dict[str, Any] | None:
        if self.orchestration_id is None:
            return None
        return await self._ingestion.orchestration_status(self.orchestration_id)

    async def wait(
        self, *, timeout: float = 7200.0, interval: float = 5.0
    ) -> dict[str, Any]:
        return await self._ingestion.wait_for_orchestration(
            self.orchestration_id,
            timeout=timeout,
            interval=interval,
            baseline=self._baseline,
        )
