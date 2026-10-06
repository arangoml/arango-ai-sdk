"""Unit tests for :class:`AutoRagManager`; no platform needed.

``AiProjectHandle.refresh`` stands in for the platform's view of the project
and ``ServiceApi`` for ACP's answers, so the tests check what the manager
decides and sends, not what the platform does. The fixture project carries
two retrievers so a lookup by id is actually exercised.
"""

from unittest.mock import patch

import pytest

from arango_ai_sdk._naming import AcpPath, AutoRagInstallParams
from arango_ai_sdk.autorag import AutoRag
from arango_ai_sdk.autorag_manager import AutoRagDeployResult
from arango_ai_sdk.communication import Communication
from arango_ai_sdk.exceptions import (
    AutoRagNotDeployedError,
    InvalidServiceParametersError,
)
from arango_ai_sdk.models import (
    AiProject,
    AiService,
    GraphRagProjectMetaData,
    ServiceInfo,
)
from arango_ai_sdk.project_handle import AiProjectHandle

REFRESH = "arango_ai_sdk.project_handle.AiProjectHandle.refresh"
GET_PROJECT = "arango_ai_sdk.project_handle.get_project"
DEPLOY_SERVICE = "arango_ai_sdk._service_api.ServiceApi.deploy_service"
WAIT_UNTIL_READY = "arango_ai_sdk.autorag.AutoRag.wait_until_ready"

FIRST = "arangodb-graphrag-retriever-aaa"
SECOND = "arangodb-graphrag-retriever-bbb"


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


def _sales(placeholder_communication: Communication, *service_ids: str) -> AiProjectHandle:
    return AiProjectHandle(
        ai_project=_project(*service_ids), communication=placeholder_communication
    )


def _deploy(sales: AiProjectHandle, **extra) -> AutoRagDeployResult:
    """Call ``deploy`` with the four required arguments plus ``extra``."""
    return sales.autorag.deploy(
        chat_api_provider="openai",
        embedding_api_provider="openai",
        chat_secret_profile_id="chat-secret",
        embedding_secret_profile_id="embed-secret",
        **extra,
    )


def test_deploy_sends_the_install_request_and_binds_the_new_service(
    placeholder_communication: Communication,
):
    with patch(GET_PROJECT) as mock_get_project, patch(DEPLOY_SERVICE) as mock_deploy:
        mock_get_project.return_value = _project(FIRST, SECOND)
        mock_deploy.return_value = ServiceInfo(service_id=SECOND)
        sales = _sales(placeholder_communication, FIRST)

        result = _deploy(sales)

    assert result.service_info.service_id == SECOND
    assert result.ready is None, "nobody waited, so readiness is unknown"
    assert isinstance(result.autorag, AutoRag)
    assert result.autorag.service_id == SECOND
    assert result.autorag.service_url == "https://host:8529/graphrag/retriever/bbb/"
    mock_deploy.assert_called_once()
    assert mock_deploy.call_args.kwargs["install_path"] == AcpPath.GRAPHRAG_RETRIEVER
    request = mock_deploy.call_args.kwargs["request"]
    assert request.env == {
        AutoRagInstallParams.GENAI_PROJECT_NAME: "sales",
        AutoRagInstallParams.DB_NAME: "mydb",
        AutoRagInstallParams.CHAT_API_PROVIDER: "openai",
        AutoRagInstallParams.EMBEDDING_API_PROVIDER: "openai",
        AutoRagInstallParams.CHAT_SECRET_PROFILE_ID: "chat-secret",
        AutoRagInstallParams.EMBEDDING_SECRET_PROFILE_ID: "embed-secret",
    }
    assert request.labels == {}
    assert mock_get_project.call_count == 1, "once after the install, nothing to check before it"


def test_deploy_does_not_refuse_a_second_retriever(
    placeholder_communication: Communication,
):
    """A project can run several retrievers, so an existing one never blocks a deploy."""
    with patch(REFRESH) as mock_refresh, patch(DEPLOY_SERVICE) as mock_deploy:
        mock_refresh.return_value = _project(FIRST, SECOND)
        mock_deploy.return_value = ServiceInfo(service_id=SECOND)
        sales = _sales(placeholder_communication, FIRST)

        result = _deploy(sales)

    assert result.autorag.service_id == SECOND
    assert [retriever.service_id for retriever in sales.autorag.list()] == [
        FIRST,
        SECOND,
    ]


def test_deploy_adds_optional_settings_and_labels_when_given(
    placeholder_communication: Communication,
):
    with patch(REFRESH) as mock_refresh, patch(DEPLOY_SERVICE) as mock_deploy:
        mock_refresh.return_value = _project(FIRST)
        mock_deploy.return_value = ServiceInfo(service_id=FIRST)
        sales = _sales(placeholder_communication)

        _deploy(
            sales,
            chat_model="gpt-4o",
            embedding_model="text-embedding-3-small",
            chat_api_url="https://chat.example",
            embedding_api_url="https://embed.example",
            labels={"team": "sales"},
        )

    request = mock_deploy.call_args.kwargs["request"]
    assert request.env[AutoRagInstallParams.CHAT_MODEL] == "gpt-4o"
    assert request.env[AutoRagInstallParams.EMBEDDING_MODEL] == "text-embedding-3-small"
    assert request.env[AutoRagInstallParams.CHAT_API_URL] == "https://chat.example"
    assert request.env[AutoRagInstallParams.EMBEDDING_API_URL] == "https://embed.example"
    assert request.labels == {"team": "sales"}


def test_deploy_with_wait_reports_readiness(placeholder_communication: Communication):
    with (
        patch(REFRESH) as mock_refresh,
        patch(DEPLOY_SERVICE) as mock_deploy,
        patch(WAIT_UNTIL_READY) as mock_wait,
    ):
        mock_refresh.return_value = _project(FIRST)
        mock_deploy.return_value = ServiceInfo(service_id=FIRST)
        mock_wait.return_value = True
        sales = _sales(placeholder_communication)

        result = _deploy(sales, wait=True)

    assert result.ready is True
    mock_wait.assert_called_once_with()


def test_deploy_reraises_invalid_parameters_without_refreshing(
    placeholder_communication: Communication,
):
    with patch(REFRESH) as mock_refresh, patch(DEPLOY_SERVICE) as mock_deploy:
        mock_deploy.side_effect = InvalidServiceParametersError("bad provider", status_code=400)
        sales = _sales(placeholder_communication)

        with pytest.raises(InvalidServiceParametersError):
            _deploy(sales)

    mock_refresh.assert_not_called()


# --- AutoRagManager.list and get ------------------------------------------


def test_list_returns_one_object_per_retriever_in_metadata(
    placeholder_communication: Communication,
):
    with patch(GET_PROJECT, return_value=_project(FIRST, SECOND)) as mock_get_project:
        sales = _sales(placeholder_communication)

        retrievers = sales.autorag.list()

    assert mock_get_project.call_count == 1
    assert [retriever.service_id for retriever in retrievers] == [FIRST, SECOND]
    assert all(isinstance(retriever, AutoRag) for retriever in retrievers)
    assert retrievers[0].service_url == "https://host:8529/graphrag/retriever/aaa/"
    assert retrievers[1].service_path == "/graphrag/retriever/bbb"


def test_list_is_empty_when_the_project_has_no_metadata(
    placeholder_communication: Communication,
):
    with patch(GET_PROJECT, return_value=_project()):
        sales = _sales(placeholder_communication)

        assert sales.autorag.list() == []


def test_get_returns_the_object_bound_to_the_id(
    placeholder_communication: Communication,
):
    with patch(GET_PROJECT, return_value=_project(FIRST, SECOND)):
        sales = _sales(placeholder_communication)

        retriever = sales.autorag.get(service_id=SECOND)

    assert retriever.service_id == SECOND
    assert retriever.is_deployed is True
    assert retriever.service_url == "https://host:8529/graphrag/retriever/bbb/"


def test_get_raises_not_deployed_for_an_unknown_id(
    placeholder_communication: Communication,
):
    with patch(GET_PROJECT, return_value=_project(FIRST)):
        sales = _sales(placeholder_communication)

        with pytest.raises(AutoRagNotDeployedError):
            sales.autorag.get(service_id=SECOND)
