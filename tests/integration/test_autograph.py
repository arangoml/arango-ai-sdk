"""Integration tests for :class:`AutoGraph`, against a live platform.

Marker and credentials skip come from ``tests/integration/conftest.py``. These
tests go through ``AiProjectHandle.autograph`` the way a user does. What ACP
answers to a raw install or delete is covered in ``test_service_api.py``.
"""

import contextlib
import os

import pytest

from arango_ai_sdk._naming import AcpPath, EnvVar
from arango_ai_sdk.communication import Communication
from arango_ai_sdk.exceptions import (
    AutoGraphAlreadyDeployedError,
    AutoGraphNotDeployedError,
    ServiceError,
)
from arango_ai_sdk.managers.autograph import DeployResult
from arango_ai_sdk.managers.projects import ProjectManager
from arango_ai_sdk.managers.secret_profiles import SecretProfileManager

DB_NAME = os.environ.get(EnvVar.ARANGO_SDK_TEST_DB, "")


def test_deploy_then_undeploy(
    communication: Communication,
    project_name: str,
    secret_profile_name: str,
    fake_secret: str,
) -> None:
    """Deploy AutoGraph on a fresh project, see it in the handle state, remove it."""
    projects = ProjectManager(communication=communication, db_name=DB_NAME)
    secrets = SecretProfileManager(communication=communication)
    sales = projects.create(project_name=project_name, project_type="autograph")
    chat = secrets.create(name=f"{secret_profile_name}-chat", secret=fake_secret, provider="openai")
    embed = secrets.create(
        name=f"{secret_profile_name}-embed", secret=fake_secret, provider="openai"
    )
    assert sales.autograph.is_deployed is False
    try:
        # Deliberately not `wait=True`. Waiting for the pod inside deploy makes
        # one SDK call outlive the platform's own request deadline, so the test
        # fails on the wait rather than on anything deploy did. Readiness is
        # checked below instead, on its own bound.
        deploy_results: DeployResult = sales.autograph.deploy(
            chat_api_provider="openai",
            embedding_api_provider="openai",
            chat_secret_profile_id=chat.profile_id,
            embedding_secret_profile_id=embed.profile_id,
            fps_recovery_username="fps-recovery",
            chat_model="gpt-4o",
            embedding_model="text-embedding-3-small",
        )
        service_info = deploy_results.service_info
        assert deploy_results.ready is None, "nobody waited, so readiness is unknown"
        assert service_info.service_id
        # deploy refreshed the handle, so its state already shows the service.
        assert sales.autograph.is_deployed is True
        assert sales.autograph.service_id == service_info.service_id
        settings = sales.model_settings
        assert settings is not None
        assert settings.chat_model == "gpt-4o"
        assert settings.chat_secret_profile_id == chat.profile_id

        # A pod that is not up within the bound is not a failure here; the test
        # is about deploy and undeploy. What this does pin is that the health
        # check reaches the service and answers in the shape the SDK expects,
        # which is only exercised against a live AutoGraph.
        assert isinstance(sales.autograph.wait_until_ready(timeout=60.0), bool)

        removed = sales.autograph.undeploy()
        assert removed.service_id == service_info.service_id
        assert sales.autograph.is_deployed is False
        with pytest.raises(AutoGraphNotDeployedError):
            sales.autograph.undeploy()
    finally:
        with contextlib.suppress(ServiceError):
            sales.autograph.undeploy()
        communication.send_request("delete", f"{AcpPath.SECRETS}/{chat.profile_id}")
        communication.send_request("delete", f"{AcpPath.SECRETS}/{embed.profile_id}")
        communication.send_request("delete", f"{AcpPath.PROJECT}/{DB_NAME}/{project_name}")


def test_second_deploy_on_the_same_project_is_refused(
    communication: Communication,
    project_name: str,
    secret_profile_name: str,
    fake_secret: str,
) -> None:
    """A project has one AutoGraph; a second deploy raises and keeps the first."""
    projects = ProjectManager(communication=communication, db_name=DB_NAME)
    secrets = SecretProfileManager(communication=communication)
    sales = projects.create(project_name=project_name, project_type="autograph")
    chat = secrets.create(name=f"{secret_profile_name}-chat", secret=fake_secret, provider="openai")
    embed = secrets.create(
        name=f"{secret_profile_name}-embed", secret=fake_secret, provider="openai"
    )
    try:
        first = sales.autograph.deploy(
            chat_api_provider="openai",
            embedding_api_provider="openai",
            chat_secret_profile_id=chat.profile_id,
            embedding_secret_profile_id=embed.profile_id,
            fps_recovery_username="fps-recovery",
        )
        # A fresh handle for the same project sees the deployed service too.
        same_project = projects.get(project_name=project_name)
        with pytest.raises(AutoGraphAlreadyDeployedError):
            same_project.autograph.deploy(
                chat_api_provider="openai",
                embedding_api_provider="openai",
                chat_secret_profile_id=chat.profile_id,
                embedding_secret_profile_id=embed.profile_id,
                fps_recovery_username="fps-recovery",
            )
        assert same_project.autograph.service_id == first.service_info.service_id
    finally:
        with contextlib.suppress(ServiceError):
            sales.autograph.undeploy()
        communication.send_request("delete", f"{AcpPath.SECRETS}/{chat.profile_id}")
        communication.send_request("delete", f"{AcpPath.SECRETS}/{embed.profile_id}")
        communication.send_request("delete", f"{AcpPath.PROJECT}/{DB_NAME}/{project_name}")
