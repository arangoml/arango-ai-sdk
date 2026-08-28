"""Integration tests for :class:`Communication`, against a live platform.

These are not unit tests. They open real connections to the pilot deployment,
create and delete real projects, and need real credentials. They are skipped
automatically unless ``ARANGO_SDK_TEST_PASSWORD`` is set, so CI -- which has
neither the credentials nor a route to the pilot -- stays green without extra
configuration.

To run them::

    export ARANGO_SDK_TEST_PASSWORD='...'
    uv run pytest tests/test_communication.py -v

The endpoints exercised here belong to GenAI-Service (``proto/genai.proto``):
create a project, list project names, delete a project.
"""

import os
import uuid
from collections.abc import Iterator

import pytest

from arango_ai_sdk.communication import Communication
from arango_ai_sdk.exceptions import InvalidCredentialsError, ServiceError

BASE_URL = "https://h9tcixq7.rnd.pilot.arango.ai"
DB_NAME = "sdk_test"
USERNAME = "sdk_test"
PASSWORD = os.environ.get("ARANGO_SDK_TEST_PASSWORD", "")

# Every AI service sits behind this prefix on the gateway. The proto paths are
# relative to it, so `post: "/v1/project"` is reached at "/ai/v1/project".
AI_PREFIX = "/ai"

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not PASSWORD,
        reason="ARANGO_SDK_TEST_PASSWORD is not set, skipping live-platform tests",
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
        f"{AI_PREFIX}/v1/project",
        data={
            "project_name": project_name,
            "project_type": "graphrag",
            "project_db_name": DB_NAME,
            "project_description": "Created by the SDK integration tests.",
        },
    )
    assert created is not None

    try:
        listed = communication.send_request("get", f"{AI_PREFIX}/v1/all_project_names/{DB_NAME}")

        # The wire format is protobuf JSON, which renders `project_names` as
        # `projectNames`. Fields arrive camelCased across every service.
        assert "projectNames" in listed
        assert project_name in listed["projectNames"]
    finally:
        # Runs even when the assertions above fail, so a red test does not
        # leave litter behind on a shared deployment.
        communication.send_request("delete", f"{AI_PREFIX}/v1/project/{DB_NAME}/{project_name}")


def test_deleted_project_is_gone_from_the_list(
    communication: Communication, project_name: str
) -> None:
    """Deletion actually removes the project, rather than reporting success."""
    communication.send_request(
        "post",
        f"{AI_PREFIX}/v1/project",
        data={
            "project_name": project_name,
            "project_type": "graphrag",
            "project_db_name": DB_NAME,
        },
    )
    communication.send_request("delete", f"{AI_PREFIX}/v1/project/{DB_NAME}/{project_name}")

    listed = communication.send_request("get", f"{AI_PREFIX}/v1/all_project_names/{DB_NAME}")
    assert project_name not in listed.get("projectNames", [])


def test_unknown_endpoint_raises_service_error_with_404(
    communication: Communication,
) -> None:
    """A path the gateway does not route surfaces as ServiceError, not a raw status.

    This is the contract the whole error hierarchy rests on: the caller branches
    on an exception type and reads ``status_code``, never on a returned code.
    """
    with pytest.raises(ServiceError) as excinfo:
        communication.send_request("get", f"{AI_PREFIX}/v1/there_is_no_such_endpoint")

    assert excinfo.value.status_code == 404


def test_wrong_password_raises_invalid_credentials() -> None:
    """Bad credentials fail at construction, with an SDK exception.

    Authentication is eager -- ``db()`` exchanges the credentials for a token
    while the object is being built -- so this surfaces here rather than on the
    first request. No ``python-arango`` exception may escape.
    """
    with pytest.raises(InvalidCredentialsError):
        Communication(BASE_URL, USERNAME, "definitely-not-the-password", DB_NAME)


def test_unknown_username_raises_invalid_credentials() -> None:
    """An account that does not exist fails the same way as a wrong password.

    Deliberately identical to the wrong-password case: the SDK must not let a
    caller tell the two apart, since that difference is what account enumeration
    is built on.
    """
    with pytest.raises(InvalidCredentialsError):
        Communication(BASE_URL, "no_such_user", PASSWORD, DB_NAME)


def test_nonexistent_database_still_connects(project_name: str) -> None:
    """A database that does not exist does not fail at construction.

    Worth pinning down because it is surprising. Authentication goes to
    ``/_open/auth``, which is database-agnostic, and every later request is sent
    with ``skip_db_prefix=True`` -- so ``db_name`` never reaches a URL and the
    platform is never asked whether it exists.

    If the SDK should reject an unknown database, that is a deliberate extra
    check we would have to add; it is not something the current design detects.
    """
    comm = Communication(BASE_URL, USERNAME, PASSWORD, "no_such_database")
    try:
        # Connecting succeeded. The database name only matters where a service
        # takes it as a path parameter, and there it is the service that judges.
        listed = comm.send_request("get", f"{AI_PREFIX}/v1/all_project_names/no_such_database")
        assert listed.get("projectNames", []) == []
    finally:
        comm.close()
