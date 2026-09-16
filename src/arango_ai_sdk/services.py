"""ACP service endpoints: install a service and delete one by id.

An internal layer, not a user-facing namespace. Service objects such as
``AutoGraph`` build the install request and hand it to ``deploy_service``;
this module sends it and maps ACP's error answers to SDK exceptions.
"""

from collections.abc import Mapping
from typing import Any

from arango_ai_sdk._naming import AcpPath
from arango_ai_sdk.communication import Communication
from arango_ai_sdk.exceptions import (
    InvalidServiceParametersError,
    ProjectNotFoundError,
    ServiceError,
    ServiceNotDeletableError,
    ServiceNotFoundError,
)
from arango_ai_sdk.models import CreateEntityRequest, ServiceInfo

__all__ = ["ServiceManager"]


class ServiceManager:
    """Manage services through the communication layer.

    Parameters
    ----------
    communication : Communication
        Shared transport. This class calls ``send_request`` and nothing else.
    """

    def __init__(self, communication: Communication) -> None:
        self._communication = communication

    def deploy_service(self, install_path: str, request: CreateEntityRequest) -> ServiceInfo:
        """Post a ready install request to ACP and return the service info.

        Parameters
        ----------
        install_path : str
            ACP install endpoint for the service kind, e.g. ``AcpPath.AUTOGRAPH``.
        request : CreateEntityRequest
            Install parameters, already built by the caller. The env map must
            name the project and database the service belongs to.

        Returns
        -------
        ServiceInfo
            ``service_id`` is what :meth:`delete` takes.

        Raises
        ------
        ProjectNotFoundError
            ACP has no project with the name given in the request.
        InvalidServiceParametersError
            ACP rejected an install parameter.
        ServiceError
            Any other error answer from the service.
        """
        try:
            body = self._communication.send_request("post", install_path, data=request.to_dict())
        except ServiceError as exc:
            # TODO(AIS-2208): ACP does not send a dedicated error code for a missing
            # project on install, so this matches on the message text. Replace with
            # the error code once the ticket is resolved.
            message = str(exc).lower()
            if "project" in message and ("not found in the metadata store" in message):
                raise ProjectNotFoundError(
                    str(exc),
                    status_code=404,
                    error_code=exc.error_code,
                ) from exc
            if exc.status_code == 400:
                raise InvalidServiceParametersError(
                    str(exc),
                    status_code=exc.status_code,
                    error_code=exc.error_code,
                ) from exc
            raise
        return _service_info_from_body(body)

    def delete(self, service_id: str) -> ServiceInfo:
        """Stop and remove a platform service by id.

        Parameters
        ----------
        service_id : str
            Id returned by :meth:`deploy_service`.

        Returns
        -------
        ServiceInfo
            The removed service, as ACP described it.

        Raises
        ------
        ServiceNotFoundError
            ``service_id`` is empty, or ACP has no service with that id.
        ServiceNotDeletableError
            ACP will not delete a service managed by another entity.
        ServiceError
            Any other error answer from the service.
        """
        if not service_id:
            raise ServiceNotFoundError(
                "No service with this ID exists.",
                status_code=404,
            )
        try:
            body = self._communication.send_request("delete", f"{AcpPath.SERVICE}/{service_id}")
        except ServiceError as exc:
            message = str(exc).lower()
            if exc.status_code == 404 or "not found" in message:
                raise ServiceNotFoundError(
                    str(exc),
                    status_code=exc.status_code,
                    error_code=exc.error_code,
                ) from exc
            if "is managed by" in message or "can be deleted via this endpoint" in message:
                raise ServiceNotDeletableError(
                    str(exc),
                    status_code=exc.status_code,
                    error_code=exc.error_code,
                ) from exc
            raise
        return _service_info_from_body(body)


def _service_info_from_body(body: Any) -> ServiceInfo:
    """Load :class:`ServiceInfo` from a create or delete JSON body.

    ACP nests the record under ``serviceInfo``. An empty body is an empty
    ``ServiceInfo``.
    """
    info = ServiceInfo()
    if not isinstance(body, Mapping):
        return info
    raw = body.get("serviceInfo")
    payload: Mapping[str, Any] = raw if isinstance(raw, Mapping) else body
    info.from_dict(payload)  # ty: ignore[invalid-attribute-access]
    return info
