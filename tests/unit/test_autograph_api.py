"""Unit tests for :class:`AutoGraphApi`; no platform needed.

``Communication.send_request`` is patched, so the tests check the request
``AutoGraphApi`` sends, the model it loads the reply into, and the SDK
exception it translates an error answer into.
"""

from unittest.mock import patch

import pytest

from arango_ai_sdk._autograph_api import AutoGraphApi
from arango_ai_sdk.communication import Communication
from arango_ai_sdk.exceptions import AutoGraphBusyError, ModelConfigNotReadyError, ServiceError
from arango_ai_sdk.models import (
    BuildStrategy,
    CreateCorpusBuildRequest,
    CreateCorpusBuildResponse,
    GetBuildStatusResponse,
    GetRagStrategizerJobStatusResponse,
    GetRagStrategizerStrategyResponse,
    RagStrategizerComplexity,
    TriggerRagStrategizerRequest,
    TriggerRagStrategizerResponse,
)

SEND_REQUEST = "arango_ai_sdk.communication.Communication.send_request"

SERVICE_PATH = "/autograph/c-123"


def test_get_corpus_build_status_returns_status(
    placeholder_communication: Communication,
):
    with patch(SEND_REQUEST) as mock_send:
        mock_send.return_value = {
            "corpusBuildId": "build-1",
            "status": "running",
            "progress": 40,
            "message": "Embedding documents",
        }
        api = AutoGraphApi(communication=placeholder_communication)

        status = api.get_corpus_build_status(service_path=SERVICE_PATH, build_id="build-1")

    mock_send.assert_called_once_with("get", f"{SERVICE_PATH}/v1/corpus/builds/build-1")
    assert isinstance(status, GetBuildStatusResponse)
    assert status.corpus_build_id == "build-1"
    assert status.status == "running"
    assert status.progress == 40
    assert status.message == "Embedding documents"


def test_start_corpus_build_posts_request_and_returns_id(
    placeholder_communication: Communication,
):
    request = CreateCorpusBuildRequest(
        categories=["finance"], incremental=True, strategy=BuildStrategy(top_k=5)
    )
    with patch(SEND_REQUEST) as mock_send:
        mock_send.return_value = {"corpusBuildId": "build-1", "graphName": "p_CorpusGraph"}
        api = AutoGraphApi(communication=placeholder_communication)

        response = api.start_corpus_build(service_path=SERVICE_PATH, request=request)

    mock_send.assert_called_once_with(
        "post", f"{SERVICE_PATH}/v1/corpus/builds", data=request.to_dict()
    )
    assert isinstance(response, CreateCorpusBuildResponse)
    assert response.corpus_build_id == "build-1"
    assert response.graph_name == "p_CorpusGraph"


@pytest.mark.parametrize(
    ("message", "status_code", "expected"),
    [
        (
            "Model configuration is invalid (auth_failed): bad key "
            "[Error: InvalidRequestError, HTTP: 400]",
            400,
            ModelConfigNotReadyError,
        ),
        (
            "Model configuration reconciliation is still in progress; retry after startup "
            "finishes reloading persisted settings [Error: InvalidRequestError, HTTP: 400]",
            400,
            ModelConfigNotReadyError,
        ),
        (
            "A build is already running [Error: BuildInProgressError, HTTP: 409]",
            409,
            AutoGraphBusyError,
        ),
        (
            "An orchestration is running [Error: OrchestrationInProgressError, HTTP: 409]",
            409,
            AutoGraphBusyError,
        ),
    ],
)
def test_start_corpus_build_translates_error(
    placeholder_communication: Communication,
    message: str,
    status_code: int,
    expected: type[ServiceError],
):
    with patch(SEND_REQUEST) as mock_send:
        mock_send.side_effect = ServiceError(message, status_code=status_code)
        api = AutoGraphApi(communication=placeholder_communication)

        with pytest.raises(expected) as exc_info:
            api.start_corpus_build(
                service_path=SERVICE_PATH, request=CreateCorpusBuildRequest(categories=["a"])
            )

    assert exc_info.value.status_code == status_code


def test_start_corpus_build_passes_other_errors_through(
    placeholder_communication: Communication,
):
    original = ServiceError(
        "categories must not be empty [Error: InvalidRequestError, HTTP: 400]", status_code=400
    )
    with patch(SEND_REQUEST) as mock_send:
        mock_send.side_effect = original
        api = AutoGraphApi(communication=placeholder_communication)

        with pytest.raises(ServiceError) as exc_info:
            api.start_corpus_build(
                service_path=SERVICE_PATH, request=CreateCorpusBuildRequest(categories=["a"])
            )

    assert exc_info.value is original


def test_start_strategizer_posts_request_and_returns_job_id(
    placeholder_communication: Communication,
):
    request = TriggerRagStrategizerRequest(
        project="sales",
        complexity=RagStrategizerComplexity.high,
        categories=["finance"],
    )
    with patch(SEND_REQUEST) as mock_send:
        mock_send.return_value = {"strategizeJobId": "job-1"}
        api = AutoGraphApi(communication=placeholder_communication)

        response = api.start_strategizer(service_path=SERVICE_PATH, request=request)

    mock_send.assert_called_once_with(
        "post", f"{SERVICE_PATH}/v1/rag-strategizer/analyze", data=request.to_dict()
    )
    assert isinstance(response, TriggerRagStrategizerResponse)
    assert response.strategize_job_id == "job-1"


@pytest.mark.parametrize(
    ("message", "status_code", "expected"),
    [
        (
            "Model configuration is invalid (auth_failed): bad key "
            "[Error: InvalidRequestError, HTTP: 400]",
            400,
            ModelConfigNotReadyError,
        ),
        (
            "A strategizer run is already going [Error: StrategizerInProgressError, HTTP: 409]",
            409,
            AutoGraphBusyError,
        ),
    ],
)
def test_start_strategizer_translates_error(
    placeholder_communication: Communication,
    message: str,
    status_code: int,
    expected: type[ServiceError],
):
    with patch(SEND_REQUEST) as mock_send:
        mock_send.side_effect = ServiceError(message, status_code=status_code)
        api = AutoGraphApi(communication=placeholder_communication)

        with pytest.raises(expected) as exc_info:
            api.start_strategizer(
                service_path=SERVICE_PATH,
                request=TriggerRagStrategizerRequest(project="sales", categories=["finance"]),
            )

    assert exc_info.value.status_code == status_code


def test_get_strategizer_job_status_returns_status(
    placeholder_communication: Communication,
):
    with patch(SEND_REQUEST) as mock_send:
        mock_send.return_value = {
            "status": "running",
            "progress": 0.5,
            "clustersTotal": 4,
            "clustersDone": 2,
        }
        api = AutoGraphApi(communication=placeholder_communication)

        status = api.get_strategizer_job_status(service_path=SERVICE_PATH, job_id="job-1")

    mock_send.assert_called_once_with("get", f"{SERVICE_PATH}/v1/rag-strategizer/jobs/job-1")
    assert isinstance(status, GetRagStrategizerJobStatusResponse)
    assert status.status == "running"
    assert status.progress == 0.5
    assert status.clusters_total == 4
    assert status.clusters_done == 2


def test_get_strategies_returns_the_stored_list(
    placeholder_communication: Communication,
):
    with patch(SEND_REQUEST) as mock_send:
        mock_send.return_value = {
            "strategies": [{"clusterId": "c1", "strategyType": "vector"}],
            "totalStrategies": 1,
        }
        api = AutoGraphApi(communication=placeholder_communication)

        result = api.get_strategies(service_path=SERVICE_PATH)

    mock_send.assert_called_once_with("get", f"{SERVICE_PATH}/v1/rag-strategizer/strategy")
    assert isinstance(result, GetRagStrategizerStrategyResponse)
    assert result.total_strategies == 1
    assert result.strategies[0].cluster_id == "c1"
    assert result.strategies[0].strategy_type == "vector"
