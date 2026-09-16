"""Project namespace.

The first user-facing area on the client. The user
never builds a URL, sets a header, or handles a token to manage projects.
"""

from arango_ai_sdk._naming import AcpPath
from arango_ai_sdk._project_api import get_project, project_from_body
from arango_ai_sdk.communication import Communication
from arango_ai_sdk.exceptions import InvalidProjectNameError, ServiceError
from arango_ai_sdk.models import AiProject, CreateProjectRequest
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
            ai_project=project_from_body(body), communication=self._communication
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
        # The db_name comes from the ProjectManager object and not as a call
        # argument because everything happens inside one client.
        project = get_project(
            communication=self._communication,
            db_name=self._db_name,
            project_name=project_name,
        )
        return AiProjectHandle(ai_project=project, communication=self._communication)
