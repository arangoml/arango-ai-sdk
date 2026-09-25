"""Unit tests for :class:`AutoGraph`; no platform needed.

``AiProjectHandle.refresh`` stands in for the platform's view of the project
and ``ServiceApi.deploy_service`` for ACP's answer, so the tests check
what ``AutoGraph`` decides and sends, not what the platform does.
"""

from unittest.mock import patch

import pytest

from arango_ai_sdk._naming import AcpPath, AutoGraphInstallParams
from arango_ai_sdk.communication import Communication
from arango_ai_sdk.exceptions import (
    AutoGraphAlreadyDeployedError,
    AutoGraphNotDeployedError,
    AutoGraphUnavailableError,
    InvalidServiceParametersError,
    PlatformUnreachableError,
    ProjectNotFoundError,
    ServiceError,
    ServiceNotFoundError,
)
from arango_ai_sdk.models import (
    AiProject,
    AutoGraphService,
    GraphRagProjectMetaData,
    HealthCheckResponse,
    ServiceInfo,
)
from arango_ai_sdk.project_handle import AiProjectHandle

REFRESH = "arango_ai_sdk.project_handle.AiProjectHandle.refresh"
GET_PROJECT = "arango_ai_sdk.project_handle.get_project"
DEPLOY_SERVICE = "arango_ai_sdk._service_api.ServiceApi.deploy_service"
DELETE = "arango_ai_sdk._service_api.ServiceApi.delete"
HEALTH = "arango_ai_sdk._autograph_api.AutoGraphApi.health"
SEND_REQUEST = "arango_ai_sdk.communication.Communication.send_request"
WAIT_UNTIL_READY = "arango_ai_sdk.autograph.AutoGraph.wait_until_ready"
SLEEP = "time.sleep"
MONOTONIC = "time.monotonic"


def _deploy(sales: AiProjectHandle, chat_api_provider: str = "openai") -> ServiceInfo:
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

    assert result.service_id == "svc-123"
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


def test_deploy_without_wait_does_not_check_health(
    placeholder_communication: Communication,
):
    with (
        patch(REFRESH) as mock_refresh,
        patch(DEPLOY_SERVICE) as mock_deploy,
        patch(WAIT_UNTIL_READY) as mock_wait,
    ):
        mock_refresh.return_value = _project(deployed=False)
        mock_deploy.return_value = ServiceInfo(service_id="svc-123")
        sales = AiProjectHandle(
            ai_project=_project(deployed=False), communication=placeholder_communication
        )

        result = _deploy(sales)

    assert result.service_id == "svc-123"
    mock_wait.assert_not_called()


def test_deploy_with_wait_checks_health_and_returns_the_service(
    placeholder_communication: Communication,
):
    with (
        patch(REFRESH) as mock_refresh,
        patch(DEPLOY_SERVICE) as mock_deploy,
        patch(WAIT_UNTIL_READY) as mock_wait,
    ):
        mock_refresh.return_value = _project(deployed=False)
        mock_deploy.return_value = ServiceInfo(service_id="svc-123")
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

    assert result.service_id == "svc-123"
    mock_wait.assert_called_once_with()


def test_deploy_with_wait_raises_when_the_service_does_not_come_up(
    placeholder_communication: Communication,
):
    """The install is done; the wait's own error is what the caller sees."""
    with (
        patch(REFRESH) as mock_refresh,
        patch(DEPLOY_SERVICE) as mock_deploy,
        patch(WAIT_UNTIL_READY) as mock_wait,
    ):
        mock_refresh.return_value = _project(deployed=False)
        mock_deploy.return_value = ServiceInfo(service_id="svc-123")
        mock_wait.side_effect = AutoGraphUnavailableError("no answer")
        sales = AiProjectHandle(
            ai_project=_project(deployed=False), communication=placeholder_communication
        )

        with pytest.raises(AutoGraphUnavailableError):
            sales.autograph.deploy(
                chat_api_provider="openai",
                embedding_api_provider="openai",
                chat_secret_profile_id="chat-secret",
                embedding_secret_profile_id="embed-secret",
                fps_recovery_username="fps-recovery",
                wait=True,
            )

    mock_deploy.assert_called_once()


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


def test_wait_until_ready_raises_unavailable_when_the_bound_passes(
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

        with pytest.raises(AutoGraphUnavailableError, match="NOT_SERVING"):
            sales.autograph.wait_until_ready(timeout=2.0, poll_interval=1.0)

    assert mock_health.call_count == 2
    mock_health.assert_called_with(service_path="/autograph/c-123")
    mock_sleep.assert_called_once_with(1.0)


def test_wait_until_ready_returns_once_healthy(
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

        sales.autograph.wait_until_ready(timeout=2.0, poll_interval=1.0)

    mock_health.assert_called_once_with(service_path="/autograph/c-123")
    mock_sleep.assert_not_called()


def test_wait_until_ready_keeps_polling_while_the_service_is_coming_up(
    placeholder_communication: Communication,
) -> None:
    """No route yet, no pod behind it yet, gateway unreachable: all count as not ready.

    Patched at ``send_request``, so the health body goes through the real
    conversion into ``HealthCheckResponse``.
    """
    sales = AiProjectHandle(
        ai_project=_project(deployed=True), communication=placeholder_communication
    )
    with (
        patch(GET_PROJECT, return_value=_project(deployed=True)),
        patch(SEND_REQUEST) as mock_send,
        patch(SLEEP) as mock_sleep,
    ):
        mock_send.side_effect = [
            ServiceError(
                "Requested endpoint: /autograph/c-123/v1/health does not exist.", status_code=404
            ),
            ServiceError("upstream connect error", status_code=503),
            PlatformUnreachableError("GET /autograph/c-123/v1/health did not get through"),
            {"status": "SERVING", "message": "Service is healthy"},
        ]

        sales.autograph.wait_until_ready(timeout=60.0, poll_interval=1.0)

    assert mock_send.call_count == 4
    assert mock_sleep.call_count == 3


def test_wait_until_ready_raises_an_error_answer_that_is_not_a_startup_sign(
    placeholder_communication: Communication,
) -> None:
    """A 403 is a rejection, not a pod coming up: it is raised, not waited out."""
    sales = AiProjectHandle(
        ai_project=_project(deployed=True), communication=placeholder_communication
    )
    with (
        patch(GET_PROJECT, return_value=_project(deployed=True)),
        patch(SEND_REQUEST) as mock_send,
        patch(SLEEP) as mock_sleep,
    ):
        mock_send.side_effect = ServiceError("forbidden", status_code=403)

        with pytest.raises(ServiceError) as excinfo:
            sales.autograph.wait_until_ready(timeout=60.0, poll_interval=1.0)

    assert excinfo.value.status_code == 403
    mock_send.assert_called_once()
    mock_sleep.assert_not_called()
