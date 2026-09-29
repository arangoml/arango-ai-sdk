"""The AutoGraph service of one project.

Reached as ``autograph`` on an ``AiProjectHandle``. A project has exactly one
AutoGraph service, so this object is created once per handle and ``deploy``
refuses to install a second one. Pipeline steps such as corpus build are added
here as methods.

The object never touches the transport. It builds the install request and
hands it to ``ServiceApi``, and it reads deployment state from the
``AiProject`` snapshot the handle refreshes on request.
"""

import time
from collections.abc import Callable, Mapping, Sequence
from enum import StrEnum
from typing import cast
from urllib.parse import urlsplit

import betterproto

from arango_ai_sdk._autograph_api import AutoGraphApi
from arango_ai_sdk._naming import AcpPath, AutoGraphInstallParams
from arango_ai_sdk._service_api import ServiceApi
from arango_ai_sdk.exceptions import (
    AutoGraphAlreadyDeployedError,
    AutoGraphNotDeployedError,
    CommunicationError,
)
from arango_ai_sdk.models import (
    AiProject,
    AutoGraphService,
    CreateEntityRequest,
    GetBuildStatusResponse,
    HealthCheckResponse,
    ServiceInfo,
)

__all__ = ["AutoGraph", "DeployResult", "HealthState", "JobState"]

DEFAULT_READY_TIMEOUT = 300.0


class HealthState(StrEnum):
    """Values of ``status`` in the AutoGraph health check response."""

    SERVING = "SERVING"
    NOT_SERVING = "NOT_SERVING"


class JobState(StrEnum):
    """Job states AutoGraph reports in the ``status`` field of its three job GETs.

    Plain strings in ``corpus_graph.proto``, so no enum is generated for them.
    ``COMPLETED``, ``FAILED`` and ``CANCELLED`` are terminal. ``CANCELLED``
    only occurs on orchestration.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DeployResult:
    """What ``AutoGraph.deploy`` returns: the service record and whether it is ready.

    Attributes
    ----------
    service_info : ServiceInfo
        The service as ACP described it right after accepting the install.
    ready : bool or None
        ``True`` when ``deploy(wait=True)`` saw the health check answer
        ``SERVING`` within the bound, ``False`` when the bound passed first,
        ``None`` when nobody waited (``wait=False``). Unless ``True``, the
        service is installed and may still be coming up, call
        ``wait_until_ready`` to check again.
    """

    def __init__(self, service_info: ServiceInfo, ready: bool | None) -> None:
        self.service_info = service_info
        self.ready = ready


class AutoGraph:
    """The single AutoGraph service of a project.

    Parameters
    ----------
    service_api : ServiceApi
        Sends install and delete requests to ACP.
    api : AutoGraphApi
        Sends job requests to the AutoGraph service itself.
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
        service_api: ServiceApi,
        api: AutoGraphApi,
        project: Callable[[], AiProject],
        refresh: Callable[[], AiProject],
    ) -> None:
        self._service_api = service_api
        self._api = api
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

    @property
    def service_path(self) -> str | None:
        """Return the gateway path of the deployed service, or ``None``.

        ``service_url`` minus scheme and host, without a trailing slash, so job
        endpoints can be appended to it.
        """
        url = self.service_url
        if not url:
            return None
        return urlsplit(url).path.rstrip("/")

    def _deployed_service(self) -> AutoGraphService | None:
        """Return ``project_metadata.autograph_service`` from the snapshot, or ``None``."""
        project_metadata = self._project().project_metadata
        return project_metadata.autograph_service if project_metadata else None

    def corpus_build(
        self,
        categories: Sequence[str],
        *,
        incremental: bool = False,
        top_k: int | None = None,
        cluster_threshold: int | None = None,
        timeout: float | None = None,
        poll_interval: float = 30.0,
        on_progress: Callable[[GetBuildStatusResponse], None] | None = None,
    ) -> GetBuildStatusResponse:
        """Build the corpus graph for the given categories and wait for it to finish.

        Starts the build, polls its status until it is terminal and returns the
        final status. A build that completes with a non-empty ``error_code`` is
        a partial success: it is returned, not raised, and a warning is logged.

        Parameters
        ----------
        categories : Sequence[str]
            Bare category labels, the second label of the scope the files were
            uploaded with. Required; an empty list is rejected.
        incremental : bool
            Keep the existing corpus and only add or update the given categories.
        top_k : int, optional
            Similar documents linked per document. Service default 7.
        cluster_threshold : int, optional
            Minimum cluster size, 1 or 2. Service default 2.
        timeout : float, optional
            Deadline in seconds for the whole build. ``None`` waits without bound.
        poll_interval : float
            Seconds between two status polls.
        on_progress : callable, optional
            Called with each polled :class:`GetBuildStatusResponse`.

        Raises
        ------
        AutoGraphNotDeployedError
            The project has no AutoGraph service.
        ModelConfigNotReadyError
            The service reports its model configuration invalid.
        AutoGraphBusyError
            Another build, strategizer run, orchestration or delete is in progress.
        IngestionFailedError
            The build ended as failed; carries the final status.
        JobStatusLostError
            The service dropped the build's status record while polling.
        JobTimeoutError
            ``timeout`` expired before the build finished.
        ServiceError
            Any other error answer from the service.
        """
        raise NotImplementedError

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
        wait: bool = False,
    ) -> DeployResult:
        """Install AutoGraph for this project and return the deploy result.

        Steps: refresh the project, raise if it already has an AutoGraph
        service, build the install request, send it through
        ``ServiceApi.deploy_service`` to ``AcpPath.AUTOGRAPH``, refresh again.
        ACP answers once Helm accepts the install, before the pod is up. With
        ``wait=True`` the call then runs :meth:`wait_until_ready` with its
        defaults and reports the outcome in ``ready``; a slow start never fails
        the deploy.

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
        fps_recovery_username : str
            ArangoDB user AutoGraph uses to resume File Parser work after a pod
            restart. Must have read and write access to the project database.
            The SDK does not create this user.
        chat_model : str, optional
            Chat model name, for example ``"gpt-4o"``.
        embedding_model : str, optional
            Embedding model name, for example ``"text-embedding-3-small"``.
        chat_api_url : str, optional
            Override for the chat provider's endpoint.
        embedding_api_url : str, optional
            Override for the embedding provider's endpoint.
        multimodal_model : str, optional
            Multimodal model name, when documents contain images.
        labels : Mapping[str, str], optional
            Labels attached to the deployed service on the platform.
        wait : bool
            Also wait for the service health check before returning.

        Optional parameters are left out of the install request when not
        given. The SDK does not validate the required strings; an empty value
        is sent as is.

        Returns
        -------
        DeployResult
            ``service_info`` from ACP and ``ready``: ``None`` without ``wait``,
            otherwise whether the service became ``SERVING`` within the bound.

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
        service_info = self._service_api.deploy_service(
            install_path=AcpPath.AUTOGRAPH, request=request
        )
        self._refresh()
        ready = False
        if not wait:
            ready = None
        elif self.wait_until_ready():
            ready = True
        return DeployResult(service_info=service_info, ready=ready)

    def wait_until_ready(
        self,
        *,
        timeout: float = DEFAULT_READY_TIMEOUT,
        poll_interval: float = 5.0,
    ) -> bool:
        """Block until the deployed AutoGraph service answers its health check.

        Polls ``GET /v1/health`` until ``status`` is ``SERVING``. A failed
        request while the route or the pod is still coming up counts as not
        ready, not as an error.

        Parameters
        ----------
        timeout : float
            Seconds to wait before giving up.
        poll_interval : float
            Seconds between two health checks.

        Returns
        -------
        bool
            ``True`` once the service is ``SERVING``, ``False`` when ``timeout``
            passed first.

        Raises
        ------
        AutoGraphNotDeployedError
            The project has no AutoGraph service.
        """
        self._refresh()
        if not self.is_deployed:
            raise AutoGraphNotDeployedError("The project has no AutoGraph service.")
        # ACP writes the service URL together with the service record, so a
        # deployed service always has a path; the cast only informs the type checker.
        service_path = cast(str, self.service_path)
        deadline = time.monotonic() + timeout
        while True:
            try:
                health: HealthCheckResponse | None = self._api.health(service_path=service_path)
            except CommunicationError:
                # The route or the pod is still coming up.
                health = None
            if health is not None and health.status == HealthState.SERVING:
                return True
            if time.monotonic() >= deadline:
                return False
            time.sleep(poll_interval)

    def undeploy(self) -> ServiceInfo:
        """Stop and remove this project's AutoGraph service.

        Steps: refresh the project, raise if it has no AutoGraph service, send
        ``ServiceApi.delete`` with the id from the metadata, refresh again.

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
        service_info = self._service_api.delete(service_id=self.service_id)
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


MAX_CONSECUTIVE_POLL_ERRORS = 3


def _wait_for_job(
    fetch_status: Callable[[], betterproto.Message],
    *,
    job_id: str,
    timeout: float | None,
    poll_interval: float,
    on_progress: Callable[[betterproto.Message], None] | None = None,
) -> betterproto.Message:
    """Poll ``fetch_status`` until the job is terminal and return the final status.

    Shared by build, strategize and orchestrate; each passes its own GET as
    ``fetch_status`` and casts the result back to its response type. The three
    response types all carry the state in a ``status`` string field.

    Parameters
    ----------
    fetch_status : callable returning the job's status message
        One GET of the job's status endpoint.
    job_id : str
        The id the job was started with; named in the exceptions.
    timeout : float, optional
        Deadline in seconds for the whole wait. ``None`` waits without bound.
    poll_interval : float
        Seconds between two polls.
    on_progress : callable, optional
        Called once per poll with the status message just fetched.

    Raises
    ------
    IngestionFailedError
        The job reached ``failed`` or ``cancelled``; carries the status message.
    JobStatusLostError
        The service answered ``404`` for an id it had answered before.
    JobTimeoutError
        ``timeout`` expired before a terminal state.
    ServiceError
        ``MAX_CONSECUTIVE_POLL_ERRORS`` polls in a row failed.
    """
    raise NotImplementedError
