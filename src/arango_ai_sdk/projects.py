"""Project namespace.

The first user-facing area on the client. One call creates a project; the user
never builds a URL, sets a header, or handles a token.
"""

from arango_ai_sdk.communication import Communication
from arango_ai_sdk.exceptions import InvalidProjectNameError, ServiceError

__all__ = ["AIProject", "ProjectManager"]


class AIProject:
    """The project as the service returned it.

    Attributes only, matching ``AIProject`` in ACP. JSON arrives camelCased
    (``projectName``); these fields are snake_case.
    """

    # TODO [AIS-2043]: replace this hand-written class with the generated data classes from
    # arango_platform_clients (FileManager).
    # https://github.com/arangoml/mlflow_http_artifact_repository/tree/main/packages/arango_platform_clients

    def __init__(
        self,
        project_name: str,
        project_type: str,
        project_db_name: str,
        project_description: str | None = None,
    ) -> None:
        self.project_name = project_name
        self.project_type = project_type
        self.project_db_name = project_db_name
        self.project_description = project_description


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
    ) -> AIProject:
        """Create a project and return it as :class:`AIProject`.

        Parameters
        ----------
        project_name : str
            Project name. Sent as ``project_name`` on the wire.
        project_type : str
            Project type, e.g. ``"autograph"``. Sent as ``project_type``.
        description : str, optional
            Optional description. Omitted from the body when not given.

        Returns
        -------
        AIProject
            The created project.

        Raises
        ------
        InvalidProjectNameError
            The endpoint rejected the project name.
        """
        data: dict[str, str] = {
            "project_name": project_name,
            "project_type": project_type,
            "project_db_name": self._db_name,
        }
        if description is not None:
            data["project_description"] = description
        # ACP service sits behind this prefix on the gateway. The proto paths are
        # relative to it, so `post: "/v1/project"` is reached at "/ai/v1/project".
        invalid_project_name_message = (
            "Project name can only contain letters, numbers, underscores, and hyphens"
        )
        try:
            body = self._communication.send_request("post", "/ai/v1/project", data=data)
        except ServiceError as exc:
            if invalid_project_name_message in str(exc):
                raise InvalidProjectNameError(
                    str(exc),
                    status_code=exc.status_code,
                    error_code=exc.error_code,
                ) from exc
            raise
        return AIProject(
            project_name=body["projectName"],
            project_type=body["projectType"],
            project_db_name=body["projectDbName"],
            project_description=body.get("projectDescription"),
        )
