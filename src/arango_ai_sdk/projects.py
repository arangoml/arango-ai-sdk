"""Project namespace.

The first user-facing area on the client. One call creates a project; the user
never builds a URL, sets a header, or handles a token.
"""

from arango_ai_sdk._naming import AcpPath
from arango_ai_sdk.communication import Communication
from arango_ai_sdk.exceptions import InvalidProjectNameError, ServiceError
from arango_ai_sdk.models import AiProject, CreateProjectRequest

__all__ = ["AiProject", "ProjectManager"]


class ProjectManager:
    """Create projects through the communication layer.

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
    ) -> AiProject:
        """Create a project and return it as :class:`AiProject`.

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
        AiProject
            The created project.

        Raises
        ------
        InvalidProjectNameError
            The endpoint rejected the project name.
        """
        # The request body comes from the generated proto message, so the field
        # names are the proto's and a rename breaks at import time, not on the
        # wire. `to_dict` emits camelCase keys, which the gateway accepts.
        # Note on empty strings: `to_dict` omits a plain string field at its zero
        # value, so project_name="" is not sent at all. The server reads a missing
        # field as "" anyway, so it still gets rejected with the same error.
        # project_description is a proto `optional` field, so presence is
        # tracked: None is omitted, "" is sent as "".
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
        return AiProject(
            project_name=body["projectName"],
            project_type=body["projectType"],
            project_db_name=body["projectDbName"],
            project_description=body.get("projectDescription"),
        )
