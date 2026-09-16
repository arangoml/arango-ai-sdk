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
from arango_ai_sdk.exceptions import InvalidProjectNameError, ProjectNotFoundError
from arango_ai_sdk.project_handle import AiProjectHandle
from arango_ai_sdk.projects import ProjectManager

DB_NAME = os.environ.get(EnvVar.ARANGO_SDK_TEST_DB, "")


def test_create_project_through_the_project_manager(
    communication: Communication, project_name: str
) -> None:
    """A user-facing create call creates a real project on the platform."""
    project = ProjectManager(communication, db_name=DB_NAME)
    created: AiProjectHandle = project.create(
        project_name=project_name,
        project_type="autograph",
        description="Created by the SDK integration tests.",
    )
    try:
        assert created._project.project_name == project_name
        assert created._project.project_type == "autograph"
        assert created._project.project_db_name == DB_NAME

        listed = communication.send_request("get", f"{AcpPath.ALL_PROJECT_NAMES}/{DB_NAME}")
        assert project_name in listed["projectNames"]
    finally:
        communication.send_request("delete", f"{AcpPath.PROJECT}/{DB_NAME}/{project_name}")


def test_get_existing_project_returns_a_handle_bound_to_it(
    communication: Communication, project_name: str
) -> None:
    """A project created earlier can be picked up again by name, as a handle."""
    project = ProjectManager(communication, db_name=DB_NAME)
    project.create(
        project_name=project_name,
        project_type="autograph",
        description="Created by the SDK integration tests.",
    )
    try:
        fetched = project.get(project_name=project_name)
        assert isinstance(fetched, AiProjectHandle)
        assert fetched.name == project_name
        assert fetched.project_type == "autograph"
        assert fetched.db_name == DB_NAME
        assert fetched.description == "Created by the SDK integration tests."
    finally:
        communication.send_request("delete", f"{AcpPath.PROJECT}/{DB_NAME}/{project_name}")


def test_refresh_reloads_the_project_and_raises_once_it_is_gone(
    communication: Communication, project_name: str
) -> None:
    """``refresh`` re-reads the project; after deletion it is a not-found error."""
    project = ProjectManager(communication, db_name=DB_NAME)
    created = project.create(project_name=project_name, project_type="autograph")
    try:
        reloaded = created.refresh()
        assert reloaded is created.project
        assert created.name == project_name
        assert created.db_name == DB_NAME
    finally:
        communication.send_request("delete", f"{AcpPath.PROJECT}/{DB_NAME}/{project_name}")
    with pytest.raises(ProjectNotFoundError):
        created.refresh()


def test_get_missing_project_raises_project_not_found(
    communication: Communication, project_name: str
) -> None:
    """Asking for a name that was never created is a distinct not-found error."""
    project = ProjectManager(communication, db_name=DB_NAME)
    with pytest.raises(ProjectNotFoundError) as excinfo:
        project.get(project_name=project_name)
    assert excinfo.value.status_code == 404


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
