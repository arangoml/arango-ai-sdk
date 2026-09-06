"""Integration tests for :class:`ProjectManager`, against a live platform.

Marker and credentials skip come from ``tests/integration/conftest.py``. Values
can come from the process environment or from a ``.env`` file in the repo root
(see ``.env.example``). These tests send a real HTTP request through
``ProjectManager.create``.
"""

import os

import pytest

from arango_ai_sdk._naming import AcpPath, EnvVar
from arango_ai_sdk.communication import Communication
from arango_ai_sdk.exceptions import InvalidProjectNameError
from arango_ai_sdk.projects import ProjectManager

DB_NAME = os.environ.get(EnvVar.ARANGO_SDK_TEST_DB, "")


def test_create_project_through_the_project_manager(
    communication: Communication, project_name: str
) -> None:
    """A user-facing create call creates a real project on the platform."""
    project = ProjectManager(communication, db_name=DB_NAME)
    created = project.create(
        project_name=project_name,
        project_type="autograph",
        description="Created by the SDK integration tests.",
    )
    try:
        assert created.project_name == project_name
        assert created.project_type == "autograph"
        assert created.project_db_name == DB_NAME

        listed = communication.send_request("get", f"{AcpPath.ALL_PROJECT_NAMES}/{DB_NAME}")
        assert project_name in listed["projectNames"]
    finally:
        communication.send_request("delete", f"{AcpPath.PROJECT}/{DB_NAME}/{project_name}")


def test_create_project_with_empty_name_raises_invalid_project_name(
    communication: Communication,
) -> None:
    """An empty name is rejected by the endpoint and surfaced as a named error."""
    project = ProjectManager(communication, db_name=DB_NAME)
    with pytest.raises(InvalidProjectNameError, match="Project name can only contain"):
        project.create(project_name="", project_type="autograph")


def test_create_project_with_invalid_name_raises_invalid_project_name(
    communication: Communication,
) -> None:
    """A name that breaks ACP naming rules is surfaced as a named error."""
    project = ProjectManager(communication, db_name=DB_NAME)
    with pytest.raises(InvalidProjectNameError, match="Project name can only contain"):
        project.create(project_name="Not A Valid Name!", project_type="autograph")
