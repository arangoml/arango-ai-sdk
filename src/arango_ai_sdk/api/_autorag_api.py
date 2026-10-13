"""Endpoints of one project's retriever service: health and the unary query.

An internal layer, not a user-facing namespace. ``AutoRag`` builds the
request and reads the answer, this module sends it through ``Communication``
and maps the service's error answers to SDK exceptions.

The retriever appends no ``[Error: <Class>, HTTP: <code>]`` suffix to its
messages, so conditions are told apart by status code and message text.
"""

from arango_ai_sdk._naming import AutoRagPath
from arango_ai_sdk.api._autograph_api import _response_from_body
from arango_ai_sdk.communication import Communication
from arango_ai_sdk.exceptions import AutoRagNotDeployedError, ServiceError
from arango_ai_sdk.models import (
    AutoRagHealthCheckResponse,
    GraphRagQueryRequest,
    GraphRagQueryResponse,
)

__all__ = ["AutoRagApi"]


class AutoRagApi:
    """Send requests to one project's retriever service.

    Parameters
    ----------
    communication : Communication
        Shared transport. This class calls ``send_request`` and nothing else.

    Every method takes ``service_path``, the gateway path of the service
    (``AutoRag.service_path``), and appends its endpoint to it. It is an
    argument rather than state because one object serves every retriever of
    the project, each with its own path.
    """

    def __init__(self, communication: Communication) -> None:
        self._communication = communication

    def health(self, service_path: str) -> AutoRagHealthCheckResponse:
        """GET the service health; ``status`` is ``"OK"`` when the pod is up.

        Raises
        ------
        ServiceError
            Any error answer from the service, a ``404`` while the route is
            still coming up included. The caller decides what that means.
        """
        body = self._communication.send_request(
            method="GET",
            path=f"{service_path}/{AutoRagPath.HEALTH}",
        )
        return _response_from_body(AutoRagHealthCheckResponse(), body)

    def query(self, service_path: str, request: GraphRagQueryRequest) -> GraphRagQueryResponse:
        """POST a query and return the answer.

        A ``200`` whose body carries a non-empty ``error_code`` is returned as
        is; ``AutoRag.ask`` turns it into :class:`QueryFailedError`, so this
        layer stays a plain transport.

        Raises
        ------
        AutoRagNotDeployedError
            The service path answers ``404``: the retriever is gone.
        ServiceError
            Any other error answer from the service.
        """
        try:
            body = self._communication.send_request(
                "post",
                f"{service_path}/{AutoRagPath.QUERY}",
                data=request.to_dict(),
            )
        except ServiceError as exc:
            if exc.status_code == 404:
                raise AutoRagNotDeployedError(
                    str(exc), status_code=exc.status_code, error_code=exc.error_code
                ) from exc
            raise
        return _response_from_body(GraphRagQueryResponse(), body)
