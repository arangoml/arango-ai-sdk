"""One retriever service of a project, the object ``AutoRagManager`` hands out.

An ``AutoRag`` is bound to one service id for its lifetime. It asks the
retriever questions, waits for it to come up and removes it. It never touches
the transport: it builds the query and hands it to ``AutoRagApi``, and it
reads deployment state from the ``AiProject`` snapshot the handle refreshes
on request, so a retriever removed elsewhere reads as gone here.
"""

import time
from collections.abc import Callable, Sequence
from enum import StrEnum
from typing import cast
from urllib.parse import urlsplit

from arango_ai_sdk._autorag_api import AutoRagApi
from arango_ai_sdk._service_api import ServiceApi
from arango_ai_sdk.autograph import DEFAULT_READY_TIMEOUT
from arango_ai_sdk.exceptions import (
    AutoRagNotDeployedError,
    CommunicationError,
    QueryFailedError,
)
from arango_ai_sdk.models import (
    AiProject,
    AiService,
    AutoRagHealthCheckResponse,
    GraphRagQueryRequest,
    GraphRagQueryResponse,
    QueryType,
    ServiceInfo,
)

__all__ = [
    "AutoRag",
    "AutoRagHealthState",
]


class AutoRagHealthState(StrEnum):
    """Values of ``status`` in the retriever health check response."""

    OK = "OK"
    FAIL = "FAIL"


class AutoRag:
    """One deployed retriever of a project, bound to its service id.

    Obtained from ``AutoRagManager``, never constructed by users. The id is
    fixed for the object's lifetime, every other state property is read from
    the project snapshot and reflects a refresh.

    Parameters
    ----------
    service_api : ServiceApi
        Sends the delete request to ACP.
    api : AutoRagApi
        Sends health and query requests to the retriever itself.
    project : callable returning AiProject
        Returns the current project snapshot.
    refresh : callable returning AiProject
        Reloads the project from the platform and returns the new snapshot.
    service_id : str
        Id of the retriever this object is bound to.
    """

    def __init__(
        self,
        service_api: ServiceApi,
        api: AutoRagApi,
        project: Callable[[], AiProject],
        refresh: Callable[[], AiProject],
        service_id: str,
    ) -> None:
        self._service_api = service_api
        self._api = api
        self._project = project
        self._refresh = refresh
        self._service_id = service_id

    def __repr__(self) -> str:
        """Return a short representation naming the service id."""
        return f"{type(self).__name__}(service_id={self._service_id!r})"

    @property
    def service_id(self) -> str:
        """Return the id of the retriever this object is bound to."""
        return self._service_id

    @property
    def is_deployed(self) -> bool:
        """Return whether the last project snapshot still lists this retriever."""
        return self._deployed_service() is not None

    @property
    def service_url(self) -> str | None:
        """Return the retriever's URL, or ``None`` when it is no longer deployed."""
        service = self._deployed_service()
        return service.service_url if service is not None else None

    @property
    def service_path(self) -> str | None:
        """Return the gateway path of the retriever, or ``None``.

        ``service_url`` minus scheme and host, without a trailing slash, so
        endpoints can be appended to it.
        """
        url = self.service_url
        if not url:
            return None
        return urlsplit(url).path.rstrip("/")

    def _deployed_service(self) -> AiService | None:
        """Return this retriever's entry in ``retriever_services``, or ``None``."""
        return _find_retriever_service_by_id(self._project(), self._service_id)

    def ask(
        self,
        query: str,
        *,
        query_type: QueryType = QueryType.UNIFIED,
        response_instructions: str | None = None,
        include_metadata: bool = False,
        partition_ids: Sequence[str] | None = None,
        show_citations: bool | None = None,
        model: str | None = None,
    ) -> GraphRagQueryResponse:
        """Ask the retriever a question and return its answer.

        Parameters
        ----------
        query : str
            The question, in natural language. Required, an empty string is rejected.
        query_type : QueryType
            How the retriever searches. Default ``UNIFIED``, which works on
            both VectorRAG and Full GraphRAG partitions.
        response_instructions : str, optional
            Style instructions for the answer, such as ``"Short answer"``.
        include_metadata : bool
            Whether to include retrieval metadata in the response.
        partition_ids : Sequence[str], optional
            Restrict retrieval to these partitions. When omitted the service
            selects the relevant partitions itself.
        show_citations : bool, optional
            Whether to keep inline citations in the answer. Omitted means the
            service default.
        model : str, optional
            Chat model to use for this query only, instead of the deploy-time
            default.

        Returns
        -------
        GraphRagQueryResponse
            ``result`` holds the answer, ``run_id`` the persisted query run.

        Raises
        ------
        ValueError
            ``query`` is empty; nothing is sent.
        AutoRagNotDeployedError
            The retriever is no longer in the project.
        QueryFailedError
            The service answered with a failure code instead of a result.
        ServiceError
            Any other error answer from the service.
        """
        if not query.strip():
            raise ValueError("query must not be empty.")
        self._refresh()
        if not self.is_deployed:
            raise AutoRagNotDeployedError(
                _RETRIEVER_NOT_DEPLOYED_MESSAGE.format(service_id=self._service_id)
            )
        service_path = cast(str, self.service_path)
        request = GraphRagQueryRequest(
            query=query,
            query_type=query_type,
            include_metadata=include_metadata,
        )
        if response_instructions is not None:
            request.response_instructions = response_instructions
        if partition_ids is not None:
            request.partition_ids = list(partition_ids)
        if show_citations is not None:
            request.show_citations = show_citations
        if model is not None:
            request.model = model
        response = self._api.query(service_path=service_path, request=request)
        if response.error_code:
            raise QueryFailedError(
                f"The retriever could not answer the query ({response.error_code}): "
                f"{response.result}",
                failure_code=response.error_code,
                run_id=response.run_id,
                status_code=200,
            )
        return response

    def wait_until_ready(
        self,
        *,
        timeout: float = DEFAULT_READY_TIMEOUT,
        poll_interval: float = 5.0,
    ) -> bool:
        """Block until the retriever answers its health check with ``OK``.

        A failed request while the route or the pod is still coming up counts
        as not ready, not as an error.
        For the sake of convenience, this method is dedicated to AutoRag retrievers,
        and not shared with other types of services.

        Parameters
        ----------
        timeout : float
            Seconds to wait before giving up.
        poll_interval : float
            Seconds between two health checks.

        Returns
        -------
        bool
            ``True`` once the service is ``OK``, ``False`` when ``timeout``
            passed first.

        Raises
        ------
        AutoRagNotDeployedError
            The retriever is no longer in the project.
        """
        self._refresh()
        if not self.is_deployed:
            raise AutoRagNotDeployedError(
                _RETRIEVER_NOT_DEPLOYED_MESSAGE.format(service_id=self._service_id)
            )
        # ACP writes the service URL together with the service record, so a
        # deployed service always has a path; the cast only informs the type checker.
        service_path = cast(str, self.service_path)
        deadline = time.monotonic() + timeout
        while True:
            try:
                health: AutoRagHealthCheckResponse | None = self._api.health(
                    service_path=service_path
                )
            except CommunicationError:
                # The route or the pod is still coming up.
                health = None
            if health is not None and health.status == AutoRagHealthState.OK:
                return True
            if time.monotonic() >= deadline:
                return False
            time.sleep(poll_interval)

    def undeploy(self) -> ServiceInfo:
        """Stop and remove this retriever.

        Steps: refresh the project, raise if the retriever is gone, send
        ``ServiceApi.delete`` with the bound id, refresh again.

        Raises
        ------
        AutoRagNotDeployedError
            The retriever is no longer in the project.
        ServiceNotFoundError
            ACP no longer knows the service id the project metadata holds.
        ServiceError
            Any other error answer from the service.
        """
        self._refresh()
        if not self.is_deployed:
            raise AutoRagNotDeployedError(
                _RETRIEVER_NOT_DEPLOYED_MESSAGE.format(service_id=self._service_id)
            )
        service_info = self._service_api.delete(service_id=self._service_id)
        self._refresh()
        return service_info


_RETRIEVER_NOT_DEPLOYED_MESSAGE = "The project has no retriever with service id {service_id!r}."


def _retriever_services_of_project(project: AiProject) -> list[AiService]:
    """Return ``project_metadata.retriever_services`` from the snapshot, or an empty list."""
    project_metadata = project.project_metadata
    return list(project_metadata.retriever_services) if project_metadata else []


def _find_retriever_service_by_id(project: AiProject, service_id: str) -> AiService | None:
    """Return the retriever entry with ``service_id``, or ``None`` when none has it."""
    for service in _retriever_services_of_project(project):
        if service.service_id == service_id:
            return service
    return None
