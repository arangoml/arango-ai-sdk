"""The central communication layer.

Every request the SDK makes to any service goes through :class:`Communication`.
It owns the connection, attaches the authentication header, renews the token
when the platform rejects it, and translates driver-level failures into the
SDK's own exceptions. Service modules built on top of it -- ingestion,
retrieval, file upload -- never handle a token or a status code themselves.

Transport is provided by ``python-arango``.

TODO: decouple from ``python-arango`` internals. ``Connection.process_request``
and its ``skip_db_prefix`` argument are private, undocumented API.
"""

from collections.abc import Mapping
from typing import Any

__all__ = ["Communication"]

DEFAULT_PORT = 8529
DEFAULT_TIMEOUT = 60.0
DEFAULT_MAX_RETRIES = 3


class Communication:
    """Owns the authenticated connection to the platform.

    Parameters
    ----------
    base_url : str
        Platform URL without a port, e.g. ``https://example.rnd.pilot.arango.ai``.
    username : str
        Username to authenticate with.
    password : str
        Password to authenticate with.
    db_name : str
        Database to connect to. Required: the client above always decides this,
        so a default here would never be used and could only disagree with it.
    port : int, optional
        Port every request is sent to. Defaults to ``8529``.
    timeout : float, optional
        Per-request timeout in seconds.
    max_retries : int, optional
        How many times an unreachable platform is retried before giving up.

    Raises
    ------
    InvalidCredentialsError
        The platform rejected the username or password. Authentication happens
        during construction, so this surfaces here rather than on first use.
    PlatformUnreachableError
        The platform could not be reached within the retry budget.
    """

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        db_name: str,
        *,
        port: int = DEFAULT_PORT,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        raise NotImplementedError

    def _authenticate(self) -> None:
        """Exchange the credentials for a token and hold it.

        Called twice at most per token: once during construction, and again when
        the platform rejects a request. There is no separate "renew" -- the two
        are the same exchange, and the platform's rejection is the only reliable
        signal that the held token is no longer good.

        Private on purpose: the point of this layer is that nothing above it
        ever obtains, inspects or refreshes a token.

        Raises
        ------
        InvalidCredentialsError
            The platform rejected the username or password.
        TokenRefreshError
            The exchange could not be completed for any other reason.
        PlatformUnreachableError
            The platform could not be reached within the retry budget.
        """
        raise NotImplementedError

    def send_request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, str] | None = None,
        data: Any = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        """Send an authenticated request and return the parsed response body.

        The caller supplies only the method and the path. The token, its
        renewal, retries and error translation are handled here.

        This mirrors ``JwtConnection.send_request`` in ``python-arango`` and
        deviates from it in three deliberate ways. They are listed because each
        one looks like an accident, and "simplifying" any of them back towards
        the driver reintroduces a bug:

        1. It calls ``process_request(..., skip_db_prefix=True)``. The driver's
           ``send_request`` always prefixes ``/_db/<db_name>``, which is wrong
           for platform services -- not all of them expose scoped endpoints.
        2. It treats a bare ``401`` as the signal to re-authenticate. The driver
           additionally requires ArangoDB's ``errorNum 11``, AI services behind the
           gateway have no reason to emit ArangoDB error numbers.
        3. It re-authenticates on a ``401`` even when the held token has already
           expired, and surfaces the error only if that second attempt also fails.
           The driver, having received a ``401``, compares the token's expiry against
           the current time and returns the error unrefreshed. So a client idle
           past the one-hour token lifetime fails on perfectly good credentials.

        Parameters
        ----------
        method : str
            HTTP method, e.g. ``"get"`` or ``"post"``.
        path : str
            Path on the platform, e.g. ``"/v1/ai/all_project_names/{database}"``.
        params : Mapping[str, str], optional
            Query-string parameters.
        data : Any, optional
            Request payload. Serialised as JSON.
        headers : Mapping[str, str], optional
            Extra request headers. The ``Authorization`` header is set here and
            cannot be overridden.

        Returns
        -------
        Any
            The deserialised response body. Never a driver response object --
            that type must not reach callers.

        Raises
        ------
        InvalidCredentialsError
            The platform rejected the token and re-authenticating did not help.
        PlatformUnreachableError
            The platform could not be reached within the retry budget.
        ServiceError
            The service answered with a non-success status.
        """
        raise NotImplementedError

    def close(self) -> None:
        """Release the underlying HTTP sessions."""
        raise NotImplementedError
