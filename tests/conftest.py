"""Load a local ``.env`` so integration tests can use real endpoints.

CI does not ship this file. Copy ``.env.example`` to ``.env`` and fill in
values. The file is gitignored.
"""

import os
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest
from dotenv import load_dotenv

from arango_ai_sdk._naming import EnvVar
from arango_ai_sdk.communication import Communication

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

BASE_URL = os.environ.get(EnvVar.ARANGO_DEPLOYMENT_ENDPOINT, "")
DB_NAME = os.environ.get(EnvVar.ARANGO_SDK_TEST_DB, "sdk_test")
USERNAME = os.environ.get(EnvVar.ARANGO_SDK_TEST_USERNAME, "sdk_test")
PASSWORD = os.environ.get(EnvVar.ARANGO_SDK_TEST_PASSWORD, "")


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
