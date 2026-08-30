"""The SDK's entry point.

:class:`ArangoAIClient` is what a user constructs. It takes credentials once and owns
the communication layer every later service namespace is built on.
"""

from arango_ai_sdk.communication import Communication

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
        Full platform endpoint, port included, exactly as the deployment
        publishes it -- e.g. ``https://deployment.<cluster>.svc:8529``.
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

    Raises
    ------
    InvalidCredentialsError
        The platform rejected the username or password.
    DatabaseNotFoundError
        ``db_name`` does not exist on the platform.
    PlatformUnreachableError
        The platform could not be reached within the retry budget.
    """

    def __init__(
        self,
        base_url: str,
        project_name: str,
        username: str,
        password: str,
        db_name: str = DEFAULT_DB_NAME,
    ) -> None:
        # construction should fail if any of these is an empty string.
        self._base_url = base_url
        self._project_name = project_name
        self._username = username
        self._password = password
        self._db_name = db_name
        self._communication = Communication(base_url, username, password, db_name)
        # TODO:
        # self._acp = ACP(self._communication)

    @property
    def base_url(self) -> str:
        """Full platform endpoint this client talks to, port included."""
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
    def communication(self) -> Communication:
        """The layer every service namespace sends its requests through.

        A namespace takes this at construction and calls ``send_request`` on it;
        it never reaches back into the client.
        """
        return self._communication

    def close(self) -> None:
        """Release the network resources this client holds.

        Forwards to the communication layer, which closes the driver's HTTP
        sessions and the sockets they keep alive. Safe to call more than once.
        """
        self._communication.close()

    # No `password` property, deliberately. A public getter on a credential is a
    # leak waiting to happen and nothing outside this class needs to read it back.
