"""Unit tests for the create-project request builder.

These tests do not send HTTP. They check the small helper that turns
``create(name=..., type=...)`` into a path and JSON body. The call that
actually posts that body is covered by the projects integration tests.
"""

from arango_ai_sdk.projects import AI_PREFIX, _build_create_project_request


def test_build_create_project_request_matches_the_communication_test_body():
    path, data = _build_create_project_request(
        name="my-project",
        type="autograph",
        db_name="sdk_test",
        description="Created by the SDK integration tests.",
    )

    assert path == f"{AI_PREFIX}/project"
    assert data == {
        "project_name": "my-project",
        "project_type": "autograph",
        "project_db_name": "sdk_test",
        "project_description": "Created by the SDK integration tests.",
    }


def test_build_create_project_request_omits_description_when_not_given():
    path, data = _build_create_project_request(
        name="my-project",
        type="autograph",
        db_name="sdk_test",
    )

    assert path == f"{AI_PREFIX}/project"
    assert data == {
        "project_name": "my-project",
        "project_type": "autograph",
        "project_db_name": "sdk_test",
    }
    assert "project_description" not in data
