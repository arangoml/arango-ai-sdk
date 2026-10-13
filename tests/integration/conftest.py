"""Mark and gate every test under ``tests/integration``.

All tests in this directory hit a live platform. Instead of repeating the
``integration`` marker and the credentials ``skipif`` in each module, this hook
adds both to every test collected here. A test marked ``system`` also needs the
provider keys. When the CI job requires those tests, a missing key fails the
session; otherwise that test is skipped. Session fixtures then wait until the
platform routes the services a test calls.
"""

import os
import time
from pathlib import Path

import pytest

from arango_ai_sdk._naming import AcpPath, EnvVar, FileManagerPath
from arango_ai_sdk.communication import Communication
from arango_ai_sdk.exceptions import PlatformUnreachableError, ServiceError

_HERE = Path(__file__).resolve().parent

_REQUIRED = (
    EnvVar.ARANGO_DEPLOYMENT_ENDPOINT,
    EnvVar.ARANGO_SDK_TEST_DB,
    EnvVar.ARANGO_SDK_TEST_USERNAME,
    EnvVar.ARANGO_SDK_TEST_PASSWORD,
)

_SYSTEM_REQUIRED = (
    EnvVar.ARANGO_SDK_TEST_CHAT_API_KEY,
    EnvVar.ARANGO_SDK_TEST_EMBEDDING_API_KEY,
)

# Set on the test pod when the job includes the system tests. A missing key
# then fails the job instead of skipping, so a misconfigured main run cannot pass.
_REQUIRE_SYSTEM = "ARANGO_SDK_REQUIRE_SYSTEM_TESTS"


def _system_required() -> bool:
    return os.environ.get(_REQUIRE_SYSTEM, "").lower() == "true"


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Add the ``integration`` marker and the credentials skip to tests in this directory.

    This hook is captured automatically by pytest and executed at test collection.
    A ``system`` test also needs the provider keys, and fails the session when
    the CI job required it and one of those keys is missing.
    """
    for item in items:
        if not item.path.is_relative_to(_HERE):
            continue
        item.add_marker(pytest.mark.integration)
        # `is None`, not falsy: the CI deployment's root account has an empty password.
        required = _REQUIRED
        if item.get_closest_marker("system"):
            required += _SYSTEM_REQUIRED
        missing = [name for name in required if os.environ.get(name) is None]
        if not missing:
            continue
        if item.get_closest_marker("system") and _system_required():
            pytest.exit(
                "system tests are required but missing: " + ", ".join(missing),
                returncode=1,
            )
        item.add_marker(
            pytest.mark.skip(
                reason=f"{', '.join(required)} must all be set for live-platform tests "
                f"(missing: {', '.join(missing)})"
            )
        )


_READY_TIMEOUT = 5 * 60
_READY_INTERVAL = 2


def _wait_for(path: str) -> None:
    """Poll a health endpoint until it answers, or fail after the timeout.

    In CI the test pod starts as soon as the services are installed, before the
    gateway has registered their routes, and every request answers 404 for a
    few seconds. On a platform that is already up this costs one request.
    """
    if any(os.environ.get(name) is None for name in _REQUIRED):
        return
    comm = Communication(
        os.environ[EnvVar.ARANGO_DEPLOYMENT_ENDPOINT],
        os.environ[EnvVar.ARANGO_SDK_TEST_USERNAME],
        os.environ[EnvVar.ARANGO_SDK_TEST_PASSWORD],
        os.environ[EnvVar.ARANGO_SDK_TEST_DB],
        verify=os.environ.get(EnvVar.ARANGO_SDK_TEST_TLS_VERIFY, "true").lower() != "false",
    )
    try:
        deadline = time.monotonic() + _READY_TIMEOUT
        while True:
            try:
                comm.send_request("get", path)
                return
            except (ServiceError, PlatformUnreachableError) as exc:
                if time.monotonic() >= deadline:
                    pytest.fail(f"{path} did not answer within {_READY_TIMEOUT}s: {exc}")
                time.sleep(_READY_INTERVAL)
    finally:
        comm.close()


@pytest.fixture(scope="session", autouse=True)
def acp_ready() -> None:
    """Wait until the gateway routes ACP; every test here calls it."""
    _wait_for(AcpPath.HEALTH)


@pytest.fixture(scope="session")
def file_manager_ready() -> None:
    """Wait until the gateway routes the file service; only the file tests need it."""
    _wait_for(FileManagerPath.HEALTH)
