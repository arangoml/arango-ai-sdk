"""Create and manage AiProjectHandle objects.

AiProjectHandle is the object that contains all project-scoped services::

    sales = client.project.create(project_name="sales", project_type="autograph")
    print(sales.db_name)
"""

from arango_ai_sdk.communication import Communication
from arango_ai_sdk.models import (
    AiProject,
    AutoGraphModelSettings,
    GraphRagProjectMetaData,
)

__all__ = ["AiProjectHandle"]


class AiProjectHandle:
    """Stores all project-scoped objects.

    Right now, the handle contains only the AiProject and the communication objects.
    With the time, we will be adding autograph and graphrag objects as well.

    """

    def __init__(self, ai_project: AiProject, communication: Communication):
        """Construct an AiProjectHandle object.

        To construct the AiProjectHandle instance, we need the raw AiProject
        and a communication object that facilitates the transport to the platform
        """
        self._project: AiProject = ai_project
        self._communication: Communication = communication

    def __repr__(self) -> str:
        """Return a short representation naming the project, its type and database."""
        return (
            f"{type(self).__name__}(name={self.name!r}, project_type={self.project_type!r}, "
            f"db_name={self.db_name!r})"
        )

    @property
    def name(self) -> str:
        """Return project name stored in this handle."""
        return self._project.project_name

    @property
    def project_type(self) -> str:
        """Return project type, e.g. ``"autograph"``."""
        return self._project.project_type

    @property
    def db_name(self) -> str:
        """Return database name to which this project belongs."""
        return self._project.project_db_name

    @property
    def description(self) -> str | None:
        """Return project description, or ``None`` if none was given."""
        return self._project.project_description

    @property
    def metadata(self) -> GraphRagProjectMetaData | None:
        """Return project metadata describing the project's services state."""
        return self._project.project_metadata

    @property
    def file_names(self) -> list[str]:
        """Return names of the files uploaded to this project."""
        return self._project.project_files

    @property
    def model_settings(self) -> AutoGraphModelSettings | None:
        """Return durable AutoGraph model and provider configuration."""
        return self._project.model_settings

    @property
    def project(self) -> AiProject:
        """Return raw AiProject object of this handle."""
        return self._project
