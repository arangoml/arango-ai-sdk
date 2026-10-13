"""Unit tests for :class:`AutoRag`; no platform needed.

``AiProjectHandle.refresh`` stands in for the platform's view of the project,
``ServiceApi`` for ACP's answers and ``AutoRagApi`` for the retriever's, so
the tests check what the bound object decides and sends, not what the
platform does. Objects are obtained through ``AutoRagManager.get``, as users
get them. The fixture project carries two retrievers so the object has to
pick its own entry.
"""

from unittest.mock import patch

import pytest

from arango_ai_sdk.communication import Communication
from arango_ai_sdk.exceptions import (
    AutoRagNotDeployedError,
    QueryFailedError,
    ServiceNotFoundError,
)
from arango_ai_sdk.managers.project_handle import AiProjectHandle
from arango_ai_sdk.models import (
    AiProject,
    AiService,
    AutoRagHealthCheckResponse,
    GraphRagProjectMetaData,
    GraphRagQueryRequest,
    GraphRagQueryResponse,
    QueryType,
    ServiceInfo,
)

GET_PROJECT = "arango_ai_sdk.managers.project_handle.get_project"
DELETE = "arango_ai_sdk.api._service_api.ServiceApi.delete"
HEALTH = "arango_ai_sdk.api._autorag_api.AutoRagApi.health"
QUERY = "arango_ai_sdk.api._autorag_api.AutoRagApi.query"
SLEEP = "time.sleep"
MONOTONIC = "time.monotonic"

FIRST_SERVICE_ID = "arangodb-graphrag-retriever-aaa"
SECOND_SERVICE_ID = "arangodb-graphrag-retriever-bbb"


def _project(*service_ids: str) -> AiProject:
    """Return a project snapshot listing one retriever per id given."""
    project = AiProject(project_name="sales", project_type="autograph", project_db_name="mydb")
    if service_ids:
        project.project_metadata = GraphRagProjectMetaData(
            retriever_services=[
                AiService(
                    service_id=service_id,
                    service_url=f"https://host:8529/graphrag/retriever/{service_id[-3:]}/",
                )
                for service_id in service_ids
            ]
        )
    return project


def _sales_project_handle(
    placeholder_communication: Communication, *service_ids: str
) -> AiProjectHandle:
    return AiProjectHandle(
        ai_project=_project(*service_ids), communication=placeholder_communication
    )


def test_properties_follow_project_handle_refresh(
    placeholder_communication: Communication,
):
    """The object reads the handle's current snapshot, so a removed retriever reads as gone."""
    with patch(GET_PROJECT) as mock_get_project:
        mock_get_project.side_effect = [
            _project(FIRST_SERVICE_ID, SECOND_SERVICE_ID),
            _project(FIRST_SERVICE_ID),
        ]
        sales = _sales_project_handle(placeholder_communication)
        retriever = sales.autorag.get(service_id=SECOND_SERVICE_ID)
        assert retriever.is_deployed is True

        sales.refresh()

    assert retriever.service_id == SECOND_SERVICE_ID, "the bound id never changes"
    assert retriever.is_deployed is False
    assert retriever.service_url is None
    assert retriever.service_path is None


def test_repr_names_the_service_id(placeholder_communication: Communication):
    with patch(GET_PROJECT, return_value=_project(FIRST_SERVICE_ID)):
        sales = _sales_project_handle(placeholder_communication)
        retriever = sales.autorag.get(service_id=FIRST_SERVICE_ID)

    assert repr(retriever) == f"AutoRag(service_id={FIRST_SERVICE_ID!r})"


def test_undeploy_deletes_only_the_bound_retriever(
    placeholder_communication: Communication,
):
    with patch(GET_PROJECT) as mock_get_project, patch(DELETE) as mock_delete:
        # The platform lists both before the delete and only the first after it;
        # the closing ``list`` refreshes once more.
        mock_get_project.side_effect = [
            _project(FIRST_SERVICE_ID, SECOND_SERVICE_ID),
            _project(FIRST_SERVICE_ID, SECOND_SERVICE_ID),
            _project(FIRST_SERVICE_ID),
            _project(FIRST_SERVICE_ID),
        ]
        mock_delete.return_value = ServiceInfo(service_id=SECOND_SERVICE_ID)
        sales = _sales_project_handle(placeholder_communication)
        retriever = sales.autorag.get(service_id=SECOND_SERVICE_ID)

        info = retriever.undeploy()
        assert mock_get_project.call_count == 3, "get, before the check and after the delete"
        remaining = [other.service_id for other in sales.autorag.list()]

    assert info.service_id == SECOND_SERVICE_ID
    mock_delete.assert_called_once_with(service_id=SECOND_SERVICE_ID)
    assert retriever.is_deployed is False
    assert remaining == [FIRST_SERVICE_ID]


def test_undeploy_raises_not_deployed_when_the_retriever_is_gone(
    placeholder_communication: Communication,
):
    with patch(GET_PROJECT) as mock_get_project, patch(DELETE) as mock_delete:
        mock_get_project.side_effect = [
            _project(FIRST_SERVICE_ID, SECOND_SERVICE_ID),
            _project(FIRST_SERVICE_ID),
        ]
        sales = _sales_project_handle(placeholder_communication)
        retriever = sales.autorag.get(service_id=SECOND_SERVICE_ID)

        with pytest.raises(AutoRagNotDeployedError):
            retriever.undeploy()

    mock_delete.assert_not_called()


def test_undeploy_reraises_service_not_found_from_acp(
    placeholder_communication: Communication,
):
    with patch(GET_PROJECT) as mock_get_project, patch(DELETE) as mock_delete:
        mock_get_project.return_value = _project(FIRST_SERVICE_ID)
        mock_delete.side_effect = ServiceNotFoundError("not found", status_code=404)
        sales = _sales_project_handle(placeholder_communication)
        retriever = sales.autorag.get(service_id=FIRST_SERVICE_ID)

        with pytest.raises(ServiceNotFoundError):
            retriever.undeploy()

    mock_delete.assert_called_once_with(service_id=FIRST_SERVICE_ID)
    assert mock_get_project.call_count == 2, "get and the check; nothing after the failed delete"


# --- AutoRag.wait_until_ready ----------------------------------------------


def test_wait_until_ready_raises_not_deployed_without_sending(
    placeholder_communication: Communication,
):
    with patch(GET_PROJECT) as mock_get_project, patch(HEALTH) as mock_health:
        mock_get_project.side_effect = [_project(FIRST_SERVICE_ID), _project()]
        sales = _sales_project_handle(placeholder_communication)
        retriever = sales.autorag.get(service_id=FIRST_SERVICE_ID)

        with pytest.raises(AutoRagNotDeployedError):
            retriever.wait_until_ready()

    mock_health.assert_not_called()


def test_wait_until_ready_returns_false_when_the_bound_passes(
    placeholder_communication: Communication,
):
    """Health never reports OK, so the wait gives up once the deadline passes."""
    with (
        patch(GET_PROJECT, return_value=_project(FIRST_SERVICE_ID)),
        patch(HEALTH) as mock_health,
        patch(SLEEP) as mock_sleep,
        patch(MONOTONIC) as mock_monotonic,
    ):
        mock_health.return_value = AutoRagHealthCheckResponse(status="FAIL")
        # The fake clock: start, after the first poll (within the bound), after
        # the second (past it). Sleep is a no-op, so real time never advances.
        mock_monotonic.side_effect = [0.0, 1.0, 3.0, 3.0]
        sales = _sales_project_handle(placeholder_communication)
        retriever = sales.autorag.get(service_id=FIRST_SERVICE_ID)

        ready = retriever.wait_until_ready(timeout=2.0, poll_interval=1.0)

    assert ready is False
    assert mock_health.call_count == 2
    mock_health.assert_called_with(service_path="/graphrag/retriever/aaa")
    mock_sleep.assert_called_once_with(1.0)


def test_wait_until_ready_returns_true_once_healthy(
    placeholder_communication: Communication,
):
    with (
        patch(GET_PROJECT, return_value=_project(FIRST_SERVICE_ID)),
        patch(HEALTH) as mock_health,
        patch(SLEEP) as mock_sleep,
    ):
        mock_health.return_value = AutoRagHealthCheckResponse(status="OK")
        sales = _sales_project_handle(placeholder_communication)
        retriever = sales.autorag.get(service_id=FIRST_SERVICE_ID)

        ready = retriever.wait_until_ready(timeout=2.0, poll_interval=1.0)

    assert ready is True
    mock_health.assert_called_once_with(service_path="/graphrag/retriever/aaa")
    mock_sleep.assert_not_called()


# --- AutoRag.ask -----------------------------------------------------------


def test_ask_posts_a_unified_query_and_returns_the_answer(
    placeholder_communication: Communication,
):
    with (
        patch(GET_PROJECT, return_value=_project(FIRST_SERVICE_ID)) as mock_get_project,
        patch(QUERY) as mock_query,
    ):
        mock_query.return_value = GraphRagQueryResponse(
            result="Refunds are accepted within 30 days.", run_id="run-1"
        )
        sales = _sales_project_handle(placeholder_communication)
        retriever = sales.autorag.get(service_id=FIRST_SERVICE_ID)

        answer = retriever.ask("What is the refund policy?")

    assert answer.result == "Refunds are accepted within 30 days."
    assert answer.run_id == "run-1"
    assert mock_get_project.call_count == 2, "get, then the check before sending"
    mock_query.assert_called_once()
    assert mock_query.call_args.kwargs["service_path"] == "/graphrag/retriever/aaa"
    request = mock_query.call_args.kwargs["request"]
    assert isinstance(request, GraphRagQueryRequest)
    assert request.query == "What is the refund policy?"
    assert request.query_type == QueryType.UNIFIED
    assert request.response_instructions == ""
    assert request.include_metadata is False
    assert request.partition_ids == []
    assert request.show_citations is None, "omitted, so the service default applies"
    assert request.model == ""


def test_ask_passes_the_optional_arguments_into_the_request(
    placeholder_communication: Communication,
):
    with (
        patch(GET_PROJECT, return_value=_project(FIRST_SERVICE_ID)),
        patch(QUERY) as mock_query,
    ):
        mock_query.return_value = GraphRagQueryResponse(result="Short.", run_id="run-2")
        sales = _sales_project_handle(placeholder_communication)
        retriever = sales.autorag.get(service_id=FIRST_SERVICE_ID)

        retriever.ask(
            "Summarize the refund policy",
            query_type=QueryType.LOCAL,
            response_instructions="Short answer",
            include_metadata=True,
            partition_ids=["finance", "legal"],
            show_citations=False,
            model="gpt-4o-mini",
        )

    request = mock_query.call_args.kwargs["request"]
    assert request.query_type == QueryType.LOCAL
    assert request.response_instructions == "Short answer"
    assert request.include_metadata is True
    assert request.partition_ids == ["finance", "legal"]
    assert request.show_citations is False
    assert request.model == "gpt-4o-mini"


def test_ask_rejects_an_empty_query_without_sending(
    placeholder_communication: Communication,
):
    with (
        patch(GET_PROJECT, return_value=_project(FIRST_SERVICE_ID)) as mock_get_project,
        patch(QUERY) as mock_query,
    ):
        sales = _sales_project_handle(placeholder_communication)
        retriever = sales.autorag.get(service_id=FIRST_SERVICE_ID)

        with pytest.raises(ValueError):
            retriever.ask("   ")

    mock_query.assert_not_called()
    assert mock_get_project.call_count == 1, "the argument check comes before any refresh"


def test_ask_raises_not_deployed_without_sending(
    placeholder_communication: Communication,
):
    with patch(GET_PROJECT) as mock_get_project, patch(QUERY) as mock_query:
        mock_get_project.side_effect = [_project(FIRST_SERVICE_ID), _project()]
        sales = _sales_project_handle(placeholder_communication)
        retriever = sales.autorag.get(service_id=FIRST_SERVICE_ID)

        with pytest.raises(AutoRagNotDeployedError):
            retriever.ask("anything")

    mock_query.assert_not_called()


def test_ask_raises_query_failed_on_a_failure_code(
    placeholder_communication: Communication,
):
    """A ``200`` whose body carries ``error_code`` is a failed query, not an empty answer."""
    with (
        patch(GET_PROJECT, return_value=_project(FIRST_SERVICE_ID)),
        patch(QUERY) as mock_query,
    ):
        mock_query.return_value = GraphRagQueryResponse(
            result="", run_id="run-3", error_code="INSUFFICIENT_QUOTA"
        )
        sales = _sales_project_handle(placeholder_communication)
        retriever = sales.autorag.get(service_id=FIRST_SERVICE_ID)

        with pytest.raises(QueryFailedError) as exc_info:
            retriever.ask("anything")

    assert exc_info.value.failure_code == "INSUFFICIENT_QUOTA"
    assert exc_info.value.run_id == "run-3"
    assert exc_info.value.status_code == 200
    assert "INSUFFICIENT_QUOTA" in str(exc_info.value)
