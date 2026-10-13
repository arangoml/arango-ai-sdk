"""Unit tests for :class:`ServiceApi`; no platform needed.

``Communication.send_request`` is patched, so the tests check three things:
the request ``ServiceApi`` sends, the ``ServiceError`` it catches, and
the SDK exception it translates that error into.
"""

from unittest.mock import patch

import pytest

from arango_ai_sdk._naming import AcpPath
from arango_ai_sdk.api._service_api import ServiceApi
from arango_ai_sdk.communication import Communication
from arango_ai_sdk.exceptions import (
    InvalidServiceParametersError,
    ProjectNotFoundError,
    ServiceError,
    ServiceNotDeletableError,
    ServiceNotFoundError,
)
from arango_ai_sdk.models import CreateEntityRequest

SEND_REQUEST = "arango_ai_sdk.communication.Communication.send_request"

REQUEST = CreateEntityRequest(env={"genai_project_name": "sales", "db_name": "mydb"})
SERVICE_BODY = {"serviceInfo": {"serviceId": "svc-123", "status": "DEPLOYING"}}


def test_deploy_service_posts_the_request_and_returns_the_service_info(
    placeholder_communication: Communication,
):
    with patch(SEND_REQUEST) as mock_send:
        mock_send.return_value = SERVICE_BODY

        info = ServiceApi(communication=placeholder_communication).deploy_service(
            install_path=AcpPath.AUTOGRAPH, request=REQUEST
        )

    mock_send.assert_called_once_with("post", AcpPath.AUTOGRAPH, data=REQUEST.to_dict())
    assert info.service_id == "svc-123"
    assert info.status == "DEPLOYING"


def test_deploy_service_translates_a_400_into_invalid_service_parameters(
    placeholder_communication: Communication,
):
    with patch(SEND_REQUEST) as mock_send:
        mock_send.side_effect = ServiceError("chat_api_provider is required", status_code=400)

        with pytest.raises(InvalidServiceParametersError) as excinfo:
            ServiceApi(communication=placeholder_communication).deploy_service(
                install_path=AcpPath.AUTOGRAPH, request=REQUEST
            )

    assert excinfo.value.status_code == 400
    assert isinstance(excinfo.value.__cause__, ServiceError)


def test_deploy_service_translates_a_missing_project_into_project_not_found(
    placeholder_communication: Communication,
):
    with patch(SEND_REQUEST) as mock_send:
        # ACP raises ValueError for a missing project, which its gateway sends as
        # a 400 like any other invalid argument, so the message is what tells the
        # two apart. See TODO(AIS-2208) in services.py.
        mock_send.side_effect = ServiceError(
            "Project sales not found in the metadata store under database mydb. "
            "Create the project before installing services. Aborting installation.",
            status_code=400,
        )

        with pytest.raises(ProjectNotFoundError) as excinfo:
            ServiceApi(communication=placeholder_communication).deploy_service(
                install_path=AcpPath.AUTOGRAPH, request=REQUEST
            )

    assert excinfo.value.status_code == 404
    assert isinstance(excinfo.value.__cause__, ServiceError)


def test_deploy_service_reraises_any_other_service_error_unchanged(
    placeholder_communication: Communication,
):
    error = ServiceError("An internal server error occurred", status_code=500)
    with patch(SEND_REQUEST) as mock_send:
        mock_send.side_effect = error

        with pytest.raises(ServiceError) as excinfo:
            ServiceApi(communication=placeholder_communication).deploy_service(
                install_path=AcpPath.AUTOGRAPH, request=REQUEST
            )

    assert excinfo.value is error


def test_delete_sends_the_id_and_returns_the_removed_service_info(
    placeholder_communication: Communication,
):
    with patch(SEND_REQUEST) as mock_send:
        mock_send.return_value = SERVICE_BODY

        info = ServiceApi(communication=placeholder_communication).delete(service_id="svc-123")

    mock_send.assert_called_once_with("delete", f"{AcpPath.SERVICE}/svc-123")
    assert info.service_id == "svc-123"


def test_delete_with_an_empty_id_raises_without_sending(
    placeholder_communication: Communication,
):
    with patch(SEND_REQUEST) as mock_send, pytest.raises(ServiceNotFoundError) as excinfo:
        ServiceApi(communication=placeholder_communication).delete(service_id="")

    mock_send.assert_not_called()
    assert excinfo.value.status_code == 404


def test_delete_translates_a_404_into_service_not_found(
    placeholder_communication: Communication,
):
    with patch(SEND_REQUEST) as mock_send:
        mock_send.side_effect = ServiceError("service no-such-id not found", status_code=404)

        with pytest.raises(ServiceNotFoundError) as excinfo:
            ServiceApi(communication=placeholder_communication).delete(service_id="no-such-id")

    assert excinfo.value.status_code == 404
    assert isinstance(excinfo.value.__cause__, ServiceError)


def test_delete_translates_a_managed_service_into_service_not_deletable(
    placeholder_communication: Communication,
):
    with patch(SEND_REQUEST) as mock_send:
        mock_send.side_effect = ServiceError(
            "Service svc-123 is managed by project 'sales' and cannot be deleted directly",
            status_code=400,
        )

        with pytest.raises(ServiceNotDeletableError) as excinfo:
            ServiceApi(communication=placeholder_communication).delete(service_id="svc-123")

    assert excinfo.value.status_code == 400
    assert isinstance(excinfo.value.__cause__, ServiceError)
