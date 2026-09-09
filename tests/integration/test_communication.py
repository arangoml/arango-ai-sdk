"""Integration tests for :class:`Communication`, against a live platform.

Integration tests that open real connections to the devstack deployment,
create and delete real projects, and need real credentials. They are skipped
automatically by ``tests/integration/conftest.py`` unless all credential
variables are set, so CI -- which has neither the credentials nor a route to
the pilot -- stays green without extra configuration.

To run them::

    export ARANGO_DEPLOYMENT_ENDPOINT='https://deployment.<cluster>.svc:8529'
    export ARANGO_SDK_TEST_PASSWORD='...'   # single quotes: the password contains $ and !
    uv run pytest tests/integration/test_communication.py -v

The endpoints exercised here belong to ACP Service (``proto/genai.proto``):
create a project, list project names, delete a project.

Note: pytest prints function arguments in tracebacks, so a failure here puts the
password on screen. Harmless locally, you typed it into the same terminal,
but do not paste raw failure output into a ticket or a chat.
Moreover, a test user and test database have been created in the EU devstack for
dev purposes.
"""

import os
from collections.abc import Iterator

import pytest

from arango_ai_sdk._naming import AcpPath, EnvVar
from arango_ai_sdk.communication import Communication
from arango_ai_sdk.exceptions import (
    AuthenticationError,
    DatabaseNotFoundError,
    InvalidCredentialsError,
    PlatformUnreachableError,
    ServiceError,
)

BASE_URL = os.environ.get(EnvVar.ARANGO_DEPLOYMENT_ENDPOINT, "")
DB_NAME = os.environ.get(EnvVar.ARANGO_SDK_TEST_DB, "")
USERNAME = os.environ.get(EnvVar.ARANGO_SDK_TEST_USERNAME, "")
PASSWORD = os.environ.get(EnvVar.ARANGO_SDK_TEST_PASSWORD, "")


@pytest.fixture
def communication_wrong_password() -> Iterator[Communication]:
    """Open an authenticated connection to the pilot platform, and close it after."""
    comm = Communication(BASE_URL, USERNAME, PASSWORD, DB_NAME)
    comm._conn._password = "wrong-password"
    yield comm
    comm.close()


@pytest.fixture
def communication_wrong_url() -> Iterator[Communication]:
    """Open an authenticated connection to the pilot platform, and close it after."""
    comm = Communication(BASE_URL, USERNAME, PASSWORD, DB_NAME)
    comm._conn._hosts = ["https://pilot.arango.non.existing:8529"]
    yield comm
    comm.close()


@pytest.fixture
def communication_invalid_jwt() -> Iterator[Communication]:
    """Open an authenticated connection to the pilot platform, and close it after."""
    comm = Communication(BASE_URL, USERNAME, PASSWORD, DB_NAME)
    old_header: str = str(comm._conn._auth_header)
    comm._conn._auth_header = old_header[:-1]
    yield comm
    comm.close()


@pytest.fixture
def communication_wrong_password_and_token() -> Iterator[Communication]:
    """Open an authenticated connection to the pilot platform, and close it after."""
    comm = Communication(BASE_URL, USERNAME, PASSWORD, DB_NAME)
    comm._conn._password = "wrong-password"
    comm._conn._auth_header = str(comm._conn._auth_header)[:-1]
    yield comm
    comm.close()


def test_create_project_then_find_it_in_the_list(
    communication: Communication, project_name: str
) -> None:
    """A created project shows up in the project-name listing.

    Covers the happy path end to end: a POST with a body, a GET whose response
    is parsed, and the deletion afterwards.
    """
    created = communication.send_request(
        "post",
        AcpPath.PROJECT,
        data={
            "project_name": project_name,
            "project_type": "autograph",
            "project_db_name": DB_NAME,
            "project_description": "Created by the SDK integration tests.",
        },
    )
    try:
        # The response is an AIProject echoing back what was created. Field names
        # arrive camelCased: protobuf JSON renders `project_name` as `projectName`,
        # and that mapping holds across every service.
        assert created["projectName"] == project_name
        assert created["projectType"] == "autograph"
        assert created["projectDbName"] == DB_NAME

        listed = communication.send_request("get", f"{AcpPath.ALL_PROJECT_NAMES}/{DB_NAME}")

        assert "projectNames" in listed
        assert project_name in listed["projectNames"]
    finally:
        # Runs even when the assertions above fail, so a red test does not
        # leave litter behind on a shared deployment.
        communication.send_request("delete", f"{AcpPath.PROJECT}/{DB_NAME}/{project_name}")


def test_unknown_endpoint_raises_service_error_with_404(
    communication: Communication,
) -> None:
    """A path the gateway does not route surfaces as ServiceError, not a raw status.

    This is the contract the whole error hierarchy rests on: the caller branches
    on an exception type and reads ``status_code``, never rely on a returned code.
    """
    with pytest.raises(ServiceError) as excinfo:
        communication.send_request("get", f"{AcpPath.PREFIX}/there_is_no_such_endpoint")

    assert excinfo.value.status_code == 404


def test_send_request_retries_invalid_token(
    communication_invalid_jwt: Communication, project_name: str
) -> None:
    """Tests that send_request refreshes the token if it receives 401 and retries once more."""
    old_token = communication_invalid_jwt._conn._auth_header
    created = communication_invalid_jwt.send_request(
        "post",
        AcpPath.PROJECT,
        data={
            "project_name": project_name,
            "project_type": "autograph",
            "project_db_name": DB_NAME,
            "project_description": "Created by the SDK integration tests.",
        },
    )
    try:
        assert communication_invalid_jwt._conn._auth_header != old_token
        # The response is an AIProject echoing back what was created. Field names
        # arrive camelCased: protobuf JSON renders `project_name` as `projectName`,
        # and that mapping holds across every service.
        assert created["projectName"] == project_name
        assert created["projectType"] == "autograph"
        assert created["projectDbName"] == DB_NAME

        listed = communication_invalid_jwt.send_request(
            "get", f"{AcpPath.ALL_PROJECT_NAMES}/{DB_NAME}"
        )

        assert "projectNames" in listed
        assert project_name in listed["projectNames"]
    finally:
        # Runs even when the assertions above fail, so a red test does not
        # leave litter behind on a shared deployment.
        communication_invalid_jwt.send_request(
            "delete", f"{AcpPath.PROJECT}/{DB_NAME}/{project_name}"
        )


def test_send_request_retries_invalid_token_raises_on_failure(
    communication_wrong_password_and_token: Communication, project_name: str
) -> None:
    """Tests that send_request raises proper error when retry fails."""
    # assert number of retries is one.
    with pytest.raises(AuthenticationError):
        communication_wrong_password_and_token.send_request(
            "post",
            AcpPath.PROJECT,
            data={
                "project_name": project_name,
                "project_type": "autograph",
                "project_db_name": DB_NAME,
                "project_description": "Created by the SDK integration tests.",
            },
        )


def test__authenticate_refresh_token(
    communication_invalid_jwt: Communication,
) -> None:
    """Tests that _authenticate actually refresh the JWT token."""
    jwt_before = communication_invalid_jwt._conn._auth_header
    communication_invalid_jwt._authenticate()
    assert jwt_before != communication_invalid_jwt._conn._auth_header


def test__authenticate_raises_invalid_credentials_error(
    communication_wrong_password: Communication,
) -> None:
    """Test _authenticate method raises InvalidCredentialsError.

    When the token expires while the client is active, the Communication
    class tries to refresh the token using the credentials stored in that
    client object, if it fails, it should raise InvalidCredentialsError
    if the credentials have been invalid meanwhile.
    """
    # if credentials became invlid meanwhile.
    with pytest.raises(expected_exception=InvalidCredentialsError):
        communication_wrong_password._authenticate()


def test__authenticate_raises_server_unreachable_error(
    communication_wrong_url: Communication,
) -> None:
    """Test _authenticate method raises PlatformUnreachableError.

    When the token expires while the client is active, the Communication
    class tries to refresh the token using the credentials stored in that
    client object, if it fails, it should raise PlatformUnreachableError
    if the auth endpoint could not be reached.
    """
    with pytest.raises(expected_exception=PlatformUnreachableError):
        communication_wrong_url._authenticate()


def test_wrong_password_raises_invalid_credentials() -> None:
    """Bad credentials fail at construction, with an SDK exception.

    Authentication is eager, ``db()`` exchanges the credentials for a token
    while the object is being built, so this surfaces here rather than on the
    first request.
    The idea here is to make sure that no `python-arango` exception surfaces here.
    """
    with pytest.raises(InvalidCredentialsError):
        Communication(BASE_URL, USERNAME, "wrong-password", DB_NAME)


def test_unknown_username_raises_invalid_credentials() -> None:
    """An account that does not exist fails the same way as a wrong password.

    Deliberately identical exception to the wrong-password case: the SDK must not let a
    caller tell the two apart.
    """
    with pytest.raises(InvalidCredentialsError):
        Communication(BASE_URL, "no_such_user", PASSWORD, DB_NAME)


def test_nonexistent_database_raises_database_not_found() -> None:
    """A database that does not exist fails at construction, not on first use.

    Authentication alone would not catch this: ``/_open/auth`` is
    database-agnostic. The connection in python-arango is built with ``verify=True``, which sends
    a probe through the database-prefixed URL, so an unknown name comes back
    ``404`` while the object is still being constructed.
    """
    with pytest.raises(DatabaseNotFoundError):
        Communication(BASE_URL, USERNAME, PASSWORD, "no_such_database")


def test_bad_credentials_win_over_a_bad_database() -> None:
    """When both are wrong, the credentials error is the one raised.

    The order matters to anyone writing an ``except`` block: the token exchange
    runs before the database probe, so a user with a wrong password is never
    told to fix their database name instead.
    """
    with pytest.raises(InvalidCredentialsError):
        Communication(BASE_URL, USERNAME, "not-the-password", "no_such_database")


def test_communication_raises_platform_unreachable() -> None:
    with pytest.raises(expected_exception=PlatformUnreachableError):
        Communication("https://wrong_url:8529", USERNAME, "not-the-password", "no_such_database")


def test_a_callable_body_is_rebuilt_for_every_attempt(
    communication_invalid_jwt: Communication, project_name: str
) -> None:
    """The retry after a 401 gets a freshly built body.

    A dict stands in for the body here; what matters is that the builder runs
    once per attempt, which is what lets a one-shot streamed body be retried.
    """
    builds: list[int] = []

    def body() -> dict[str, str]:
        builds.append(len(builds) + 1)
        return {
            "project_name": project_name,
            "project_type": "autograph",
            "project_db_name": DB_NAME,
        }

    created = communication_invalid_jwt.send_request("post", AcpPath.PROJECT, data=body)
    try:
        assert builds == [1, 2]
        assert created["projectName"] == project_name
    finally:
        communication_invalid_jwt.send_request(
            "delete", f"{AcpPath.PROJECT}/{DB_NAME}/{project_name}"
        )


def test_a_per_call_timeout_applies_to_that_call_only(communication: Communication) -> None:
    """A timeout too short to be met fails that call, and the next call is back to the default."""
    default = communication._client.request_timeout

    with pytest.raises(PlatformUnreachableError):
        communication.send_request("get", f"{AcpPath.ALL_PROJECT_NAMES}/{DB_NAME}", timeout=0.0001)

    assert communication._client.request_timeout == default
    listed = communication.send_request("get", f"{AcpPath.ALL_PROJECT_NAMES}/{DB_NAME}")
    assert "projectNames" in listed
