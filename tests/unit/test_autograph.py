"""Unit tests for :class:`AutoGraph`; no platform needed.

``AiProjectHandle.refresh`` stands in for the platform's view of the project
and ``ServiceApi.deploy_service`` for ACP's answer, so the tests check
what ``AutoGraph`` decides and sends, not what the platform does.
"""

from collections.abc import Callable
from typing import cast
from unittest.mock import patch

import betterproto
import pytest

from arango_ai_sdk._autograph_api import AutoGraphApi
from arango_ai_sdk._naming import AcpPath, AutoGraphInstallParams, OrchestrationPhase
from arango_ai_sdk.autograph import (
    DeployResult,
    IngestProgress,
    IngestResult,
    JobState,
    _wait_for_job,
)
from arango_ai_sdk.communication import Communication
from arango_ai_sdk.exceptions import (
    AutoGraphAlreadyDeployedError,
    AutoGraphNotDeployedError,
    IngestionFailedError,
    InvalidServiceParametersError,
    JobStatusLostError,
    JobTimeoutError,
    ProjectNotFoundError,
    ServiceError,
    ServiceNotFoundError,
)
from arango_ai_sdk.models import (
    AiProject,
    AutoGraphModelSettings,
    AutoGraphService,
    BuildStrategy,
    CreateCorpusBuildResponse,
    GetBuildStatusResponse,
    GetOrchestrationStatusResponse,
    GetRagStrategizerJobStatusResponse,
    GetRagStrategizerStrategyResponse,
    GraphRagProjectMetaData,
    HealthCheckResponse,
    RagStrategizerComplexity,
    ServiceInfo,
    TriggerOrchestrationResponse,
    TriggerRagStrategizerResponse,
)
from arango_ai_sdk.project_handle import AiProjectHandle

REFRESH = "arango_ai_sdk.project_handle.AiProjectHandle.refresh"
GET_PROJECT = "arango_ai_sdk.project_handle.get_project"
DEPLOY_SERVICE = "arango_ai_sdk._service_api.ServiceApi.deploy_service"
DELETE = "arango_ai_sdk._service_api.ServiceApi.delete"
HEALTH = "arango_ai_sdk._autograph_api.AutoGraphApi.health"
START_BUILD = "arango_ai_sdk._autograph_api.AutoGraphApi.start_corpus_build"
BUILD_STATUS = "arango_ai_sdk._autograph_api.AutoGraphApi.get_corpus_build_status"
START_STRATEGIZER = "arango_ai_sdk._autograph_api.AutoGraphApi.start_strategizer"
STRATEGIZER_STATUS = "arango_ai_sdk._autograph_api.AutoGraphApi.get_strategizer_job_status"
GET_STRATEGIES = "arango_ai_sdk._autograph_api.AutoGraphApi.get_strategies"
START_ORCHESTRATION = "arango_ai_sdk._autograph_api.AutoGraphApi.start_orchestration"
ORCHESTRATION_STATUS = "arango_ai_sdk._autograph_api.AutoGraphApi.get_orchestration_status"
SEND_REQUEST = "arango_ai_sdk.communication.Communication.send_request"
SERVICE_PATH = "/autograph/c-123"
WAIT_UNTIL_READY = "arango_ai_sdk.autograph.AutoGraph.wait_until_ready"
SLEEP = "time.sleep"
MONOTONIC = "time.monotonic"
CORPUS_BUILD = "arango_ai_sdk.autograph.AutoGraph.corpus_build"
STRATEGIZE = "arango_ai_sdk.autograph.AutoGraph.strategize"
STRATEGIES = "arango_ai_sdk.autograph.AutoGraph.strategies"
ORCHESTRATE = "arango_ai_sdk.autograph.AutoGraph.orchestrate"


def _deploy(sales: AiProjectHandle, chat_api_provider: str = "openai") -> DeployResult:
    """Call ``deploy`` with the five required arguments; only the chat provider varies."""
    return sales.autograph.deploy(
        chat_api_provider=chat_api_provider,
        embedding_api_provider="openai",
        chat_secret_profile_id="chat-secret",
        embedding_secret_profile_id="embed-secret",
        fps_recovery_username="fps-recovery",
    )


def _project(deployed: bool) -> AiProject:
    project = AiProject(project_name="sales", project_type="autograph", project_db_name="mydb")
    if deployed:
        project.project_metadata = GraphRagProjectMetaData(
            autograph_service=AutoGraphService(
                service_id="svc-123", service_url="https://host:8529/autograph/c-123/"
            )
        )
    return project


def test_deploy_sends_the_install_request_when_nothing_is_deployed(
    placeholder_communication: Communication,
):
    with patch(REFRESH) as mock_refresh, patch(DEPLOY_SERVICE) as mock_deploy:
        mock_refresh.return_value = _project(deployed=False)
        mock_deploy.return_value = ServiceInfo(service_id="svc-123")
        sales = AiProjectHandle(
            ai_project=_project(deployed=False), communication=placeholder_communication
        )

        result = _deploy(sales)

    assert result.service_info.service_id == "svc-123"
    assert result.ready is None, "nobody waited, so readiness is unknown"
    mock_deploy.assert_called_once()
    assert mock_deploy.call_args.kwargs["install_path"] == AcpPath.AUTOGRAPH
    request = mock_deploy.call_args.kwargs["request"]
    assert request.env == {
        AutoGraphInstallParams.GENAI_PROJECT_NAME: "sales",
        AutoGraphInstallParams.DB_NAME: "mydb",
        AutoGraphInstallParams.CHAT_API_PROVIDER: "openai",
        AutoGraphInstallParams.EMBEDDING_API_PROVIDER: "openai",
        AutoGraphInstallParams.CHAT_SECRET_PROFILE_ID: "chat-secret",
        AutoGraphInstallParams.EMBEDDING_SECRET_PROFILE_ID: "embed-secret",
        AutoGraphInstallParams.FPS_RECOVERY_USERNAME: "fps-recovery",
    }


def test_deploy_with_wait_reports_not_ready(
    placeholder_communication: Communication,
):
    """A slow start does not fail the deploy: the service info comes back with ``ready=False``."""
    with (
        patch(REFRESH) as mock_refresh,
        patch(DEPLOY_SERVICE) as mock_deploy,
        patch(WAIT_UNTIL_READY) as mock_wait,
    ):
        mock_refresh.return_value = _project(deployed=False)
        mock_deploy.return_value = ServiceInfo(service_id="svc-123")
        mock_wait.return_value = False
        sales = AiProjectHandle(
            ai_project=_project(deployed=False), communication=placeholder_communication
        )

        result = sales.autograph.deploy(
            chat_api_provider="openai",
            embedding_api_provider="openai",
            chat_secret_profile_id="chat-secret",
            embedding_secret_profile_id="embed-secret",
            fps_recovery_username="fps-recovery",
            wait=True,
        )

    assert result.service_info.service_id == "svc-123"
    assert result.ready is False
    mock_wait.assert_called_once_with()


def test_deploy_with_wait_reports_ready(
    placeholder_communication: Communication,
):
    """A slow start does not fail the deploy: the service info comes back with ``ready=True``."""
    with (
        patch(REFRESH) as mock_refresh,
        patch(DEPLOY_SERVICE) as mock_deploy,
        patch(WAIT_UNTIL_READY) as mock_wait,
    ):
        mock_refresh.return_value = _project(deployed=False)
        mock_deploy.return_value = ServiceInfo(service_id="svc-123")
        mock_wait.return_value = True
        sales = AiProjectHandle(
            ai_project=_project(deployed=False), communication=placeholder_communication
        )

        result = sales.autograph.deploy(
            chat_api_provider="openai",
            embedding_api_provider="openai",
            chat_secret_profile_id="chat-secret",
            embedding_secret_profile_id="embed-secret",
            fps_recovery_username="fps-recovery",
            wait=True,
        )

    assert result.service_info.service_id == "svc-123"
    assert result.ready is True
    mock_wait.assert_called_once_with()


def test_deploy_refuses_when_the_project_already_has_autograph(
    placeholder_communication: Communication,
):
    with (
        patch(GET_PROJECT, return_value=_project(deployed=True)),
        patch(DEPLOY_SERVICE) as mock_deploy,
    ):
        sales = AiProjectHandle(
            ai_project=_project(deployed=False), communication=placeholder_communication
        )

        with pytest.raises(AutoGraphAlreadyDeployedError):
            _deploy(sales)

    mock_deploy.assert_not_called()


def test_autograph_properties_follow_a_handle_refresh(
    placeholder_communication: Communication,
):
    """AutoGraph reads the handle's current snapshot rather than retaining the old one."""
    with patch(GET_PROJECT, return_value=_project(deployed=True)):
        sales = AiProjectHandle(
            ai_project=_project(deployed=False), communication=placeholder_communication
        )

        sales.refresh()

    assert sales.autograph.is_deployed is True
    assert sales.autograph.service_id == "svc-123"


def test_deploy_raises_invalid_service_parameters_when_acp_rejects_the_install(
    placeholder_communication: Communication,
):
    with patch(REFRESH) as mock_refresh, patch(DEPLOY_SERVICE) as mock_deploy:
        mock_refresh.return_value = _project(deployed=False)
        mock_deploy.side_effect = InvalidServiceParametersError(
            "chat_api_provider is empty", status_code=400
        )
        sales = AiProjectHandle(
            ai_project=_project(deployed=False), communication=placeholder_communication
        )

        with pytest.raises(InvalidServiceParametersError):
            _deploy(sales)


def test_deploy_reraises_project_not_found_from_refresh(
    placeholder_communication: Communication,
):
    with patch(REFRESH) as mock_refresh, patch(DEPLOY_SERVICE) as mock_deploy:
        mock_refresh.side_effect = ProjectNotFoundError("gone", status_code=404)
        sales = AiProjectHandle(
            ai_project=_project(deployed=False), communication=placeholder_communication
        )

        with pytest.raises(ProjectNotFoundError):
            _deploy(sales)

    mock_deploy.assert_not_called()


def test_deploy_refreshes_twice_on_success_and_once_on_each_failure(
    placeholder_communication: Communication,
):
    with patch(REFRESH) as mock_refresh, patch(DEPLOY_SERVICE) as mock_deploy:
        mock_refresh.return_value = _project(deployed=False)
        mock_deploy.return_value = ServiceInfo(service_id="svc-123")
        sales = AiProjectHandle(
            ai_project=_project(deployed=False), communication=placeholder_communication
        )

        _deploy(sales)
        assert mock_refresh.call_count == 2, "before the check and after the install"

        mock_refresh.reset_mock()
        mock_deploy.side_effect = InvalidServiceParametersError("rejected", status_code=400)
        with pytest.raises(InvalidServiceParametersError):
            _deploy(sales)
        assert mock_refresh.call_count == 1, "the install failed, so no refresh after it"


def test_deploy_leaves_the_project_undeployed_when_acp_rejects_the_install(
    placeholder_communication: Communication,
):
    with patch(REFRESH) as mock_refresh, patch(DEPLOY_SERVICE) as mock_deploy:
        mock_refresh.return_value = _project(deployed=False)
        mock_deploy.side_effect = InvalidServiceParametersError("rejected", status_code=400)
        sales = AiProjectHandle(
            ai_project=_project(deployed=False), communication=placeholder_communication
        )

        with pytest.raises(InvalidServiceParametersError):
            _deploy(sales)

        assert sales.autograph.is_deployed is False
        assert sales.autograph.service_id is None


def test_deploy_passes_an_empty_required_argument_through_to_acp(
    placeholder_communication: Communication,
):
    """Pin that the SDK does not validate required strings itself.

    ACP does not validate them either: it installs the service and only skips
    writing ``model_settings``. Client-side validation was decided against for now.
    """
    with patch(REFRESH) as mock_refresh, patch(DEPLOY_SERVICE) as mock_deploy:
        mock_refresh.return_value = _project(deployed=False)
        mock_deploy.return_value = ServiceInfo(service_id="svc-123")
        sales = AiProjectHandle(
            ai_project=_project(deployed=False), communication=placeholder_communication
        )

        _deploy(sales, chat_api_provider="")

    request = mock_deploy.call_args.kwargs["request"]
    assert request.env[AutoGraphInstallParams.CHAT_API_PROVIDER] == ""


def test_undeploy_deletes_the_service_named_in_project_metadata(
    placeholder_communication: Communication,
):
    with patch(GET_PROJECT) as mock_get_project, patch(DELETE) as mock_delete:
        # The platform reports the service before the delete and none after it.
        mock_get_project.side_effect = [
            _project(deployed=True),
            _project(deployed=False),
        ]
        mock_delete.return_value = ServiceInfo(service_id="svc-123")
        sales = AiProjectHandle(
            ai_project=_project(deployed=True), communication=placeholder_communication
        )

        info = sales.autograph.undeploy()

    assert info.service_id == "svc-123"
    mock_delete.assert_called_once_with(service_id="svc-123")
    assert mock_get_project.call_count == 2, "before the check and after the delete"
    assert sales.autograph.is_deployed is False
    assert sales.autograph.service_id is None


def test_undeploy_reraises_service_not_found_when_acp_no_longer_knows_the_service(
    placeholder_communication: Communication,
):
    with patch(REFRESH) as mock_refresh, patch(DELETE) as mock_delete:
        # The project metadata still names the service, but ACP has lost it.
        mock_refresh.return_value = _project(deployed=True)
        mock_delete.side_effect = ServiceNotFoundError("service svc-123 not found", status_code=404)
        sales = AiProjectHandle(
            ai_project=_project(deployed=True), communication=placeholder_communication
        )

        with pytest.raises(ServiceNotFoundError):
            sales.autograph.undeploy()

    mock_delete.assert_called_once_with(service_id="svc-123")
    assert mock_refresh.call_count == 1, "the delete failed, so no refresh after it"


def test_undeploy_before_any_deploy_raises_not_deployed_without_sending(
    placeholder_communication: Communication,
):
    with patch(REFRESH) as mock_refresh, patch(DELETE) as mock_delete:
        mock_refresh.return_value = _project(deployed=False)
        sales = AiProjectHandle(
            ai_project=_project(deployed=False), communication=placeholder_communication
        )

        with pytest.raises(AutoGraphNotDeployedError):
            sales.autograph.undeploy()

    mock_delete.assert_not_called()
    assert mock_refresh.call_count == 1, "the check refused, nothing was sent"


def test_wait_until_ready_raises_not_deployed_error(
    placeholder_communication: Communication,
):
    with patch(GET_PROJECT) as mock_get_project, patch(HEALTH) as mock_health:
        mock_get_project.return_value = _project(deployed=False)
        sales = AiProjectHandle(
            ai_project=_project(deployed=False), communication=placeholder_communication
        )

        with pytest.raises(AutoGraphNotDeployedError):
            sales.autograph.wait_until_ready()

    mock_health.assert_not_called()
    assert mock_get_project.call_count == 1, "the check refused, nothing was sent"


def test_wait_until_ready_returns_false_when_the_bound_passes(
    placeholder_communication: Communication,
):
    """Health never reports SERVING, so the wait gives up once the deadline passes."""
    with (
        patch(GET_PROJECT) as mock_get_project,
        patch(HEALTH) as mock_health,
        patch(SLEEP) as mock_sleep,
        patch(MONOTONIC) as mock_monotonic,
    ):
        mock_get_project.return_value = _project(deployed=True)
        mock_health.return_value = HealthCheckResponse(status="NOT_SERVING")
        # The fake clock: start, after the first poll (within the bound), after
        # the second (past it). Sleep is a no-op, so real time never advances.
        mock_monotonic.side_effect = [0.0, 1.0, 3.0, 3.0]
        sales = AiProjectHandle(
            ai_project=_project(deployed=True), communication=placeholder_communication
        )

        ready: bool = sales.autograph.wait_until_ready(timeout=2.0, poll_interval=1.0)

    assert ready is False
    assert mock_health.call_count == 2
    mock_health.assert_called_with(service_path="/autograph/c-123")
    mock_sleep.assert_called_once_with(1.0)


def test_wait_until_ready_returns_true_once_healthy(
    placeholder_communication: Communication,
):
    with (
        patch(GET_PROJECT) as mock_get_project,
        patch(HEALTH) as mock_health,
        patch(SLEEP) as mock_sleep,
    ):
        mock_get_project.return_value = _project(deployed=True)
        mock_health.return_value = HealthCheckResponse(status="SERVING")
        sales = AiProjectHandle(
            ai_project=_project(deployed=True), communication=placeholder_communication
        )

        ready = sales.autograph.wait_until_ready(timeout=2.0, poll_interval=1.0)

    assert ready is True
    mock_health.assert_called_once_with(service_path="/autograph/c-123")
    mock_sleep.assert_not_called()


def _poll(
    fetch_status: Callable[[], GetBuildStatusResponse],
    *,
    job_id: str,
    timeout: float | None,
    poll_interval: float,
    on_progress: Callable[[GetBuildStatusResponse], None] | None = None,
):
    """Wait on one status call with the arguments written out."""
    return _wait_for_job(
        fetch_status,
        job_id=job_id,
        timeout=timeout,
        poll_interval=poll_interval,
        on_progress=cast(Callable[[betterproto.Message], None] | None, on_progress),
    )


def _body(state: str, **fields) -> dict:
    return {"corpusBuildId": "build-1", "status": state, **fields}


def test_wait_for_job_polls_corpus_build_status_until_completed(
    placeholder_communication: Communication,
):
    progress: list[GetBuildStatusResponse] = []
    with patch(SEND_REQUEST) as mock_send, patch(SLEEP) as mock_sleep:
        mock_send.side_effect = [_body("running", progress=40), _body("completed")]
        api = AutoGraphApi(communication=placeholder_communication)

        result = _poll(
            lambda: api.get_corpus_build_status(service_path=SERVICE_PATH, build_id="build-1"),
            job_id="build-1",
            timeout=None,
            poll_interval=2.0,
            on_progress=progress.append,
        )

    assert isinstance(result, GetBuildStatusResponse)
    assert result.status == "completed"
    assert [status.status for status in progress] == ["running", "completed"]
    mock_send.assert_called_with("get", f"{SERVICE_PATH}/v1/corpus/builds/build-1")
    mock_sleep.assert_called_once_with(2.0)


def test_wait_for_job_raises_ingestion_failed_on_failed(
    placeholder_communication: Communication,
):
    failed = _body("failed", error="embedding provider rejected the key")
    with patch(SEND_REQUEST) as mock_send:
        mock_send.return_value = failed
        api = AutoGraphApi(communication=placeholder_communication)

        with pytest.raises(IngestionFailedError) as exc_info:
            _poll(
                lambda: api.get_corpus_build_status(service_path=SERVICE_PATH, build_id="build-1"),
                job_id="build-1",
                timeout=None,
                poll_interval=1.0,
            )

    assert exc_info.value.job_status.status == "failed"
    assert exc_info.value.job_status.error == "embedding provider rejected the key"
    assert (
        str(exc_info.value) == "Job build-1 ended as failed: embedding provider rejected the key."
    )


def test_wait_for_job_raises_status_lost_on_404_after_a_status(
    placeholder_communication: Communication,
):
    with patch(SEND_REQUEST) as mock_send, patch(SLEEP):
        mock_send.side_effect = [
            _body("running"),
            ServiceError("Requested endpoint does not exist.", status_code=404),
        ]
        api = AutoGraphApi(communication=placeholder_communication)

        with pytest.raises(JobStatusLostError) as exc_info:
            _poll(
                lambda: api.get_corpus_build_status(service_path=SERVICE_PATH, build_id="build-1"),
                job_id="build-1",
                timeout=None,
                poll_interval=1.0,
            )

    assert exc_info.value.job_id == "build-1"
    assert exc_info.value.status_code == 404


def test_wait_for_job_treats_a_404_before_any_status_as_a_poll_error(
    placeholder_communication: Communication,
):
    with patch(SEND_REQUEST) as mock_send, patch(SLEEP):
        mock_send.side_effect = [
            ServiceError("Requested endpoint does not exist.", status_code=404),
            _body("completed"),
        ]
        api = AutoGraphApi(communication=placeholder_communication)

        result = _poll(
            lambda: api.get_corpus_build_status(service_path=SERVICE_PATH, build_id="build-1"),
            job_id="build-1",
            timeout=None,
            poll_interval=1.0,
        )

    assert result.status == "completed"
    assert mock_send.call_count == 2


def test_wait_for_job_survives_poll_errors_below_the_limit(
    placeholder_communication: Communication,
):
    with patch(SEND_REQUEST) as mock_send, patch(SLEEP):
        mock_send.side_effect = [
            ServiceError("bad gateway", status_code=502),
            ServiceError("bad gateway", status_code=502),
            _body("running"),
            ServiceError("bad gateway", status_code=502),
            ServiceError("bad gateway", status_code=502),
            _body("completed"),
        ]
        api = AutoGraphApi(communication=placeholder_communication)

        result = _poll(
            lambda: api.get_corpus_build_status(service_path=SERVICE_PATH, build_id="build-1"),
            job_id="build-1",
            timeout=None,
            poll_interval=1.0,
        )

    assert result.status == "completed"


def test_wait_for_job_raises_after_too_many_poll_errors_in_a_row(
    placeholder_communication: Communication,
):
    last = ServiceError("bad gateway", status_code=502)
    with patch(SEND_REQUEST) as mock_send, patch(SLEEP):
        mock_send.side_effect = [
            ServiceError("bad gateway", status_code=502),
            ServiceError("bad gateway", status_code=502),
            last,
        ]
        api = AutoGraphApi(communication=placeholder_communication)

        with pytest.raises(ServiceError) as exc_info:
            _poll(
                lambda: api.get_corpus_build_status(service_path=SERVICE_PATH, build_id="build-1"),
                job_id="build-1",
                timeout=None,
                poll_interval=1.0,
            )

    assert exc_info.value is last
    assert mock_send.call_count == 3


def test_wait_for_job_raises_timeout_when_the_deadline_passes(
    placeholder_communication: Communication,
):
    with (
        patch(SEND_REQUEST) as mock_send,
        patch(SLEEP),
        patch(MONOTONIC) as mock_monotonic,
    ):
        mock_send.return_value = _body("running")
        # Start, after the first poll (within the bound), after the second (past it).
        mock_monotonic.side_effect = [0.0, 1.0, 3.0]
        api = AutoGraphApi(communication=placeholder_communication)

        with pytest.raises(JobTimeoutError):
            _poll(
                lambda: api.get_corpus_build_status(service_path=SERVICE_PATH, build_id="build-1"),
                job_id="build-1",
                timeout=2.0,
                poll_interval=1.0,
            )

    assert mock_send.call_count == 2


def _status(state: str, **fields) -> GetBuildStatusResponse:
    return GetBuildStatusResponse(corpus_build_id="build-1", status=state, **fields)


def test_corpus_build_starts_the_build_and_polls_until_completed(
    placeholder_communication: Communication,
):
    progress: list[GetBuildStatusResponse] = []
    with (
        patch(REFRESH) as mock_refresh,
        patch(START_BUILD) as mock_start,
        patch(BUILD_STATUS) as mock_status,
        patch(SLEEP) as mock_sleep,
    ):
        mock_refresh.return_value = _project(deployed=True)
        mock_start.return_value = CreateCorpusBuildResponse(corpus_build_id="build-1")
        mock_status.side_effect = [
            _status("running", progress=50),
            _status("completed"),
        ]
        sales = AiProjectHandle(
            ai_project=_project(deployed=True), communication=placeholder_communication
        )

        result = sales.autograph.corpus_build(
            ["finance"],
            incremental=True,
            top_k=5,
            poll_interval=2.0,
            on_progress=progress.append,
        )

    assert result.status == "completed"
    request = mock_start.call_args.kwargs["request"]
    assert mock_start.call_args.kwargs["service_path"] == "/autograph/c-123"
    assert request.categories == ["finance"]
    assert request.incremental is True
    assert request.strategy == BuildStrategy(top_k=5)
    mock_status.assert_called_with(service_path="/autograph/c-123", build_id="build-1")
    assert [status.status for status in progress] == ["running", "completed"]
    mock_sleep.assert_called_once_with(2.0)


def test_corpus_build_leaves_the_strategy_out_when_no_tuning_is_given(
    placeholder_communication: Communication,
):
    with (
        patch(REFRESH) as mock_refresh,
        patch(START_BUILD) as mock_start,
        patch(BUILD_STATUS) as mock_status,
    ):
        mock_refresh.return_value = _project(deployed=True)
        mock_start.return_value = CreateCorpusBuildResponse(corpus_build_id="build-1")
        mock_status.return_value = _status("completed")
        sales = AiProjectHandle(
            ai_project=_project(deployed=True), communication=placeholder_communication
        )

        sales.autograph.corpus_build(["finance"])

    assert mock_start.call_args.kwargs["request"].strategy is None


def test_corpus_build_rejects_empty_categories_without_sending(
    placeholder_communication: Communication,
):
    with patch(REFRESH) as mock_refresh, patch(START_BUILD) as mock_start:
        sales = AiProjectHandle(
            ai_project=_project(deployed=True), communication=placeholder_communication
        )

        with pytest.raises(ValueError):
            sales.autograph.corpus_build([])

    mock_refresh.assert_not_called()
    mock_start.assert_not_called()


def test_corpus_build_raises_not_deployed_without_sending(
    placeholder_communication: Communication,
):
    with patch(REFRESH) as mock_refresh, patch(START_BUILD) as mock_start:
        mock_refresh.return_value = _project(deployed=False)
        sales = AiProjectHandle(
            ai_project=_project(deployed=False), communication=placeholder_communication
        )

        with pytest.raises(AutoGraphNotDeployedError):
            sales.autograph.corpus_build(["finance"])

    mock_start.assert_not_called()


def test_corpus_build_raises_ingestion_failed_with_the_final_status(
    placeholder_communication: Communication,
):
    failed = _status("failed", error="embedding provider rejected the key")
    with (
        patch(REFRESH) as mock_refresh,
        patch(START_BUILD) as mock_start,
        patch(BUILD_STATUS) as mock_status,
    ):
        mock_refresh.return_value = _project(deployed=True)
        mock_start.return_value = CreateCorpusBuildResponse(corpus_build_id="build-1")
        mock_status.return_value = failed
        sales = AiProjectHandle(
            ai_project=_project(deployed=True), communication=placeholder_communication
        )

        with pytest.raises(IngestionFailedError) as exc_info:
            sales.autograph.corpus_build(["finance"])

    assert exc_info.value.job_status is failed


def test_corpus_build_returns_a_partial_success_and_logs_a_warning(
    placeholder_communication: Communication, caplog: pytest.LogCaptureFixture
):
    with (
        patch(REFRESH) as mock_refresh,
        patch(START_BUILD) as mock_start,
        patch(BUILD_STATUS) as mock_status,
    ):
        mock_refresh.return_value = _project(deployed=True)
        mock_start.return_value = CreateCorpusBuildResponse(corpus_build_id="build-1")
        mock_status.return_value = _status("completed", error_code="PARTIAL")
        sales = AiProjectHandle(
            ai_project=_project(deployed=True), communication=placeholder_communication
        )

        with caplog.at_level("WARNING", logger="arango_ai_sdk.autograph"):
            result = sales.autograph.corpus_build(["finance"])

    assert result.error_code == "PARTIAL"
    assert "PARTIAL" in caplog.text


def test_corpus_build_raises_status_lost_on_404_after_a_status(
    placeholder_communication: Communication,
):
    with (
        patch(REFRESH) as mock_refresh,
        patch(START_BUILD) as mock_start,
        patch(BUILD_STATUS) as mock_status,
        patch(SLEEP),
    ):
        mock_refresh.return_value = _project(deployed=True)
        mock_start.return_value = CreateCorpusBuildResponse(corpus_build_id="build-1")
        mock_status.side_effect = [
            _status("running"),
            ServiceError("Requested endpoint does not exist.", status_code=404),
        ]
        sales = AiProjectHandle(
            ai_project=_project(deployed=True), communication=placeholder_communication
        )

        with pytest.raises(JobStatusLostError) as exc_info:
            sales.autograph.corpus_build(["finance"])

    assert exc_info.value.job_id == "build-1"


def test_corpus_build_survives_poll_errors_below_the_limit(
    placeholder_communication: Communication,
):
    with (
        patch(REFRESH) as mock_refresh,
        patch(START_BUILD) as mock_start,
        patch(BUILD_STATUS) as mock_status,
        patch(SLEEP),
    ):
        mock_refresh.return_value = _project(deployed=True)
        mock_start.return_value = CreateCorpusBuildResponse(corpus_build_id="build-1")
        mock_status.side_effect = [
            ServiceError("bad gateway", status_code=502),
            ServiceError("bad gateway", status_code=502),
            _status("completed"),
        ]
        sales = AiProjectHandle(
            ai_project=_project(deployed=True), communication=placeholder_communication
        )

        result = sales.autograph.corpus_build(["finance"])

    assert result.status == "completed"


def test_corpus_build_raises_after_too_many_poll_errors_in_a_row(
    placeholder_communication: Communication,
):
    last = ServiceError("bad gateway", status_code=502)
    with (
        patch(REFRESH) as mock_refresh,
        patch(START_BUILD) as mock_start,
        patch(BUILD_STATUS) as mock_status,
        patch(SLEEP),
    ):
        mock_refresh.return_value = _project(deployed=True)
        mock_start.return_value = CreateCorpusBuildResponse(corpus_build_id="build-1")
        mock_status.side_effect = [
            ServiceError("bad gateway", status_code=502),
            ServiceError("bad gateway", status_code=502),
            last,
        ]
        sales = AiProjectHandle(
            ai_project=_project(deployed=True), communication=placeholder_communication
        )

        with pytest.raises(ServiceError) as exc_info:
            sales.autograph.corpus_build(["finance"])

    assert exc_info.value is last
    assert mock_status.call_count == 3


def test_corpus_build_raises_timeout_when_the_deadline_passes(
    placeholder_communication: Communication,
):
    with (
        patch(REFRESH) as mock_refresh,
        patch(START_BUILD) as mock_start,
        patch(BUILD_STATUS) as mock_status,
        patch(SLEEP),
        patch(MONOTONIC) as mock_monotonic,
    ):
        mock_refresh.return_value = _project(deployed=True)
        mock_start.return_value = CreateCorpusBuildResponse(corpus_build_id="build-1")
        mock_status.return_value = _status("running")
        # Start, after the first poll (within the bound), after the second (past it).
        mock_monotonic.side_effect = [0.0, 1.0, 3.0]
        sales = AiProjectHandle(
            ai_project=_project(deployed=True), communication=placeholder_communication
        )

        with pytest.raises(JobTimeoutError):
            sales.autograph.corpus_build(["finance"], timeout=2.0, poll_interval=1.0)

    assert mock_status.call_count == 2


def _job(state: str, **fields) -> GetRagStrategizerJobStatusResponse:
    return GetRagStrategizerJobStatusResponse(status=state, **fields)


def test_strategize_starts_the_run_and_polls_until_completed(
    placeholder_communication: Communication,
):
    progress: list[GetRagStrategizerJobStatusResponse] = []
    with (
        patch(REFRESH) as mock_refresh,
        patch(START_STRATEGIZER) as mock_start,
        patch(STRATEGIZER_STATUS) as mock_status,
        patch(SLEEP) as mock_sleep,
    ):
        mock_refresh.return_value = _project(deployed=True)
        mock_start.return_value = TriggerRagStrategizerResponse(strategize_job_id="job-1")
        mock_status.side_effect = [
            _job("running", progress=0.4),
            _job("completed", progress=1.0),
        ]
        sales = AiProjectHandle(
            ai_project=_project(deployed=True), communication=placeholder_communication
        )

        result = sales.autograph.strategize(
            ["finance"],
            extract_images_default=True,
            max_parallel_clusters=3,
            poll_interval=2.0,
            on_progress=progress.append,
        )

    assert result.status == "completed"
    request = mock_start.call_args.kwargs["request"]
    assert mock_start.call_args.kwargs["service_path"] == "/autograph/c-123"
    assert request.project == "sales"
    assert request.categories == ["finance"]
    assert request.complexity == RagStrategizerComplexity.high
    assert request.extract_images_default is True
    assert request.max_parallel_clusters == 3
    mock_status.assert_called_with(service_path="/autograph/c-123", job_id="job-1")
    assert [status.status for status in progress] == ["running", "completed"]
    mock_sleep.assert_called_once_with(2.0)


def test_strategize_rejects_empty_categories_without_sending(
    placeholder_communication: Communication,
):
    with patch(REFRESH) as mock_refresh, patch(START_STRATEGIZER) as mock_start:
        sales = AiProjectHandle(
            ai_project=_project(deployed=True), communication=placeholder_communication
        )

        with pytest.raises(ValueError):
            sales.autograph.strategize([])

    mock_refresh.assert_not_called()
    mock_start.assert_not_called()


def test_strategize_raises_not_deployed_without_sending(
    placeholder_communication: Communication,
):
    with patch(REFRESH) as mock_refresh, patch(START_STRATEGIZER) as mock_start:
        mock_refresh.return_value = _project(deployed=False)
        sales = AiProjectHandle(
            ai_project=_project(deployed=False), communication=placeholder_communication
        )

        with pytest.raises(AutoGraphNotDeployedError):
            sales.autograph.strategize(["finance"])

    mock_start.assert_not_called()


def test_strategize_raises_ingestion_failed_with_the_final_status(
    placeholder_communication: Communication,
):
    failed = _job("failed")
    with (
        patch(REFRESH) as mock_refresh,
        patch(START_STRATEGIZER) as mock_start,
        patch(STRATEGIZER_STATUS) as mock_status,
    ):
        mock_refresh.return_value = _project(deployed=True)
        mock_start.return_value = TriggerRagStrategizerResponse(strategize_job_id="job-1")
        mock_status.return_value = failed
        sales = AiProjectHandle(
            ai_project=_project(deployed=True), communication=placeholder_communication
        )

        with pytest.raises(IngestionFailedError) as exc_info:
            sales.autograph.strategize(["finance"])

    assert exc_info.value.job_status is failed


def test_strategies_returns_the_stored_list(
    placeholder_communication: Communication,
):
    stored = GetRagStrategizerStrategyResponse(total_strategies=1)
    with patch(REFRESH) as mock_refresh, patch(GET_STRATEGIES) as mock_get:
        mock_refresh.return_value = _project(deployed=True)
        mock_get.return_value = stored
        sales = AiProjectHandle(
            ai_project=_project(deployed=True), communication=placeholder_communication
        )

        result = sales.autograph.strategies()

    assert result is stored
    mock_get.assert_called_once_with(service_path="/autograph/c-123")


def test_strategies_raises_not_deployed_without_sending(
    placeholder_communication: Communication,
):
    with patch(REFRESH) as mock_refresh, patch(GET_STRATEGIES) as mock_get:
        mock_refresh.return_value = _project(deployed=False)
        sales = AiProjectHandle(
            ai_project=_project(deployed=False), communication=placeholder_communication
        )

        with pytest.raises(AutoGraphNotDeployedError):
            sales.autograph.strategies()

    mock_get.assert_not_called()


def _project_with_secrets(project: AiProject) -> AiProject:
    project.model_settings = AutoGraphModelSettings(
        chat_secret_profile_id="chat-secret",
        embedding_secret_profile_id="embed-secret",
    )
    return project


def _orchestrate_response_sample(state: str, **fields) -> GetOrchestrationStatusResponse:
    return GetOrchestrationStatusResponse(orchestration_id="orch-1", status=state, **fields)


def test_orchestrate_rejects_empty_categories_without_sending(
    placeholder_communication: Communication,
):
    with patch(REFRESH) as mock_refresh, patch(START_ORCHESTRATION) as mock_start:
        sales = AiProjectHandle(
            ai_project=_project(deployed=True), communication=placeholder_communication
        )

        with pytest.raises(ValueError, match="categories must name at least one category"):
            sales.autograph.orchestrate([])

    mock_refresh.assert_not_called()
    mock_start.assert_not_called()


def test_orchestrate_raises_not_deployed_without_sending(
    placeholder_communication: Communication,
):
    with patch(REFRESH), patch(START_ORCHESTRATION) as mock_start:
        sales = AiProjectHandle(
            ai_project=_project(deployed=False), communication=placeholder_communication
        )

        with pytest.raises(AutoGraphNotDeployedError):
            sales.autograph.orchestrate(["finance"])

    mock_start.assert_not_called()


def test_orchestrate_raises_when_secret_ids_are_missing(
    placeholder_communication: Communication,
):
    with patch(REFRESH), patch(START_ORCHESTRATION) as mock_start:
        sales = AiProjectHandle(
            ai_project=_project(deployed=True), communication=placeholder_communication
        )

        with pytest.raises(ServiceError):
            sales.autograph.orchestrate(["finance"])

    mock_start.assert_not_called()


def test_orchestrate_does_not_poll_when_nothing_is_stale(
    placeholder_communication: Communication,
):
    with (
        patch(REFRESH),
        patch(START_ORCHESTRATION) as mock_start,
        patch(ORCHESTRATION_STATUS) as mock_status,
    ):
        mock_start.return_value = None
        sales = AiProjectHandle(
            ai_project=_project_with_secrets(_project(deployed=True)),
            communication=placeholder_communication,
        )

        assert sales.autograph.orchestrate(["finance"]) is None

    mock_status.assert_not_called()


def test_orchestrate_polls_until_completed(
    placeholder_communication: Communication,
):
    progress: list[GetOrchestrationStatusResponse] = []
    with (
        patch(REFRESH) as mock_refresh,
        patch(START_ORCHESTRATION) as mock_start,
        patch(ORCHESTRATION_STATUS) as mock_status,
        patch(SLEEP) as mock_sleep,
    ):
        mock_refresh.return_value = _project_with_secrets(_project(deployed=True))
        mock_start.return_value = TriggerOrchestrationResponse(orchestration_id="orch-1")
        mock_status.side_effect = [
            _orchestrate_response_sample(JobState.RUNNING, phase=OrchestrationPhase.IMPORTING),
            _orchestrate_response_sample(JobState.COMPLETED, phase=OrchestrationPhase.FINISHED),
        ]
        sales = AiProjectHandle(
            ai_project=_project_with_secrets(_project(deployed=True)),
            communication=placeholder_communication,
        )

        result = sales.autograph.orchestrate(
            ["finance"], poll_interval=2.0, on_progress=progress.append
        )

    assert result is not None
    assert result.status == "completed"
    request = mock_start.call_args.kwargs["request"]
    assert request.project == "sales"
    assert request.categories == ["finance"]
    assert request.chat_secret_profile_ids == ["chat-secret"]
    assert request.embedding_secret_profile_id == "embed-secret"
    assert request.file_ids == []
    assert [status.status for status in progress] == ["running", "completed"]
    mock_sleep.assert_called_once_with(2.0)


def test_orchestrate_raises_ingestion_failed_when_cancelled(
    placeholder_communication: Communication,
):
    cancelled = _orchestrate_response_sample("cancelled")
    with (
        patch(REFRESH) as mock_refresh,
        patch(START_ORCHESTRATION) as mock_start,
        patch(ORCHESTRATION_STATUS) as mock_status,
    ):
        mock_refresh.return_value = _project_with_secrets(_project(deployed=True))
        mock_start.return_value = TriggerOrchestrationResponse(orchestration_id="orch-1")
        mock_status.return_value = cancelled
        sales = AiProjectHandle(
            ai_project=_project_with_secrets(_project(deployed=True)),
            communication=placeholder_communication,
        )

        with pytest.raises(IngestionFailedError) as exc_info:
            sales.autograph.orchestrate(["finance"])

    assert exc_info.value.job_status is cancelled


def _sales(placeholder_communication: Communication) -> AiProjectHandle:
    return AiProjectHandle(
        ai_project=_project(deployed=True),
        communication=placeholder_communication,
    )


def test_ingest_rejects_empty_categories_before_any_step(
    placeholder_communication: Communication,
):
    with (
        patch(CORPUS_BUILD) as mock_build,
        patch(STRATEGIZE) as mock_strategize,
        patch(STRATEGIES) as mock_strategies,
        patch(ORCHESTRATE) as mock_orchestrate,
        pytest.raises(ValueError, match="categories must name at least one category"),
    ):
        _sales(placeholder_communication).autograph.ingest([])

    mock_build.assert_not_called()
    mock_strategize.assert_not_called()
    mock_strategies.assert_not_called()
    mock_orchestrate.assert_not_called()


def test_ingest_runs_the_steps_in_order_and_reports_progress(
    placeholder_communication: Communication,
):
    build = _status("completed")
    strategize_status = GetRagStrategizerJobStatusResponse(status="completed")
    strategies = GetRagStrategizerStrategyResponse(total_strategies=1)
    orchestration = _orchestrate_response_sample("completed")
    order: list[str] = []
    seen: list[IngestProgress] = []

    def fake_build(categories, *, incremental, timeout, poll_interval, on_progress):
        order.append("build")
        assert categories == ["finance"]
        assert incremental is False
        assert timeout is None
        assert poll_interval == 30.0
        on_progress(build)
        return build

    def fake_strategize(categories, *, complexity, timeout, poll_interval, on_progress):
        order.append("strategize")
        assert categories == ["finance"]
        assert complexity is RagStrategizerComplexity.high
        assert timeout is None
        on_progress(strategize_status)
        return strategize_status

    def fake_strategies():
        order.append("strategies")
        return strategies

    def fake_orchestrate(categories, *, timeout, poll_interval, on_progress):
        order.append("orchestrate")
        assert categories == ["finance"]
        assert timeout is None
        on_progress(orchestration)
        return orchestration

    with (
        patch(CORPUS_BUILD, side_effect=fake_build),
        patch(STRATEGIZE, side_effect=fake_strategize),
        patch(STRATEGIES, side_effect=fake_strategies),
        patch(ORCHESTRATE, side_effect=fake_orchestrate),
    ):
        result = _sales(placeholder_communication).autograph.ingest(
            ["finance"], on_progress=seen.append
        )

    assert order == ["build", "strategize", "strategies", "orchestrate"]
    assert isinstance(result, IngestResult)
    assert result.build is build
    assert result.strategize is strategize_status
    assert result.strategies is strategies
    assert result.orchestration is orchestration
    assert [(item.step, item.status) for item in seen] == [
        ("build", build),
        ("strategize", strategize_status),
        ("orchestrate", orchestration),
    ]


def test_ingest_returns_when_orchestration_has_nothing_stale(
    placeholder_communication: Communication,
):
    build = _status("completed")
    strategize_status = GetRagStrategizerJobStatusResponse(status="completed")
    strategies = GetRagStrategizerStrategyResponse(total_strategies=1)
    with (
        patch(CORPUS_BUILD, return_value=build),
        patch(STRATEGIZE, return_value=strategize_status),
        patch(STRATEGIES, return_value=strategies),
        patch(ORCHESTRATE, return_value=None) as mock_orchestrate,
    ):
        result = _sales(placeholder_communication).autograph.ingest(["finance"])

    mock_orchestrate.assert_called_once()
    assert result.build is build
    assert result.strategize is strategize_status
    assert result.strategies is strategies
    assert result.orchestration is None


def test_ingest_stops_when_strategize_fails(placeholder_communication: Communication):
    failed = GetRagStrategizerJobStatusResponse(status="failed")
    with (
        patch(CORPUS_BUILD, return_value=_status("completed")) as mock_build,
        patch(
            STRATEGIZE,
            side_effect=IngestionFailedError("Job strat-1 ended as failed.", job_status=failed),
        ),
        patch(STRATEGIES) as mock_strategies,
        patch(ORCHESTRATE) as mock_orchestrate,
        pytest.raises(IngestionFailedError) as exc_info,
    ):
        _sales(placeholder_communication).autograph.ingest(["finance"])

    assert exc_info.value.job_status is failed
    mock_build.assert_called_once()
    mock_strategies.assert_not_called()
    mock_orchestrate.assert_not_called()


def test_ingest_does_not_strategize_when_the_deadline_is_spent(
    placeholder_communication: Communication,
):
    with (
        patch(MONOTONIC, side_effect=[0.0, 0.0, 30.0]),
        patch(CORPUS_BUILD, return_value=_status("completed")) as mock_build,
        patch(STRATEGIZE) as mock_strategize,
        patch(STRATEGIES) as mock_strategies,
        patch(ORCHESTRATE) as mock_orchestrate,
        pytest.raises(JobTimeoutError, match="Ingest did not finish within 10 seconds"),
    ):
        _sales(placeholder_communication).autograph.ingest(["finance"], timeout=10)

    mock_build.assert_called_once()
    assert mock_build.call_args.kwargs["timeout"] == 10
    mock_strategize.assert_not_called()
    mock_strategies.assert_not_called()
    mock_orchestrate.assert_not_called()
