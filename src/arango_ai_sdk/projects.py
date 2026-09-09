"""Project namespace.

The first user-facing area on the client. The user
never builds a URL, sets a header, or handles a token to manage projects.
"""

from collections.abc import Mapping
from typing import Any

from arango_ai_sdk._naming import AcpPath
from arango_ai_sdk.communication import Communication
from arango_ai_sdk.exceptions import (
    InvalidProjectNameError,
    ProjectNotFoundError,
    ServiceError,
)
from arango_ai_sdk.models import (
    AiProject,
    CreateProjectRequest,
    GetProjectByNameRequest,
)
from arango_ai_sdk.project_handle import AiProjectHandle

__all__ = ["AiProject", "ProjectManager"]


class ProjectManager:
    """Manage projects through the communication layer.

    Parameters
    ----------
    communication : Communication
        Shared transport. This namespace calls ``send_request`` and nothing else.
    db_name : str
        Database the created project is stored in. Taken from the client, not
        from the user of ``create``.
    """

    def __init__(self, communication: Communication, db_name: str) -> None:
        self._communication = communication
        self._db_name = db_name

    def create(
        self,
        project_name: str,
        project_type: str,
        *,
        description: str | None = None,
    ) -> AiProjectHandle:
        """Create a project and return it as :class:`AiProjectHandle`.

        Parameters
        ----------
        project_name : str
            Project name.
        project_type : str
            Project type, e.g. ``"autograph"``.
        description : str, optional
            Optional description. Omitted from the body when not given.

        Returns
        -------
        AiProjectHandle
            A handle for the created project.

        Raises
        ------
        InvalidProjectNameError
            The endpoint rejected the project name.
        """
        request = CreateProjectRequest(
            project_name=project_name,
            project_type=project_type,
            project_db_name=self._db_name,
            project_description=description,
        )
        data = request.to_dict()
        invalid_project_name_message = (
            "Project name can only contain letters, numbers, underscores, and hyphens"
        )
        try:
            body = self._communication.send_request("post", AcpPath.PROJECT, data=data)
        except ServiceError as exc:
            if invalid_project_name_message in str(exc):
                raise InvalidProjectNameError(
                    str(exc),
                    status_code=exc.status_code,
                    error_code=exc.error_code,
                ) from exc
            raise
        return AiProjectHandle(
            ai_project=_project_from_body(body), communication=self._communication
        )

    def get(
        self,
        project_name: str,
    ) -> AiProjectHandle:
        """Get a project and return it as :class:`AiProjectHandle`.

        Parameters
        ----------
        project_name : str
            Project name.

        Returns
        -------
        AiProjectHandle
            A handle for the requested project.

        Raises
        ------
        ProjectNotFoundError
            The endpoint did not find the requested project.
        ServiceError
            Any other service-related error.
        """
        if not project_name:
            raise ProjectNotFoundError(
                "No project with this empty name exists.",
                status_code=404,
            )
        request = GetProjectByNameRequest(
            project_name=project_name,
            # notice that the db_name comes from the ProjectManager object
            # and not as a call argument because everything happens inside
            # one client.
            project_db_name=self._db_name,
        )
        project_not_exist_message = f"Project with name '{project_name}' does not exist"
        endpoint_path = (
            f"{AcpPath.PROJECT_BY_NAME}/{request.project_db_name}/{request.project_name}"
        )
        try:
            body = self._communication.send_request(
                "get",
                endpoint_path,
            )
        except ServiceError as exc:
            if project_not_exist_message in str(exc):
                raise ProjectNotFoundError(
                    str(exc),
                    status_code=404,
                    error_code=exc.error_code,
                ) from exc
            raise
        return AiProjectHandle(
            ai_project=_project_from_body(body), communication=self._communication
        )


def _project_from_body(body: Mapping[str, Any]) -> AiProject:
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
