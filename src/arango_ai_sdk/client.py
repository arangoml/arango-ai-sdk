"""The SDK's entry point.

:class:`ArangoAIClient` is what a user constructs. It takes credentials once and owns
the communication layer every later service namespace is built on.
"""

__all__ = ["ArangoAIClient"]

DEFAULT_DB_NAME = "_system"


class ArangoAIClient:
    """Entry point to the Arango AI Suite.

    Not to be confused with the concept of a communication client,
    this is a client interface to the AI suite SDK,
    it does not perform any communication tasks by itself.

    Parameters
    ----------
    base_url : str
        Platform URL without a port, e.g. ``https://example.rnd.pilot.arango.ai``.
        Port 8529 is used by default to reach the platform.
    project_name : str
        Project every project-scoped call is made against. Set once here, so no
        later method takes a project argument. Work with a second project by
        creating a second client.
    username : str
        Username to authenticate with.
    password : str
        Password to authenticate with. Held in memory for the client's lifetime,
        which is what token renewal needs, and never exposed again.
    db_name : str, optional
        Database to connect to. Defaults to ``_system``.
    port : str, optional
        Port every request is sent to, including authentication. Defaults to
        ``"8529"``, which is what the platform gateway exposes.
    """

    def __init__(
        self,
        base_url: str,
        project_name: str,
        username: str,
        password: str,
        db_name: str = DEFAULT_DB_NAME,
        port: str = "8529",
    ) -> None:
        self._base_url = base_url
        self._project_name = project_name
        self._username = username
        self._password = password
        self._db_name = db_name
        self._port = port

    @property
    def base_url(self) -> str:
        """Platform URL this client talks to, without a port."""
        return self._base_url

    @property
    def project_name(self) -> str:
        """Project this client is scoped to."""
        return self._project_name

    @property
    def username(self) -> str:
        """Username this client authenticates with."""
        return self._username

    @property
    def db_name(self) -> str:
        """Database this client is connected to."""
        return self._db_name

    @property
    def port(self) -> str:
        """Port this client sends every request to."""
        return self._port

    # No `password` property, deliberately. A public getter on a credential is a
    # leak waiting to happen and nothing outside this class needs to read it back.
