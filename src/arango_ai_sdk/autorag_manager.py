"""Manager for a project's retriever services, exposed as ``AiProjectHandle.autorag``.

A project can run several retrievers, each with its own models and secret
profiles, so the entry point is a manager rather than a single service
object: ``AutoRagManager`` deploys a new one and lists or looks up the
existing ones, handing each back as an ``AutoRag`` bound to its service id.

The manager never touches the transport. It builds the install request and
hands it to ``ServiceApi``, and it reads the deployed retrievers from the
``AiProject`` snapshot the handle refreshes on request.
"""

from collections.abc import Callable, Mapping

from arango_ai_sdk._autorag_api import AutoRagApi
from arango_ai_sdk._naming import AcpPath, AutoRagInstallParams
from arango_ai_sdk._service_api import ServiceApi
from arango_ai_sdk.autograph import DeployResult
from arango_ai_sdk.autorag import AutoRag
from arango_ai_sdk.exceptions import AutoRagNotDeployedError
from arango_ai_sdk.models import AiProject, CreateEntityRequest, ServiceInfo

__all__ = [
    "AutoRagDeployResult",
    "AutoRagManager",
]


class AutoRagDeployResult(DeployResult):
    """What ``AutoRagManager.deploy`` returns: the service record, readiness and the object.

    Attributes
    ----------
    service_info : ServiceInfo
        The service as ACP described it right after accepting the install.
    ready : bool or None
        ``True`` when ``deploy(wait=True)`` saw the health check answer ``OK``
        within the bound, ``False`` when the bound passed first, ``None`` when
        nobody waited (``wait=False``).
    autorag : AutoRag
        The object bound to the new service.
    """

    def __init__(self, service_info: ServiceInfo, ready: bool | None, autorag: AutoRag) -> None:
        super().__init__(service_info=service_info, ready=ready)
        self.autorag = autorag


class AutoRagManager:
    """Deploy, list and look up the retrievers of one project.

    Parameters
    ----------
    service_api : ServiceApi
        Sends install and delete requests to ACP.
    api : AutoRagApi
        Sends health and query requests to the retrievers themselves.
    project : callable returning AiProject
        Returns the current project snapshot.
    refresh : callable returning AiProject
        Reloads the project from the platform and returns the new snapshot.
    """

    def __init__(
        self,
        service_api: ServiceApi,
        api: AutoRagApi,
        project: Callable[[], AiProject],
        refresh: Callable[[], AiProject],
    ) -> None:
        self._service_api = service_api
        self._api = api
        self._project = project
        self._refresh = refresh

    def deploy(
        self,
        *,
        chat_api_provider: str,
        embedding_api_provider: str,
        chat_secret_profile_id: str,
        embedding_secret_profile_id: str,
        chat_model: str | None = None,
        embedding_model: str | None = None,
        chat_api_url: str | None = None,
        embedding_api_url: str | None = None,
        labels: Mapping[str, str] | None = None,
        wait: bool = False,
    ) -> AutoRagDeployResult:
        """Install a new retriever in this project and return the deploy result.

        Steps: build the install request, send it through
        ``ServiceApi.deploy_service`` to ``AcpPath.GRAPHRAG_RETRIEVER``,
        refresh the project, bind an :class:`AutoRag` to the new service id.
        ACP answers once Helm accepts the install, before the pod is up. With
        ``wait=True`` the call then runs :meth:`AutoRag.wait_until_ready` with
        its defaults and reports the outcome in ``ready``; a slow start never
        fails the deploy.

        Parameters
        ----------
        chat_api_provider : str
            Provider of the chat model, for example ``"openai"``.
        embedding_api_provider : str
            Provider of the embedding model, for example ``"openai"``.
        chat_secret_profile_id : str
            ID of the secret profile holding the chat provider's API key.
        embedding_secret_profile_id : str
            ID of the secret profile holding the embedding provider's API key.
        chat_model : str, optional
            Chat model name, for example ``"gpt-4o"``.
        embedding_model : str, optional
            Embedding model name, for example ``"text-embedding-3-small"``.
        chat_api_url : str, optional
            Override for the chat provider's endpoint.
        embedding_api_url : str, optional
            Override for the embedding provider's endpoint.
        labels : Mapping[str, str], optional
            Labels attached to the deployed service on the platform.
        wait : bool
            Also wait for the service health check before returning.

        Optional parameters are left out of the install request when not
        given. The SDK does not validate the required strings; an empty value
        is sent as is.

        Returns
        -------
        AutoRagDeployResult
            ``service_info`` from ACP, ``ready`` as described above, and
            ``autorag`` bound to the new service.

        Raises
        ------
        ProjectNotFoundError
            The project no longer exists on the platform.
        InvalidServiceParametersError
            ACP rejected an install parameter.
        ServiceError
            Any other error answer from the service.
        """
        request = self._build_install_request(
            chat_api_provider=chat_api_provider,
            embedding_api_provider=embedding_api_provider,
            chat_secret_profile_id=chat_secret_profile_id,
            embedding_secret_profile_id=embedding_secret_profile_id,
            chat_model=chat_model,
            embedding_model=embedding_model,
            chat_api_url=chat_api_url,
            embedding_api_url=embedding_api_url,
            labels=labels,
        )
        service_info = self._service_api.deploy_service(
            install_path=AcpPath.GRAPHRAG_RETRIEVER, request=request
        )
        self._refresh()
        autorag = self._create_autorag_for_service(service_info.service_id)
        ready = False
        if not wait:
            ready = None
        elif autorag.wait_until_ready():
            ready = True
        return AutoRagDeployResult(service_info=service_info, ready=ready, autorag=autorag)

    def list(self) -> list[AutoRag]:
        """Refresh the project and return an :class:`AutoRag` per deployed retriever."""
        project = self._refresh()
        project_metadata = project.project_metadata
        services = project_metadata.retriever_services if project_metadata else []
        return [self._create_autorag_for_service(service.service_id) for service in services]

    def get(self, service_id: str) -> AutoRag:
        """Refresh the project and return the :class:`AutoRag` bound to ``service_id``.

        Raises
        ------
        AutoRagNotDeployedError
            No retriever with that id is in the project.
        """
        self._refresh()
        autorag = self._create_autorag_for_service(service_id)
        if not autorag.is_deployed:
            raise AutoRagNotDeployedError(
                f"The project has no retriever with service id {service_id!r}."
            )
        return autorag

    def _create_autorag_for_service(self, service_id: str) -> AutoRag:
        """Create an :class:`AutoRag` for ``service_id``, sharing this manager's wiring."""
        return AutoRag(
            service_api=self._service_api,
            api=self._api,
            project=self._project,
            refresh=self._refresh,
            service_id=service_id,
        )

    def _build_install_request(
        self,
        chat_api_provider: str,
        embedding_api_provider: str,
        chat_secret_profile_id: str,
        embedding_secret_profile_id: str,
        chat_model: str | None,
        embedding_model: str | None,
        chat_api_url: str | None,
        embedding_api_url: str | None,
        labels: Mapping[str, str] | None,
    ) -> CreateEntityRequest:
        """Turn keyword arguments into the ACP install request. Sends nothing.

        The project name and database come from the AiProject snapshot, the
        rest from the arguments; optional arguments are added to the env map
        only when they are not ``None``.
        """
        env: dict[str, str] = {
            AutoRagInstallParams.GENAI_PROJECT_NAME: self._project().project_name,
            AutoRagInstallParams.DB_NAME: self._project().project_db_name,
            AutoRagInstallParams.CHAT_API_PROVIDER: chat_api_provider,
            AutoRagInstallParams.EMBEDDING_API_PROVIDER: embedding_api_provider,
            AutoRagInstallParams.CHAT_SECRET_PROFILE_ID: chat_secret_profile_id,
            AutoRagInstallParams.EMBEDDING_SECRET_PROFILE_ID: embedding_secret_profile_id,
        }
        optional = {
            AutoRagInstallParams.CHAT_MODEL: chat_model,
            AutoRagInstallParams.EMBEDDING_MODEL: embedding_model,
            AutoRagInstallParams.CHAT_API_URL: chat_api_url,
            AutoRagInstallParams.EMBEDDING_API_URL: embedding_api_url,
        }
        env.update({key: value for key, value in optional.items() if value is not None})
        request = CreateEntityRequest(env=env)
        if labels is not None:
            request.labels = dict(labels)
        return request
