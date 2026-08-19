"""AutoGraph namespace: explicitly AutoGraph-typed projects and their workflow.

`client.autograph.create_project(...)` is the entry point. It always creates
an AutoGraph-typed project on the wire (project_type="autograph") — there is
no generic project creation in the public API.

AutoGraphAPI and AsyncAutoGraphAPI are twins: env building, secret-profile
naming and id extraction, and the project-type filter are shared; the twins
add only the I/O.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from ..exceptions import ConfigError
from .project import (
    AsyncAutoGraphProject,
    AsyncCorpusBuildRun,
    AsyncOrchestrationRun,
    AutoGraphProject,
    CorpusBuildRun,
    OrchestrationRun,
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ..client import AsyncClient, Client

__all__ = [
    "AsyncAutoGraphAPI",
    "AsyncAutoGraphProject",
    "AsyncCorpusBuildRun",
    "AsyncOrchestrationRun",
    "AutoGraphAPI",
    "AutoGraphProject",
    "CorpusBuildRun",
    "OrchestrationRun",
    "build_autograph_env",
]

_PROJECT_TYPE = "autograph"

_MISSING_CREDENTIALS = (
    "deploying needs credentials: pass openai_api_key or "
    "chat_secret_profile_id (plus optional embedding_secret_profile_id)"
)


def build_autograph_env(
    *,
    database: str,
    project_name: str,
    chat_provider: str,
    chat_model: str,
    embedding_provider: str,
    embedding_model: str,
    chat_secret_profile_id: str,
    embedding_secret_profile_id: str,
    multimodal_model: str | None = None,
    chat_api_url: str | None = None,
    embedding_api_url: str | None = None,
    fps_recovery_username: str | None = None,
) -> dict[str, str]:
    """Deploy env for the AutoGraph service.

    Mirrors the Studio UI's deployEnvFor + startAutographDeploy: snake_case
    keys, optional keys omitted entirely (the service falls back to its own
    defaults), api_url only for custom providers, always secret profile ids.
    """
    env: dict[str, str] = {
        "db_name": database,
        "genai_project_name": project_name,
        "chat_api_provider": chat_provider,
        "embedding_api_provider": embedding_provider,
        "chat_model": chat_model,
        "embedding_model": embedding_model,
        "chat_secret_profile_id": chat_secret_profile_id,
        "embedding_secret_profile_id": embedding_secret_profile_id,
    }
    if multimodal_model:
        env["multimodal_model"] = multimodal_model
    if chat_api_url:
        env["chat_api_url"] = chat_api_url
    if embedding_api_url:
        env["embedding_api_url"] = embedding_api_url
    if fps_recovery_username:
        # FPS recovers interrupted parsing jobs as a named user (AIS-1695).
        env["fps_recovery_username"] = fps_recovery_username
    return env


def _secret_profile_name(project_name: str) -> str:
    return f"{project_name}-llm-{int(time.time())}"


def _profile_id_of(profile: dict[str, Any]) -> str:
    profile_id = str(profile.get("profileId") or profile.get("id") or "")
    if not profile_id:
        raise ConfigError("secret profile created but no profile id in response")
    return profile_id


def _autograph_project_names(projects: dict[str, dict[str, Any]]) -> list[str]:
    return sorted(
        name
        for name, data in projects.items()
        if data.get("projectType") == _PROJECT_TYPE
    )


class AutoGraphAPI:
    """client.autograph — AutoGraph project lifecycle."""

    def __init__(self, client: "Client") -> None:
        self._client = client

    def create_project(
        self,
        name: str,
        *,
        description: str | None = None,
        deploy: bool = True,
        openai_api_key: str | None = None,
        chat_provider: str = "openai",
        chat_model: str = "gpt-4.1",
        embedding_provider: str | None = None,
        embedding_model: str = "text-embedding-3-small",
        multimodal_model: str | None = None,
        chat_secret_profile_id: str | None = None,
        embedding_secret_profile_id: str | None = None,
        chat_api_url: str | None = None,
        embedding_api_url: str | None = None,
        wait: bool = True,
        deploy_timeout: float = 300.0,
        serving_timeout: float = 300.0,
    ) -> AutoGraphProject:
        """Create an AutoGraph project; by default also deploy its service.

        The full onboarding the Studio UI performs: ACP project create ->
        secret profile (created from openai_api_key unless explicit profile
        ids are given) -> deploy the arangodb-autograph service -> wait for
        DEPLOYED -> health-streak gate until the pod actually serves.
        """
        acp = self._client.acp
        acp.create_project(name, project_type=_PROJECT_TYPE, description=description)
        project = AutoGraphProject(self._client, name)
        if not deploy:
            return project

        chat_id, embedding_id = self._resolve_secret_ids(
            name,
            openai_api_key=openai_api_key,
            chat_secret_profile_id=chat_secret_profile_id,
            embedding_secret_profile_id=embedding_secret_profile_id,
        )
        env = build_autograph_env(
            database=acp.database,
            project_name=name,
            chat_provider=chat_provider,
            chat_model=chat_model,
            embedding_provider=embedding_provider or chat_provider,
            embedding_model=embedding_model,
            chat_secret_profile_id=chat_id,
            embedding_secret_profile_id=embedding_id,
            multimodal_model=multimodal_model,
            chat_api_url=chat_api_url,
            embedding_api_url=embedding_api_url,
            fps_recovery_username=self._identity_or_none(),
        )
        info = acp.start_service("autograph", env)
        if wait:
            acp.wait_service_deployed(
                str(info.get("serviceId", "")), timeout=deploy_timeout
            )
            project.wait_until_serving(timeout=serving_timeout)
        return project

    def project(self, name: str) -> AutoGraphProject:
        """Bind an existing AutoGraph project (verifies it exists)."""
        self._client.acp.get_project(name)
        return AutoGraphProject(self._client, name)

    def list_projects(self) -> list[str]:
        """Names of AutoGraph-typed projects in the configured database."""
        return _autograph_project_names(self._client.acp.list_projects())

    # -- internals -----------------------------------------------------------

    def _resolve_secret_ids(
        self,
        project_name: str,
        *,
        openai_api_key: str | None,
        chat_secret_profile_id: str | None,
        embedding_secret_profile_id: str | None,
    ) -> tuple[str, str]:
        """Secret profile ids for chat + embedding.

        Explicit profile ids win; a raw key is converted into ONE profile
        reused for both roles (the UI's fallback when no separate embedding
        key is given). Raw keys are never sent in a deploy env: orchestrate
        later requires profile ids, so a raw-key deploy would fail at KG
        build time.
        """
        if chat_secret_profile_id:
            return (
                chat_secret_profile_id,
                embedding_secret_profile_id or chat_secret_profile_id,
            )
        if openai_api_key:
            profile = self._client.acp.create_secret_profile(
                _secret_profile_name(project_name),
                openai_api_key,
                profile_type="LLM",
                provider="openai",
            )
            profile_id = _profile_id_of(profile)
            return profile_id, embedding_secret_profile_id or profile_id
        raise ConfigError(_MISSING_CREDENTIALS)

    def _identity_or_none(self) -> str | None:
        # Best-effort: an identity hiccup degrades FPS recovery, not the deploy.
        try:
            return self._client.whoami() or None
        except Exception:  # noqa: BLE001 - deliberate best-effort
            return None


class AsyncAutoGraphAPI:
    """Async twin of AutoGraphAPI: same onboarding flow, awaited I/O."""

    def __init__(self, client: "AsyncClient") -> None:
        self._client = client

    async def create_project(
        self,
        name: str,
        *,
        description: str | None = None,
        deploy: bool = True,
        openai_api_key: str | None = None,
        chat_provider: str = "openai",
        chat_model: str = "gpt-4.1",
        embedding_provider: str | None = None,
        embedding_model: str = "text-embedding-3-small",
        multimodal_model: str | None = None,
        chat_secret_profile_id: str | None = None,
        embedding_secret_profile_id: str | None = None,
        chat_api_url: str | None = None,
        embedding_api_url: str | None = None,
        wait: bool = True,
        deploy_timeout: float = 300.0,
        serving_timeout: float = 300.0,
    ) -> AsyncAutoGraphProject:
        """Async twin of AutoGraphAPI.create_project (same onboarding)."""
        acp = self._client.acp
        await acp.create_project(
            name, project_type=_PROJECT_TYPE, description=description
        )
        project = AsyncAutoGraphProject(self._client, name)
        if not deploy:
            return project

        chat_id, embedding_id = await self._resolve_secret_ids(
            name,
            openai_api_key=openai_api_key,
            chat_secret_profile_id=chat_secret_profile_id,
            embedding_secret_profile_id=embedding_secret_profile_id,
        )
        env = build_autograph_env(
            database=acp.database,
            project_name=name,
            chat_provider=chat_provider,
            chat_model=chat_model,
            embedding_provider=embedding_provider or chat_provider,
            embedding_model=embedding_model,
            chat_secret_profile_id=chat_id,
            embedding_secret_profile_id=embedding_id,
            multimodal_model=multimodal_model,
            chat_api_url=chat_api_url,
            embedding_api_url=embedding_api_url,
            fps_recovery_username=await self._identity_or_none(),
        )
        info = await acp.start_service("autograph", env)
        if wait:
            await acp.wait_service_deployed(
                str(info.get("serviceId", "")), timeout=deploy_timeout
            )
            await project.wait_until_serving(timeout=serving_timeout)
        return project

    async def project(self, name: str) -> AsyncAutoGraphProject:
        """Bind an existing AutoGraph project (verifies it exists)."""
        await self._client.acp.get_project(name)
        return AsyncAutoGraphProject(self._client, name)

    async def list_projects(self) -> list[str]:
        """Names of AutoGraph-typed projects in the configured database."""
        return _autograph_project_names(await self._client.acp.list_projects())

    # -- internals -----------------------------------------------------------

    async def _resolve_secret_ids(
        self,
        project_name: str,
        *,
        openai_api_key: str | None,
        chat_secret_profile_id: str | None,
        embedding_secret_profile_id: str | None,
    ) -> tuple[str, str]:
        """Async twin of AutoGraphAPI._resolve_secret_ids (same precedence)."""
        if chat_secret_profile_id:
            return (
                chat_secret_profile_id,
                embedding_secret_profile_id or chat_secret_profile_id,
            )
        if openai_api_key:
            profile = await self._client.acp.create_secret_profile(
                _secret_profile_name(project_name),
                openai_api_key,
                profile_type="LLM",
                provider="openai",
            )
            profile_id = _profile_id_of(profile)
            return profile_id, embedding_secret_profile_id or profile_id
        raise ConfigError(_MISSING_CREDENTIALS)

    async def _identity_or_none(self) -> str | None:
        # Best-effort: an identity hiccup degrades FPS recovery, not the deploy.
        try:
            return await self._client.whoami() or None
        except Exception:  # noqa: BLE001 - deliberate best-effort
            return None
