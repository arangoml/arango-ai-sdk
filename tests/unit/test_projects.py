"""Unit tests for invalid-name handling on :class:`ProjectManager.create`."""

from unittest.mock import Mock

import pytest

from arango_ai_sdk.exceptions import InvalidProjectNameError
from arango_ai_sdk.projects import ProjectManager

_NAMING_MESSAGE = (
    "Project name can only contain letters, numbers, underscores, and hyphens "
    "and must start with a letter. It must be between 1 and 63 characters long."
)


def test_create_raises_on_an_invalid_argument_status_body() -> None:
    communication = Mock()
    communication.send_request.return_value = {
        "code": 3,
        "message": _NAMING_MESSAGE,
        "details": [],
    }
    project = ProjectManager(communication, db_name="sdk_test")

    with pytest.raises(InvalidProjectNameError) as excinfo:
        project.create(project_name="", project_type="autograph")

    assert _NAMING_MESSAGE in str(excinfo.value)
    assert excinfo.value.error_code == 3


def test_create_returns_the_project_when_the_service_accepts_the_name() -> None:
    communication = Mock()
    communication.send_request.return_value = {
        "projectName": "demo",
        "projectType": "autograph",
        "projectDbName": "sdk_test",
    }
    project = ProjectManager(communication, db_name="sdk_test")

    created = project.create(project_name="demo", project_type="autograph")

    assert created["projectName"] == "demo"
