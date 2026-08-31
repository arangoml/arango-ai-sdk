"""Integration tests for :class:`ProjectManager`, against a live platform.

Same skip rules and credentials as ``tests/test_communication.py``. Values can
come from the process environment or from a ``.env`` file in the repo root
(see ``.env.example``). These tests send a real HTTP request through
``ProjectManager.create``.
"""

import os
import uuid
from collections.abc import Iterator

import pytest

from arango_ai_sdk._naming import EnvVar
from arango_ai_sdk.communication import Communication
from arango_ai_sdk.projects import AI_PREFIX, ProjectManager

BASE_URL = os.environ.get(EnvVar.ARANGO_DEPLOYMENT_ENDPOINT, "")
DB_NAME = os.environ.get(EnvVar.ARANGO_SDK_TEST_DB, "")
USERNAME = os.environ.get(EnvVar.ARANGO_SDK_TEST_USERNAME, "")
PASSWORD = os.environ.get(EnvVar.ARANGO_SDK_TEST_PASSWORD, "")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not (BASE_URL and DB_NAME and USERNAME and PASSWORD),
        reason=(
            f"{EnvVar.ARANGO_DEPLOYMENT_ENDPOINT}, {EnvVar.ARANGO_SDK_TEST_DB}, "
            f"{EnvVar.ARANGO_SDK_TEST_USERNAME}, and {EnvVar.ARANGO_SDK_TEST_PASSWORD} "
            "must all be set for live-platform tests"
        ),
    ),
]


@pytest.fixture
def communication() -> Iterator[Communication]:
    comm = Communication(BASE_URL, USERNAME, PASSWORD, DB_NAME)
    yield comm
    comm.close()


@pytest.fixture
def project_name() -> str:
    return f"sdk_test_{uuid.uuid4().hex[:8]}"


def test_create_project_through_the_project_manager(
    communication: Communication, project_name: str
) -> None:
    """A user-facing create call creates a real project on the platform."""
    project = ProjectManager(communication, db_name=DB_NAME)
    created = project.create(
        name=project_name,
        type="autograph",
        description="Created by the SDK integration tests.",
    )
    assert created["projectName"] == project_name
    assert created["projectType"] == "autograph"
    assert created["projectDbName"] == DB_NAME

    try:
        listed = communication.send_request("get", f"{AI_PREFIX}/all_project_names/{DB_NAME}")
        assert project_name in listed["projectNames"]
    finally:
        communication.send_request("delete", f"{AI_PREFIX}/project/{DB_NAME}/{project_name}")
