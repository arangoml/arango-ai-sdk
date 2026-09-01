"""Integration tests for :class:`Communication`, against a live platform.

Integration tests that open real connections to the devstack deployment,
create and delete real projects, and need real credentials. They are skipped
automatically unless ``ARANGO_SDK_TEST_PASSWORD`` is set, so CI -- which has
neither the credentials nor a route to the pilot -- stays green without extra
configuration.

To run them::

    export ARANGO_DEPLOYMENT_ENDPOINT='https://deployment.<cluster>.svc:8529'
    export ARANGO_SDK_TEST_PASSWORD='...'   # single quotes: the password contains $ and !
    uv run pytest tests/test_communication.py -v

The endpoints exercised here belong to ACP Service (``proto/genai.proto``):
create a project, list project names, delete a project.

Note: pytest prints function arguments in tracebacks, so a failure here puts the
password on screen. Harmless locally, you typed it into the same terminal,
but do not paste raw failure output into a ticket or a chat.
Moreover, a test user and test database have been created in the EU devstack for
dev purposes.
"""

import os
import uuid
from collections.abc import Iterator

import pytest

from arango_ai_sdk._naming import EnvVar
from arango_ai_sdk.communication import Communication
from arango_ai_sdk.exceptions import (
    DatabaseNotFoundError,
    InvalidCredentialsError,
    ServiceError,
)

BASE_URL = os.environ.get(EnvVar.ARANGO_DEPLOYMENT_ENDPOINT, "")
DB_NAME = "sdk_test"
USERNAME = "sdk_test"
PASSWORD = os.environ.get(EnvVar.ARANGO_SDK_TEST_PASSWORD, "")

# AI service sits behind this prefix on the gateway. The proto paths are
# relative to it, so `post: "/v1/project"` is reached at "/ai/v1/project".
AI_PREFIX = "/ai/v1"

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not (BASE_URL and PASSWORD),
        reason=(
            f"{EnvVar.ARANGO_DEPLOYMENT_ENDPOINT} and {EnvVar.ARANGO_SDK_TEST_PASSWORD} must both "
            "be set for live-platform tests"
        ),
    ),
]


@pytest.fixture
def communication() -> Iterator[Communication]:
    """Open an authenticated connection to the pilot platform, and close it after."""
    comm = Communication(BASE_URL, USERNAME, PASSWORD, DB_NAME)
    yield comm
    comm.close()


@pytest.fixture
def project_name() -> str:
    """Return a project name unique to this run, so parallel runs cannot collide."""
    return f"sdk_test_{uuid.uuid4().hex[:8]}"


def test_create_project_then_find_it_in_the_list(
    communication: Communication, project_name: str
) -> None:
    """A created project shows up in the project-name listing.

    Covers the happy path end to end: a POST with a body, a GET whose response
    is parsed, and the deletion afterwards.
    """
    created = communication.send_request(
        "post",
        f"{AI_PREFIX}/project",
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

        listed = communication.send_request("get", f"{AI_PREFIX}/all_project_names/{DB_NAME}")

        assert "projectNames" in listed
        assert project_name in listed["projectNames"]
    finally:
        # Runs even when the assertions above fail, so a red test does not
        # leave litter behind on a shared deployment.
        communication.send_request("delete", f"{AI_PREFIX}/project/{DB_NAME}/{project_name}")


def test_unknown_endpoint_raises_service_error_with_404(
    communication: Communication,
) -> None:
    """A path the gateway does not route surfaces as ServiceError, not a raw status.

    This is the contract the whole error hierarchy rests on: the caller branches
    on an exception type and reads ``status_code``, never rely on a returned code.
    """
    with pytest.raises(ServiceError) as excinfo:
        communication.send_request("get", f"{AI_PREFIX}/there_is_no_such_endpoint")

    assert excinfo.value.status_code == 404


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
