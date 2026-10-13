"""Unit tests for :class:`AiProjectHandle`; no platform needed."""

from arango_ai_sdk.communication import Communication
from arango_ai_sdk.models import AiProject
from arango_ai_sdk.projects.handle import AiProjectHandle


def test_repr_names_project_type_and_database(placeholder_communication: Communication):
    project = AiProject(project_name="sales", project_type="autograph", project_db_name="mydb")
    handle = AiProjectHandle(ai_project=project, communication=placeholder_communication)

    assert repr(handle) == "AiProjectHandle(name='sales', project_type='autograph', db_name='mydb')"
