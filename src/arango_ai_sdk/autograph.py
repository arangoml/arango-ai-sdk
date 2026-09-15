"""The AutoGraph service of one project.

Reached as ``autograph`` on an ``AiProjectHandle``. A project has exactly one
AutoGraph service, so this object is created once per handle and ``deploy``
refuses to install a second one. Pipeline steps such as corpus build are added
here as methods.

The object never touches the transport. It builds the install request and
hands it to ``ServiceManager``, and it reads deployment state from the
``AiProject`` snapshot the handle refreshes on request.
"""

from collections.abc import Callable, Mapping

from arango_ai_sdk._naming import AcpPath, AutoGraphInstallParams
from arango_ai_sdk.exceptions import (
    AutoGraphAlreadyDeployedError,
    AutoGraphNotDeployedError,
)
from arango_ai_sdk.models import (
    AiProject,
    AutoGraphService,
    CreateEntityRequest,
    ServiceInfo,
)
from arango_ai_sdk.services import ServiceManager

__all__ = ["AutoGraph"]


class AutoGraph:
    """The single AutoGraph service of a project.

    Parameters
    ----------
    services : ServiceManager
        Sends install and delete requests to ACP.
    project : AiProject
        Snapshot of the project this service belongs to. Supplies the project
        name, the database and the deployed-service metadata.
    refresh : callable returning AiProject
        Reloads the project from the platform and returns the new snapshot.
        Called before ``deploy`` checks for an existing service and after a
        deploy or undeploy, so the state properties stay current.
    """

    def __init__(
        self,
        services: ServiceManager,
        project: Callable[[], AiProject],
        refresh: Callable[[], AiProject],
    ) -> None:
        self._services = services
        self._project: Callable[[], AiProject] = project
        self._refresh = refresh

    @property
    def is_deployed(self) -> bool:
        """Return whether the last project snapshot shows an AutoGraph service."""
        return self._deployed_service() is not None

    @property
    def service_id(self) -> str | None:
        """Return the deployed service id, or ``None`` when nothing is deployed."""
        service = self._deployed_service()
        return service.service_id if service is not None else None

    @property
    def service_url(self) -> str | None:
        """Return the deployed service URL, or ``None`` when nothing is deployed."""
        service = self._deployed_service()
        return service.service_url if service is not None else None

    def _deployed_service(self) -> AutoGraphService | None:
        """Return ``project_metadata.autograph_service`` from the snapshot, or ``None``."""
        project_metadata = self._project().project_metadata
        return project_metadata.autograph_service if project_metadata else None

    def deploy(
        self,
        *,
        chat_api_provider: str,
        embedding_api_provider: str,
        chat_secret_profile_id: str,
        embedding_secret_profile_id: str,
        fps_recovery_username: str,
        chat_model: str | None = None,
        embedding_model: str | None = None,
        chat_api_url: str | None = None,
        embedding_api_url: str | None = None,
        multimodal_model: str | None = None,
        labels: Mapping[str, str] | None = None,
    ) -> ServiceInfo:
        """Install AutoGraph for this project and return its service info.

        Steps: refresh the project, raise if it already has an AutoGraph
        service, build the install request, send it through
        ``ServiceManager.deploy_service`` to ``AcpPath.AUTOGRAPH``, refresh again.

        Raises
        ------
        AutoGraphAlreadyDeployedError
            The project already has an AutoGraph service.
        ProjectNotFoundError
            The project no longer exists on the platform.
        InvalidServiceParametersError
            ACP rejected an install parameter.
        ServiceError
            Any other error answer from the service.
        """
        self._refresh()
        if self.is_deployed:
            raise AutoGraphAlreadyDeployedError("The project already has an AutoGraph service.")
        request = self._build_install_request(
            chat_api_provider=chat_api_provider,
            embedding_api_provider=embedding_api_provider,
            chat_secret_profile_id=chat_secret_profile_id,
            embedding_secret_profile_id=embedding_secret_profile_id,
            fps_recovery_username=fps_recovery_username,
            chat_model=chat_model,
            embedding_model=embedding_model,
            chat_api_url=chat_api_url,
            embedding_api_url=embedding_api_url,
            multimodal_model=multimodal_model,
            labels=labels,
        )
        service_info = self._services.deploy_service(
            install_path=AcpPath.AUTOGRAPH, request=request
        )
        self._refresh()
        return service_info

    def undeploy(self) -> ServiceInfo:
        """Stop and remove this project's AutoGraph service.

        Steps: refresh the project, raise if it has no AutoGraph service, send
        ``ServiceManager.delete`` with the id from the metadata, refresh again.

        Raises
        ------
        AutoGraphNotDeployedError
            The project has no AutoGraph service.
        ServiceNotFoundError
            ACP no longer knows the service id the project metadata holds.
        ServiceError
            Any other error answer from the service.
        """
        self._refresh()
        if not self.service_id:
            raise AutoGraphNotDeployedError("The project has no AutoGraph service.")
        service_info = self._services.delete(service_id=self.service_id)
        self._refresh()
        return service_info

    def _build_install_request(
        self,
        chat_api_provider: str,
        embedding_api_provider: str,
        chat_secret_profile_id: str,
        embedding_secret_profile_id: str,
        fps_recovery_username: str,
        chat_model: str | None,
        embedding_model: str | None,
        chat_api_url: str | None,
        embedding_api_url: str | None,
        multimodal_model: str | None,
        labels: Mapping[str, str] | None,
    ) -> CreateEntityRequest:
        """Turn keyword arguments into the ACP install request. Sends nothing.

        The project name and database come from the AiProject snapshot, the rest from
        the arguments; optional arguments are added to the env map only when
        they are not ``None``.
        """
        env: dict[str, str] = {
            AutoGraphInstallParams.GENAI_PROJECT_NAME: self._project().project_name,
            AutoGraphInstallParams.DB_NAME: self._project().project_db_name,
            AutoGraphInstallParams.CHAT_API_PROVIDER: chat_api_provider,
            AutoGraphInstallParams.EMBEDDING_API_PROVIDER: embedding_api_provider,
            AutoGraphInstallParams.CHAT_SECRET_PROFILE_ID: chat_secret_profile_id,
            AutoGraphInstallParams.EMBEDDING_SECRET_PROFILE_ID: embedding_secret_profile_id,
            AutoGraphInstallParams.FPS_RECOVERY_USERNAME: fps_recovery_username,
        }
        optional = {
            AutoGraphInstallParams.CHAT_MODEL: chat_model,
            AutoGraphInstallParams.EMBEDDING_MODEL: embedding_model,
            AutoGraphInstallParams.CHAT_API_URL: chat_api_url,
            AutoGraphInstallParams.EMBEDDING_API_URL: embedding_api_url,
            AutoGraphInstallParams.MULTIMODAL_MODEL: multimodal_model,
        }
        env.update({key: value for key, value in optional.items() if value is not None})
        request = CreateEntityRequest(env=env)
        if labels is not None:
            request.labels = dict(labels)
        return request
