"""Unit tests for :class:`AiProjectHandle`; no platform needed."""

from typing import cast

from arango_ai_sdk.communication import Communication
from arango_ai_sdk.models import AiProject
from arango_ai_sdk.project_handle import AiProjectHandle


def test_repr_names_project_type_and_database():
    project = AiProject(project_name="sales", project_type="autograph", project_db_name="mydb")
    # The handle never touches the transport here, so any placeholder will do.
    handle = AiProjectHandle(ai_project=project, communication=cast(Communication, object()))

    assert repr(handle) == "AiProjectHandle(name='sales', project_type='autograph', db_name='mydb')"
