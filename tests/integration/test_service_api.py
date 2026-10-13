"""Integration tests for :class:`ServiceApi`, against a live platform.

Marker and credentials skip come from ``tests/integration/conftest.py``. These
tests call ``deploy_service`` and ``delete`` directly, so they check what ACP
really answers and that the unit-tested translations match it. Anything
specific to AutoGraph belongs in ``test_autograph.py``.
"""

import os

import pytest

from arango_ai_sdk._naming import AcpPath, AutoGraphInstallParams, EnvVar
from arango_ai_sdk.api._service_api import ServiceApi
from arango_ai_sdk.communication import Communication
from arango_ai_sdk.exceptions import ProjectNotFoundError, ServiceNotFoundError
from arango_ai_sdk.managers.projects import ProjectManager
from arango_ai_sdk.managers.secret_profiles import SecretProfileManager
from arango_ai_sdk.models import CreateEntityRequest

DB_NAME = os.environ.get(EnvVar.ARANGO_SDK_TEST_DB, "")


def test_delete_unknown_id_raises_service_not_found(
    communication: Communication,
) -> None:
    """An id ACP does not know is a named not-found error."""
    with pytest.raises(ServiceNotFoundError, match="not found"):
        ServiceApi(communication=communication).delete(service_id="no-such-service-id")


def test_deploy_service_for_a_missing_project_raises_project_not_found(
    communication: Communication,
) -> None:
    """ACP answers a 400 whose message names the missing project; the SDK maps it.

    This is the live check behind TODO(AIS-2208) in ``_service_api.py``.
    """
    request = CreateEntityRequest(
        env={
            AutoGraphInstallParams.GENAI_PROJECT_NAME: "no_such_sdk_project",
            AutoGraphInstallParams.DB_NAME: DB_NAME,
            AutoGraphInstallParams.CHAT_API_PROVIDER: "openai",
            AutoGraphInstallParams.EMBEDDING_API_PROVIDER: "openai",
            AutoGraphInstallParams.CHAT_SECRET_PROFILE_ID: "no-such-chat",
            AutoGraphInstallParams.EMBEDDING_SECRET_PROFILE_ID: "no-such-embed",
            AutoGraphInstallParams.FPS_RECOVERY_USERNAME: "fps-recovery",
        }
    )
    with pytest.raises(ProjectNotFoundError, match="no_such_sdk_project"):
        ServiceApi(communication=communication).deploy_service(
            install_path=AcpPath.AUTOGRAPH, request=request
        )


def test_deploy_service_then_delete(
    communication: Communication,
    project_name: str,
    secret_profile_name: str,
    fake_secret: str,
) -> None:
    """Install AutoGraph for an existing project through ACP, then delete it."""
    projects = ProjectManager(communication=communication, db_name=DB_NAME)
    secrets = SecretProfileManager(communication=communication)
    services = ServiceApi(communication=communication)
    projects.create(project_name=project_name, project_type="autograph")
    chat = secrets.create(name=f"{secret_profile_name}-chat", secret=fake_secret, provider="openai")
    embed = secrets.create(
        name=f"{secret_profile_name}-embed", secret=fake_secret, provider="openai"
    )
    request = CreateEntityRequest(
        env={
            AutoGraphInstallParams.GENAI_PROJECT_NAME: project_name,
            AutoGraphInstallParams.DB_NAME: DB_NAME,
            AutoGraphInstallParams.CHAT_API_PROVIDER: "openai",
            AutoGraphInstallParams.EMBEDDING_API_PROVIDER: "openai",
            AutoGraphInstallParams.CHAT_SECRET_PROFILE_ID: chat.profile_id,
            AutoGraphInstallParams.EMBEDDING_SECRET_PROFILE_ID: embed.profile_id,
            AutoGraphInstallParams.FPS_RECOVERY_USERNAME: "fps-recovery",
        }
    )
    try:
        created = services.deploy_service(install_path=AcpPath.AUTOGRAPH, request=request)
        assert created.service_id

        removed = services.delete(service_id=created.service_id)
        assert removed.service_id == created.service_id
        with pytest.raises(ServiceNotFoundError, match="not found"):
            services.delete(service_id=created.service_id)
    finally:
        communication.send_request("delete", f"{AcpPath.PROJECT}/{DB_NAME}/{project_name}")
