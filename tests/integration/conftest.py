"""Mark and gate every test under ``tests/integration``.

All tests in this directory hit a live platform. Instead of repeating the
``integration`` marker and the credentials ``skipif`` in each module, this hook
adds both to every test collected here. A session fixture then waits until the
platform routes the services the tests call.
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


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Add the ``integration`` marker and the credentials skip to tests in this directory.

    This hook is captured automatically by pytest and executed at test collection.
    """
    # `is None`, not falsy: the CI deployment's root account has an empty password.
    missing = [name for name in _REQUIRED if os.environ.get(name) is None]
    skip = pytest.mark.skip(
        reason=f"{', '.join(_REQUIRED)} must all be set for live-platform tests "
        f"(missing: {', '.join(missing)})"
    )
    for item in items:
        if not item.path.is_relative_to(_HERE):
            continue
        item.add_marker(pytest.mark.integration)
        if missing:
            item.add_marker(skip)


_HEALTH_PATHS = (AcpPath.HEALTH, FileManagerPath.HEALTH)
_READY_TIMEOUT = 5 * 60
_READY_INTERVAL = 2


@pytest.fixture(scope="session", autouse=True)
def platform_ready() -> None:
    """Wait until the gateway routes ACP and the file service.

    In CI the test pod starts as soon as the services are installed, before the
    gateway has registered their routes, and every request answers 404 for a
    few seconds. Polling the health endpoints until both answer removes that
    race. On a platform that is already up this costs one request per service.
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
        for path in _HEALTH_PATHS:
            while True:
                try:
                    comm.send_request("get", path)
                    break
                except (ServiceError, PlatformUnreachableError) as exc:
                    if time.monotonic() >= deadline:
                        pytest.fail(f"{path} did not answer within {_READY_TIMEOUT}s: {exc}")
                    time.sleep(_READY_INTERVAL)
    finally:
        comm.close()
