"""Mark and gate every test under ``tests/integration``.

All tests in this directory hit a live platform. Instead of repeating the
``integration`` marker and the credentials ``skipif`` in each module, this hook
adds both to every test collected here.
"""

import os
from pathlib import Path

import pytest

from arango_ai_sdk._naming import EnvVar

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
    missing = [name for name in _REQUIRED if not os.environ.get(name)]
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
