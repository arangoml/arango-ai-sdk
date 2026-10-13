"""Unit tests for the project loading helpers in ``_project_api``."""

from arango_ai_sdk.api._project_api import project_from_body


def test_project_from_body_loads_camel_case_fields():
    body = {
        "projectName": "sales",
        "projectType": "autograph",
        "projectDbName": "mydb",
        "projectDescription": "Created by the SDK unit tests.",
    }

    project = project_from_body(body)

    assert project.project_name == "sales"
    assert project.project_type == "autograph"
    assert project.project_db_name == "mydb"
    assert project.project_description == "Created by the SDK unit tests."
