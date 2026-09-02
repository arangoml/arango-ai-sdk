"""Project namespace.

The first user-facing area on the client. One call creates a project; the user
never builds a URL, sets a header, or handles a token.
"""

from typing import Any

from arango_ai_sdk.communication import Communication

__all__ = ["ProjectManager"]


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
    ) -> Any:
        """Create a project and return the service's project object.

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
        Any
            The created project as the service rendered it. Field names arrive
            camelCased (``projectName``, not ``project_name``).
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
        return self._communication.send_request("post", "/ai/v1/project", data=data)
