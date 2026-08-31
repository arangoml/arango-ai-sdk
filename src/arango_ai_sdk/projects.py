"""Project namespace.

The first user-facing area on the client. One call creates a project; the user
never builds a URL, sets a header, or handles a token.

Listing, fetching, updating and deleting projects are out of scope for this
story.
"""

from typing import Any

from arango_ai_sdk.communication import Communication

__all__ = ["ProjectManager"]

# AI service sits behind this prefix on the gateway. The proto paths are
# relative to it, so `post: "/v1/project"` is reached at "/ai/v1/project".
AI_PREFIX = "/ai/v1"


def _build_create_project_request(
    name: str,
    type: str,
    db_name: str,
    *,
    description: str | None = None,
) -> tuple[str, dict[str, str]]:
    """Build the path and JSON body for creating a project.

    No HTTP. ``ProjectManager.create`` sends this; unit tests check this helper
    without touching the network.

    Wire fields follow ``CreateProjectRequest`` in GenAI-Service ``proto/genai.proto``:
    ``project_name``, ``project_type``, ``project_db_name``, optional
    ``project_description``.

    Parameters
    ----------
    name : str
        Project name. Sent as ``project_name`` on the wire.
    type : str
        Project type, e.g. ``"autograph"``. Sent as ``project_type``.
    db_name : str
        Database the project is stored in. Sent as ``project_db_name``.
    description : str, optional
        Optional description. Omitted from the body when not given.

    Returns
    -------
    tuple[str, dict[str, str]]
        The gateway path and the request body.
    """
    data: dict[str, str] = {
        "project_name": name,
        "project_type": type,
        "project_db_name": db_name,
    }
    if description is not None:
        data["project_description"] = description
    return f"{AI_PREFIX}/project", data


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
        name: str,
        type: str,
        *,
        description: str | None = None,
    ) -> Any:
        """Create a project and return the service's project object.

        Parameters
        ----------
        name : str
            Project name. Sent as ``project_name`` on the wire.
        type : str
            Project type, e.g. ``"autograph"``. Sent as ``project_type``.
        description : str, optional
            Optional description. Omitted from the body when not given.

        Returns
        -------
        Any
            The created project as the service rendered it. Field names arrive
            camelCased (``projectName``, not ``project_name``).
        """
        path, data = _build_create_project_request(
            name,
            type,
            self._db_name,
            description=description,
        )
        return self._communication.send_request("post", path, data=data)
