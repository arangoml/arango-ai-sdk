"""Mark and gate every test under ``tests/system``.

These tests ingest a real corpus and ask a retriever. They need a live
platform and provider keys, and CI runs them only from main and the nightly
workflow. A laptop run without those settings skips them.
"""

import os
import time
from pathlib import Path

import pytest

from arango_ai_sdk._naming import AcpPath, EnvVar, FileManagerPath
from arango_ai_sdk.communication import Communication
from arango_ai_sdk.exceptions import PlatformUnreachableError, ServiceError

_HERE = Path(__file__).resolve().parent

# Set on the system-test pod. A missing key then fails the job instead of
# skipping, so a misconfigured main run cannot pass.
_REQUIRE = "ARANGO_SDK_REQUIRE_SYSTEM_TESTS"

_REQUIRED = (
    EnvVar.ARANGO_DEPLOYMENT_ENDPOINT,
    EnvVar.ARANGO_SDK_TEST_DB,
    EnvVar.ARANGO_SDK_TEST_USERNAME,
    EnvVar.ARANGO_SDK_TEST_PASSWORD,
    EnvVar.ARANGO_SDK_TEST_CHAT_API_KEY,
    EnvVar.ARANGO_SDK_TEST_EMBEDDING_API_KEY,
)

_READY_TIMEOUT = 5 * 60
_READY_INTERVAL = 2


def _missing() -> list[str]:
    # `is None`, not falsy: the CI deployment's root account has an empty password.
    return [name for name in _REQUIRED if os.environ.get(name) is None]


def _required() -> bool:
    return os.environ.get(_REQUIRE, "").lower() == "true"


def pytest_sessionstart(session: pytest.Session) -> None:
    """Fail the session when CI required this run and a setting is missing."""
    missing = _missing()
    if _required() and missing:
        pytest.exit(
            "System tests are required but missing: " + ", ".join(missing),
            returncode=1,
        )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Add the ``system`` marker, and skip the tests when settings are absent."""
    missing = _missing()
    skip = pytest.mark.skip(
        reason=f"{', '.join(_REQUIRED)} must all be set for system tests "
        f"(missing: {', '.join(missing)})"
    )
    for item in items:
        if not item.path.is_relative_to(_HERE):
            continue
        item.add_marker(pytest.mark.system)
        if missing and not _required():
            item.add_marker(skip)


def _wait_for(path: str) -> None:
    """Poll a health endpoint until it answers, or fail after the timeout."""
    if _missing():
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
def platform_ready() -> None:
    """Wait until the gateway routes ACP and the file service."""
    _wait_for(AcpPath.HEALTH)
    _wait_for(FileManagerPath.HEALTH)
