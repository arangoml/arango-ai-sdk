"""The AutoGraphProject handle: everything scoped to one project.

The AutoGraph service has no fixed gateway prefix: each instance gets its own
ArangoRoute (/autograph/{postfix}/), recorded in ACP project metadata as
autographService.serviceUrl. The SDK keeps only that URL's path and joins it
onto the configured gateway base, so calls stay deployment-parity safe.
"""

from __future__ import annotations

import glob as _glob
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator, Sequence
from urllib.parse import urlparse

from .._polling import wait_for_streak
from ..exceptions import ConfigError, ServiceNotReadyError
from ..filemanager import FileUpload, UploadResult
from ..http import raise_for_status
from ..retrieval import QueryEvent, QueryResult, clean_service_id

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ..client import Client
    from .ingestion import CorpusBuild, IngestionAPI

# Gateway routes flap while propagating; require this many consecutive 200s
# before treating the service as serving (UI: SERVING_CONSECUTIVE_OK).
SERVING_CONSECUTIVE_OK = 3


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
        files_api = self._client.files
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
                return files_api.upload_folder(self.name, path, category=category)
            if not path.exists() and _glob.has_magic(str(source)):
                source = sorted(_glob.glob(str(source)))
                if not source:
                    raise ConfigError(f"glob {str(path)!r} matched no files")
            else:
                source = [path]
        uploads = [
            (
                entry
                if isinstance(entry, FileUpload)
                else self._file_upload_from_path(Path(entry), citable_urls or {})
            )
            for entry in source
        ]
        return files_api.upload(self.name, uploads, category=category)

    @staticmethod
    def _file_upload_from_path(path: Path, citable_urls: dict[str, str]) -> FileUpload:
        url = citable_urls.get(path.name)
        return FileUpload(
            name=path.name,
            content=path.read_bytes(),
            custom_metadata={"citable_url": url} if url else None,
        )

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
        job_id = self.ingestion.strategize(
            complexity=complexity,
            extract_images=extract_images,
            categories=categories,
        )
        if not wait:
            return job_id
        self.ingestion.wait_for_strategize(job_id, timeout=timeout)
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
        orchestration_id = self.ingestion.orchestrate(
            replicas=replicas,
            categories=categories,
            chat_secret_profile_ids=chat_secret_profile_ids,
            embedding_secret_profile_id=embedding_secret_profile_id,
        )
        return OrchestrationRun(self.ingestion, orchestration_id)

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
    ) -> dict[str, Any]:
        """Deploy a retriever for this project.

        Every argument defaults from the project's persisted model settings
        (the config the AutoGraph service stored at deploy/build time), so a
        plain deploy_retriever() reuses exactly what the project was built
        with. The deployed service id is cached for ask().
        """
        settings = self.model_settings()
        chat_model = chat_model or settings.get("chatModel")
        if not chat_model:
            raise ConfigError(
                "no chat model: pass chat_model or deploy the AutoGraph "
                "service first so model settings are persisted"
            )
        info = self._client.retrievers.deploy(
            self.name,
            chat_model=chat_model,
            chat_provider=(
                chat_provider or settings.get("chatApiProvider") or "openai"
            ),
            embedding_model=embedding_model or settings.get("embeddingModel"),
            embedding_provider=(
                embedding_provider or settings.get("embeddingApiProvider")
            ),
            chat_secret_profile_id=(
                chat_secret_profile_id or settings.get("chatSecretProfileId")
            ),
            embedding_secret_profile_id=(
                embedding_secret_profile_id or settings.get("embeddingSecretProfileId")
            ),
            chat_api_url=chat_api_url or settings.get("chatApiUrl"),
            embedding_api_url=embedding_api_url or settings.get("embeddingApiUrl"),
            wait=wait,
        )
        service_id = str(info.get("serviceId", ""))
        if service_id:
            self._retriever_id = service_id
        return info

    def retriever_ids(self) -> list[str]:
        """Service ids of this project's deployed retrievers (from metadata)."""
        meta = self.metadata().get("projectMetadata") or {}
        services = meta.get("retrieverServices") or []
        return [
            str(service.get("serviceId", ""))
            for service in services
            if service.get("serviceId")
        ]

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
        ids = self.retriever_ids()
        if len(ids) == 1:
            return ids[0]
        if not ids:
            raise ServiceNotReadyError(
                f"project {self.name!r} has no deployed retriever yet; "
                "call deploy_retriever() first"
            )
        cleaned = ", ".join(clean_service_id(one) for one in ids)
        raise ConfigError(
            f"project {self.name!r} has {len(ids)} retrievers ({cleaned}); "
            "pass retriever_id to pick one"
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

    def __init__(self, ingestion: "IngestionAPI", orchestration_id: str | None) -> None:
        self._ingestion = ingestion
        self.orchestration_id = orchestration_id

    def status(self) -> dict[str, Any] | None:
        if self.orchestration_id is None:
            return None
        return self._ingestion.orchestration_status(self.orchestration_id)

    def wait(self, *, timeout: float = 7200.0, interval: float = 5.0) -> dict[str, Any]:
        return self._ingestion.wait_for_orchestration(
            self.orchestration_id, timeout=timeout, interval=interval
        )
