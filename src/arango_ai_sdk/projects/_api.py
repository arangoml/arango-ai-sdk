"""Get one project from the platform and load it into an :class:`AiProject`.

Shared by ``ProjectManager.get`` and ``AiProjectHandle.refresh``. Lives in its
own module so ``project_handle.py`` does not have to import ``projects.py``,
which imports ``project_handle.py`` in turn.
"""

from collections.abc import Mapping
from typing import Any

from arango_ai_sdk._naming import AcpPath
from arango_ai_sdk.communication import Communication
from arango_ai_sdk.exceptions import ProjectNotFoundError, ServiceError
from arango_ai_sdk.models import AiProject, GetProjectByNameRequest

__all__ = ["get_project", "project_from_body"]


def get_project(communication: Communication, db_name: str, project_name: str) -> AiProject:
    """Get a project by name and return it as :class:`AiProject`.

    Parameters
    ----------
    communication : Communication
        Transport to send the request through.
    db_name : str
        Database the project belongs to.
    project_name : str
        Project name.

    Raises
    ------
    ProjectNotFoundError
        ``project_name`` is empty, or the endpoint did not find the project.
    ServiceError
        Any other service-related error.
    """
    if not project_name:
        raise ProjectNotFoundError(
            "No project with this empty name exists.",
            status_code=404,
        )
    request = GetProjectByNameRequest(project_name=project_name, project_db_name=db_name)
    project_not_exist_message = f"Project with name '{project_name}' does not exist"
    endpoint_path = f"{AcpPath.PROJECT_BY_NAME}/{request.project_db_name}/{request.project_name}"
    try:
        body = communication.send_request("get", endpoint_path)
    except ServiceError as exc:
        if project_not_exist_message in str(exc):
            raise ProjectNotFoundError(
                str(exc),
                status_code=404,
                error_code=exc.error_code,
            ) from exc
        raise
    return project_from_body(body)


def project_from_body(body: Mapping[str, Any]) -> AiProject:
    """Build an :class:`AiProject` from the camelCase JSON body of a service reply.

    Parameters
    ----------
    body : Mapping[str, Any]
        The project object as the service returned it.

    Returns
    -------
    AiProject
        The loaded project, every field the service sent included.
    """
    project = AiProject()
    # `from_dict` fills the instance in place and returns it. It is a betterproto
    # `hybridmethod` descriptor that ty cannot type, hence the ignore. Same
    # pattern as `_profile_from_body` in secret_profiles.py.
    project.from_dict(body)  # ty: ignore[invalid-attribute-access]
    return project
