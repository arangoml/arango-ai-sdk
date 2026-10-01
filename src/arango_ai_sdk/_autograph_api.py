"""Endpoints of one project's AutoGraph service: start a job, read its status.

An internal layer, not a user-facing namespace. ``AutoGraph`` builds the
requests and decides when to wait, this module sends them through
``Communication`` and maps the service's error answers to SDK exceptions.

AutoGraph appends ``[Error: <ClassName>, HTTP: <code>]`` to every error
message, so conditions are told apart by class name, not by status code.
"""

import re
from collections.abc import Mapping
from typing import Any

import betterproto

from arango_ai_sdk._naming import AutoGraphPath
from arango_ai_sdk.communication import Communication
from arango_ai_sdk.exceptions import (
    AutoGraphBusyError,
    CategoryAlreadyBuiltError,
    ModelConfigNotReadyError,
    NoStrategiesError,
    ServiceError,
)
from arango_ai_sdk.models import (
    CreateCorpusBuildRequest,
    CreateCorpusBuildResponse,
    GetBuildStatusResponse,
    GetOrchestrationStatusResponse,
    GetRagStrategizerJobStatusResponse,
    GetRagStrategizerStrategyResponse,
    HealthCheckResponse,
    TriggerOrchestrationRequest,
    TriggerOrchestrationResponse,
    TriggerRagStrategizerRequest,
    TriggerRagStrategizerResponse,
)

__all__ = ["AutoGraphApi"]

_ERROR_SUFFIX = re.compile(r"\[Error: (?P<error_class>\w+), HTTP: \d+\]")


class AutoGraphApi:
    """Send requests to one project's AutoGraph service.

    Parameters
    ----------
    communication : Communication
        Shared transport. This class calls ``send_request`` and nothing else.

    Every method takes ``service_path``, the gateway path of the service
    (``AutoGraph.service_path``), and appends its endpoint to it. It is an
    argument rather than state because the path is only known once the
    service is deployed, and the object outlives deploy and undeploy.
    """

    def __init__(self, communication: Communication) -> None:
        self._communication = communication

    def health(self, service_path: str) -> HealthCheckResponse:
        """GET the service health; ``status`` is ``"SERVING"`` when the pod is up.

        Raises
        ------
        ServiceError
            Any error answer from the service, a ``404`` while the route is
            still coming up included. The caller decides what that means.
        """
        body = self._communication.send_request(
            method="GET",
            path=f"{service_path}/{AutoGraphPath.HEALTH}",
        )
        return _response_from_body(HealthCheckResponse(), body)

    def start_corpus_build(
        self, service_path: str, request: CreateCorpusBuildRequest
    ) -> CreateCorpusBuildResponse:
        """POST a corpus build and return its id.

        Raises
        ------
        ModelConfigNotReadyError
            The service reports its model configuration invalid.
        AutoGraphBusyError
            Another build, strategizer run, orchestration or delete holds the slot.
        CategoryAlreadyBuiltError
            A requested category is already built. Pass ``incremental=True`` to add to it.
        ServiceError
            Any other error answer from the service.
        """
        try:
            body = self._communication.send_request(
                "post",
                f"{service_path}/{AutoGraphPath.CORPUS_BUILDS}",
                data=request.to_dict(),
            )
        except ServiceError as exc:
            translated = _translate_error(exc)
            if translated is None or translated is exc:
                raise
            raise translated from exc
        return _response_from_body(CreateCorpusBuildResponse(), body)

    def get_corpus_build_status(self, service_path: str, build_id: str) -> GetBuildStatusResponse:
        """GET the status of one corpus build.

        Raises
        ------
        ServiceError
            Any error answer from the service, a ``404`` included. The caller
            decides whether a ``404`` means the record was dropped.
        """
        body = self._communication.send_request(
            "get", f"{service_path}/{AutoGraphPath.CORPUS_BUILDS}/{build_id}"
        )
        return _response_from_body(GetBuildStatusResponse(), body)

    def start_strategizer(
        self, service_path: str, request: TriggerRagStrategizerRequest
    ) -> TriggerRagStrategizerResponse:
        """POST a strategizer analysis and return its job id.

        Raises
        ------
        ModelConfigNotReadyError
            The service reports its model configuration invalid.
        AutoGraphBusyError
            Another build, strategizer run, orchestration or delete holds the slot.
        ServiceError
            Any other error answer from the service.
        """
        try:
            body = self._communication.send_request(
                "post",
                f"{service_path}/{AutoGraphPath.STRATEGIZER_ANALYZE}",
                data=request.to_dict(),
            )
        except ServiceError as exc:
            translated = _translate_error(exc)
            if translated is None or translated is exc:
                raise
            raise translated from exc
        return _response_from_body(TriggerRagStrategizerResponse(), body)

    def get_strategizer_job_status(
        self, service_path: str, job_id: str
    ) -> GetRagStrategizerJobStatusResponse:
        """GET the status of one strategizer job. Same errors as :meth:`get_corpus_build_status`."""
        body = self._communication.send_request(
            "get", f"{service_path}/{AutoGraphPath.STRATEGIZER_JOBS}/{job_id}"
        )
        return _response_from_body(GetRagStrategizerJobStatusResponse(), body)

    def get_strategies(self, service_path: str) -> GetRagStrategizerStrategyResponse:
        """GET the strategy the strategizer chose per cluster."""
        body = self._communication.send_request(
            "get", f"{service_path}/{AutoGraphPath.STRATEGIZER_STRATEGY}"
        )
        return _response_from_body(GetRagStrategizerStrategyResponse(), body)

    def start_orchestration(
        self, service_path: str, request: TriggerOrchestrationRequest
    ) -> TriggerOrchestrationResponse | None:
        """POST an orchestration and return its id, or ``None`` when nothing is stale.

        Raises
        ------
        ModelConfigNotReadyError
            The service reports its model configuration invalid.
        AutoGraphBusyError
            Another build, strategizer run, orchestration or delete holds the slot.
        NoStrategiesError
            The categories have no strategy profiles; run the strategizer first.
        ServiceError
            Any other error answer from the service.
        """
        try:
            body = self._communication.send_request(
                "post",
                f"{service_path}/{AutoGraphPath.ORCHESTRATE}",
                data=request.to_dict(),
            )
        except ServiceError as exc:
            translated = _translate_error(exc)
            if translated is None:
                return None
            if translated is exc:
                raise
            raise translated from exc
        return _response_from_body(TriggerOrchestrationResponse(), body)

    def get_orchestration_status(
        self, service_path: str, orchestration_id: str
    ) -> GetOrchestrationStatusResponse:
        """GET the status of one orchestration. Same errors as :meth:`get_corpus_build_status`."""
        body = self._communication.send_request(
            "get", f"{service_path}/{AutoGraphPath.ORCHESTRATE}/{orchestration_id}"
        )
        return _response_from_body(GetOrchestrationStatusResponse(), body)


def _response_from_body[ResponseT: betterproto.Message](
    response: ResponseT, body: Any
) -> ResponseT:
    """Load a service reply into the generated model the caller is promised.

    ``Communication.send_request`` returns the parsed JSON body and nothing
    else, so every method above has to load it into its own model before
    handing it back. AutoGraph answers in camelCase, which ``from_dict``
    reads. A body that is not a JSON object leaves ``response`` empty rather
    than raising, so a reply the service should not have sent surfaces as an
    unset field, not as a ``TypeError`` from inside the SDK.

    Parameters
    ----------
    response : betterproto.Message
        An empty instance of the model to fill.
    body : Any
        The deserialised response body.

    Returns
    -------
    betterproto.Message
        ``response``, filled in place.
    """
    if isinstance(body, Mapping):
        # `from_dict` fills the instance in place and returns it. It is a
        # betterproto `hybridmethod` descriptor that ty cannot type, hence the
        # ignore. Same pattern as `project_from_body` in _project_api.py.
        response.from_dict(body)  # ty: ignore[invalid-attribute-access]
    return response


def _translate_error(exc: ServiceError) -> ServiceError | None:
    """Return the SDK exception for an AutoGraph error answer.

    Reads the ``[Error: <ClassName>, HTTP: <code>]`` suffix of the message
    and picks the exception by class name. Returns ``exc`` itself when no
    named condition matches, so the caller can ``raise`` the result either way.
    Returns ``None`` when orchestration was asked to run and nothing is stale.
    """
    match = _ERROR_SUFFIX.search(str(exc))
    if match is None:
        return exc
    error_class = match.group("error_class")
    kwargs = {"status_code": exc.status_code, "error_code": exc.error_code}
    # The model config gate raises the generic InvalidRequestError, so the
    # message is the only thing telling it apart from other bad requests.
    if error_class == "InvalidRequestError" and "model configuration" in str(exc).lower():
        return ModelConfigNotReadyError(str(exc), **kwargs)
    if error_class.endswith("InProgressError"):
        return AutoGraphBusyError(str(exc), **kwargs)
    if error_class == "NoStrategyProfilesError":
        return NoStrategiesError(str(exc), **kwargs)
    if error_class == "RebuildNotAllowedError":
        return CategoryAlreadyBuiltError(str(exc), **kwargs)
    if error_class == "NothingToOrchestrateError":
        return None
    return exc
