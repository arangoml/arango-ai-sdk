"""The central communication layer.

Every request the SDK makes to any service goes through :class:`Communication`.
It owns the connection, attaches the authentication header, renews the token
when the platform rejects it, and translates driver-level failures into the
SDK's own exceptions. Service modules built on top of it -- ingestion,
retrieval, file upload -- never handle a token or a raw response themselves.

Error responses are the one thing this layer does not classify. A ``400`` from
"create project" means an invalid project name; the same ``400`` from "build
corpus" means an invalid file id. Only the service module knows which, so
:meth:`Communication.send_request` raises a generic :class:`ServiceError` that
carries the status code, the service's error number and its message, and the
service module catches it and re-raises the precise exception.

Transport is provided by ``python-arango``.

TODO: decouple from ``python-arango`` internals. ``Connection.process_request``
and its ``skip_db_prefix`` argument are private, undocumented API.
"""

from collections.abc import Mapping
from typing import Any, cast

from arango import ArangoClient
from arango.connection import JwtConnection
from arango.database import StandardDatabase
from arango.exceptions import ArangoError, JWTAuthError, ServerConnectionError
from arango.request import Request
from arango.response import Response
from requests.exceptions import Timeout

from arango_ai_sdk.exceptions import (
    AuthenticationError,
    CommunicationError,
    DatabaseNotFoundError,
    InvalidCredentialsError,
    PlatformUnreachableError,
    ServiceError,
    TokenRefreshError,
)

__all__ = ["Communication"]

DEFAULT_TIMEOUT = 60.0
DEFAULT_MAX_RETRIES = 3


class Communication:
    """Owns the authenticated connection to the platform.

    Parameters
    ----------
    base_url : str
        Full platform endpoint, port included, exactly as the deployment
        publishes it -- e.g. ``https://deployment.<cluster>.svc:8529``.
    username : str
        Username to authenticate with.
    password : str
        Password to authenticate with.
    db_name : str
        Database to connect to. Required: the client above always decides this,
        so a default here would never be used and could only disagree with it.
    timeout : float, optional
        Per-request timeout in seconds.
    max_retries : int, optional
        How many times an unreachable platform is retried before giving up.

    Raises
    ------
    InvalidCredentialsError
        The platform rejected the username or password. Authentication happens
        during construction, so this surfaces here rather than on first use.
    DatabaseNotFoundError
        ``db_name`` does not exist. Checked during construction too, so a typo
        fails immediately rather than on the first real request.
    PlatformUnreachableError
        The platform could not be reached within the retry budget.
    """

    # What this class borrows from ``python-arango``.
    #
    # Supported public API:
    #   _client is an ArangoClient; we call close() on it.
    #   _db comes from _client.db(..., verify=True), which authenticates and
    #     proves the database exists in the same call.
    #   _conn comes from _db.conn; we call refresh_token() on it.
    #
    # The coupling the module TODO is about, and all of it:
    #   _conn._auth_header -- private, and the driver offers no public getter.
    #   _conn.process_request(...) -- a public name with an undocumented
    #     contract, needed only for its skip_db_prefix argument.
    #
    # Replacing those two with a session and a header we own would change
    # nothing above this class.
    _client: ArangoClient
    _db: StandardDatabase
    _conn: JwtConnection

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        db_name: str,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        self._client = ArangoClient(
            hosts=base_url,
            request_timeout=timeout,
            resolver_max_tries=max_retries,
        )

        # One call, two jobs. `auth_method="jwt"` exchanges the credentials for
        # a token before returning, and `verify=True` then probes the database,
        # so a wrong password and a misspelt database name both fail here rather
        # than on the caller's first real request.
        try:
            self._db = self._client.db(
                name=db_name,
                username=username,
                password=password,
                verify=True,
                auth_method="jwt",
            )
        except JWTAuthError as exc:
            raise InvalidCredentialsError(
                "The platform rejected the username or password."
            ) from exc
        except ServerConnectionError as exc:
            # Find out the exact cause of ServerConnectionError.
            raise _probe_server_connection_error(exc, db_name) from exc
        except ConnectionAbortedError as exc:
            # The driver raises the Python builtin once it has exhausted its
            # retries, not an ArangoError, so this needs its own clause or it
            # escapes untranslated.
            raise PlatformUnreachableError(
                f"Could not reach {base_url} after {max_retries} attempts."
            ) from exc
        except ArangoError as exc:
            # Backstop: no driver exception may reach a caller untranslated.
            raise CommunicationError(f"Could not establish a connection: {exc}") from exc

        # `.conn` is typed as a union of the three connection kinds; asking for
        # JWT above is what decides which one we actually get.
        self._conn: JwtConnection = cast(JwtConnection, self._db.conn)

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
            Token refresh failed due to invalid credentials.
        PlatformUnreachableError
            Authentication endpoint could not be reached.
        TokenRefreshError
            The exchange could not be completed for any other reason.
        """
        try:
            self._conn.refresh_token()
        except JWTAuthError as err:
            if err.http_code == 401:
                raise InvalidCredentialsError(
                    "The platform rejected the username or password at token refresh attempt."
                ) from err
            raise TokenRefreshError("Token refresh failed.") from err
        except ConnectionAbortedError as err:
            raise PlatformUnreachableError(
                "Authentication endpoint is unreachable on a token refresh attempt."
            ) from err
        except ArangoError as err:
            raise TokenRefreshError("Token refresh failed.") from err

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
            Path on the platform, e.g. ``"/ai/v1/all_project_names/{database}"``.
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
        AuthenticationError
            The platform rejected the token, and re-authenticating did not help.
            Raised as the base class when the fresh token was rejected too. When
            the re-authentication itself fails, the subclass says why:
            :class:`InvalidCredentialsError` if the platform rejected the
            username or password, :class:`TokenRefreshError` for any other
            failure of the token exchange.
        PlatformUnreachableError
            The platform could not be reached within the retry budget, did not
            answer within the request timeout, or its authentication endpoint
            could not be reached during re-authentication.
        ServiceError
            The service answered with a non-success status other than ``401``.
            A ``404`` is classified here as an unrouted path. Everything else
            is deliberately generic and carries ``status_code``, the service's
            ``error_code`` where it sent one, and its message: the service
            module that made the call knows what the status means for that
            endpoint and re-raises the precise exception itself.
        """
        # A fresh dict per call: the caller's headers first, then Authorization
        # on top so it cannot be overridden.
        # Read from the connection on every call, since _authenticate()
        # replaces the token it holds.
        retried = False
        while True:
            request_headers: dict[str, str] = {
                **(headers or {}),
                "Authorization": cast(str, self._conn._auth_header),
            }
            request = Request(
                method=method,
                endpoint=path,
                headers=request_headers,
                params=dict(params) if params else None,
                data=data,
            )
            try:
                resp: Response = self._conn.process_request(
                    host_index=0, request=request, skip_db_prefix=True
                )
            except ConnectionAbortedError as err:
                raise PlatformUnreachableError(
                    "Platform could not be reached to execute the request."
                ) from err
            except Timeout as err:
                # The driver retries only requests.ConnectionError. A ReadTimeout
                # is not one, so it would otherwise reach the caller raw.
                raise PlatformUnreachableError(
                    "Platform did not answer within the request timeout."
                ) from err
            # Two statuses mean the same thing regardless of endpoint, so they are
            # classified here. 404: the path is not routed. 401: refresh the token
            # and retry once.
            if resp.status_code == 404:
                raise ServiceError(
                    message=f"Requested endpoint: {path} does not exist.", status_code=404
                )
            if resp.status_code == 401:
                if not retried:
                    retried = True
                    self._authenticate()
                    continue
                raise AuthenticationError("The platform rejected a freshly created JWT.")
            # Every other failure goes up as-is for the service module to classify.
            # `is_success` also covers a 2xx whose body carries an ArangoDB errorNum.
            if not resp.is_success:
                raise ServiceError(
                    message=f"{method.upper()} {path} failed with {resp.status_code}: "
                    f"{_error_message(resp)}",
                    status_code=resp.status_code,
                    error_code=resp.error_code,
                )
            return resp.body

    def close(self) -> None:
        """Release the underlying HTTP sessions."""
        self._client.close()


def _error_message(resp: Response) -> str:
    """Pull the human-readable message out of an error response.

    The gateway answers in ArangoDB's shape (``errorMessage``), the AI services
    in FastAPI's (``detail``). Fall back to the status text when neither is
    there, so the message is never empty.

    Parameters
    ----------
    resp : Response
        A non-success response.

    Returns
    -------
    str
        The best message the response offers.
    """
    if resp.error_message:
        return resp.error_message
    if isinstance(resp.body, dict) and resp.body.get("detail"):
        return str(resp.body["detail"])
    return resp.status_text or "no message"


def _probe_server_connection_error(
    exc: ServerConnectionError, db_name: str
) -> DatabaseNotFoundError | InvalidCredentialsError | PlatformUnreachableError:
    """Map a failed connection probe onto the condition behind it.

    The driver raises one type for every probe failure, so the status code is
    the only thing separating "no such database" from "these credentials cannot
    see it". Remember that we reach here only with a ServerConnectionError,
    which means that we could not connect to the ArangoDB.

    Parameters
    ----------
    exc : ServerConnectionError
        The failure the driver's probe raised.
    db_name : str
        Database that was probed, used in the message.

    Returns
    -------
    DatabaseNotFoundError | InvalidCredentialsError | PlatformUnreachableError
        The exception to raise. Returned rather than raised, so the caller keeps
        the ``raise ... from exc`` chain intact.
    """
    if exc.http_code == 404:
        return DatabaseNotFoundError(
            f"Database {db_name!r} does not exist on this platform.",
            status_code=404,
        )
    if exc.http_code in (401, 403):
        return InvalidCredentialsError(f"These credentials cannot access {db_name!r}.")
    return PlatformUnreachableError(f"The platform rejected the connection probe: {exc}")
