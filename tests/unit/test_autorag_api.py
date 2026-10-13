"""Unit tests for :class:`AutoRagApi`: no platform needed.

``Communication.send_request`` is patched, so the tests check the request
``AutoRagApi`` sends, the model it loads the reply into, and the SDK
exception it translates an error answer into.
"""

from unittest.mock import patch

import pytest

from arango_ai_sdk.communication import Communication
from arango_ai_sdk.exceptions import AutoRagNotDeployedError, ServiceError
from arango_ai_sdk.models import (
    AutoRagHealthCheckResponse,
    GraphRagQueryRequest,
    GraphRagQueryResponse,
    QueryType,
)
from arango_ai_sdk.projects.services.autorag._api import AutoRagApi

SEND_REQUEST = "arango_ai_sdk.communication.Communication.send_request"

SERVICE_PATH = "/graphrag/retriever/r-123"


def test_health_gets_status(placeholder_communication: Communication):
    with patch(SEND_REQUEST) as mock_send:
        mock_send.return_value = {"status": "OK", "message": "ready"}
        api = AutoRagApi(communication=placeholder_communication)

        health = api.health(service_path=SERVICE_PATH)

    mock_send.assert_called_once_with(method="GET", path=f"{SERVICE_PATH}/v1/health")
    assert isinstance(health, AutoRagHealthCheckResponse)
    assert health.status == "OK"
    assert health.message == "ready"


def test_query_posts_request_and_returns_answer(
    placeholder_communication: Communication,
):
    request = GraphRagQueryRequest(
        query="What is the refund policy?",
        query_type=QueryType.UNIFIED,
        show_citations=True,
    )
    with patch(SEND_REQUEST) as mock_send:
        mock_send.return_value = {
            "result": "Refunds are accepted within 30 days.",
            "runId": "run-1",
            "errorCode": "",
        }
        api = AutoRagApi(communication=placeholder_communication)

        response = api.query(service_path=SERVICE_PATH, request=request)

    mock_send.assert_called_once_with(
        "post", f"{SERVICE_PATH}/v1/graphrag-query", data=request.to_dict()
    )
    sent = mock_send.call_args.kwargs["data"]
    assert sent["query"] == "What is the refund policy?"
    assert sent["queryType"] == "UNIFIED"
    assert sent["showCitations"] is True
    assert isinstance(response, GraphRagQueryResponse)
    assert response.result == "Refunds are accepted within 30 days."
    assert response.run_id == "run-1"
    assert response.error_code == ""


def test_query_returns_failed_answer_with_its_code(
    placeholder_communication: Communication,
):
    """A ``200`` with a non-empty ``error_code`` is a transport success.

    The API layer hands it back untouched; ``AutoRag.ask`` raises on it.
    """
    with patch(SEND_REQUEST) as mock_send:
        mock_send.return_value = {
            "result": "",
            "runId": "run-2",
            "errorCode": "INSUFFICIENT_QUOTA",
        }
        api = AutoRagApi(communication=placeholder_communication)

        response = api.query(
            service_path=SERVICE_PATH, request=GraphRagQueryRequest(query="anything")
        )

    assert response.error_code == "INSUFFICIENT_QUOTA"
    assert response.run_id == "run-2"
    assert response.result == ""


def test_query_maps_404_to_not_deployed(placeholder_communication: Communication):
    with patch(SEND_REQUEST) as mock_send:
        mock_send.side_effect = ServiceError("Not Found", status_code=404)
        api = AutoRagApi(communication=placeholder_communication)

        with pytest.raises(AutoRagNotDeployedError) as exc_info:
            api.query(
                service_path=SERVICE_PATH,
                request=GraphRagQueryRequest(query="anything"),
            )

    assert exc_info.value.status_code == 404


def test_query_passes_other_errors_through(placeholder_communication: Communication):
    original = ServiceError("query must not be empty", status_code=400)
    with patch(SEND_REQUEST) as mock_send:
        mock_send.side_effect = original
        api = AutoRagApi(communication=placeholder_communication)

        with pytest.raises(ServiceError) as exc_info:
            api.query(
                service_path=SERVICE_PATH,
                request=GraphRagQueryRequest(query="anything"),
            )

    assert exc_info.value is original
