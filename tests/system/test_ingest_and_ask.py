"""Ingest the demo corpus and ask a retriever, against a live platform.

Marker, credential skip, and the readiness wait come from
``tests/system/conftest.py``. One fixture uploads and ingests; the second
test deploys AutoRAG on that project. Cleanup runs even when a step fails.
"""

import contextlib
import os
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

from arango_ai_sdk._naming import AcpPath, EnvVar, FileManagerPath
from arango_ai_sdk.autograph import DEFAULT_READY_TIMEOUT, IngestResult, JobState
from arango_ai_sdk.communication import Communication
from arango_ai_sdk.exceptions import ServiceError
from arango_ai_sdk.files import FileManager
from arango_ai_sdk.project_handle import AiProjectHandle
from arango_ai_sdk.projects import ProjectManager
from arango_ai_sdk.secret_profiles import SecretProfileManager

# tests/system/test_*.py -> repo root. The same layout is copied into the test image.
CORPUS = Path(__file__).resolve().parents[2] / "examples" / "sdk-demo" / "corpus"
CATEGORIES = ("bbc-news", "bloomberg-news")
# Shorter than the CI job so a stuck ingest fails here, with the step named,
# instead of the job being killed with no test result.
INGEST_TIMEOUT = 45 * 60

DB_NAME = os.environ.get(EnvVar.ARANGO_SDK_TEST_DB, "")


@dataclass
class Ingested:
    """A project whose demo categories have been through ``ingest``."""

    project: AiProjectHandle
    result: IngestResult
    chat_profile_id: str
    embed_profile_id: str


def _communication() -> Communication:
    return Communication(
        os.environ[EnvVar.ARANGO_DEPLOYMENT_ENDPOINT],
        os.environ[EnvVar.ARANGO_SDK_TEST_USERNAME],
        os.environ[EnvVar.ARANGO_SDK_TEST_PASSWORD],
        os.environ[EnvVar.ARANGO_SDK_TEST_DB],
        verify=os.environ.get(EnvVar.ARANGO_SDK_TEST_TLS_VERIFY, "true").lower() != "false",
    )


def _delete_uploaded(communication: Communication, project_name: str) -> None:
    """Delete every file uploaded under this project, both categories."""
    path = f"{FileManagerPath.PREFIX}/{DB_NAME}/{FileManagerPath.RAG_INPUT}"
    listed = communication.send_request(
        "get", path, params={"scope": project_name, "limit": "1000"}
    )
    ids = [
        stored["id"]
        for stored in listed["files"]
        if (stored.get("scope") or [])[:1] == [project_name]
    ]
    if ids:
        communication.send_request("post", f"{path}/delete", data={"ids": ids})


@pytest.fixture(scope="module")
def ingested() -> Iterator[Ingested]:
    """Upload the demo corpus, deploy AutoGraph, ingest, and always clean up."""
    communication = _communication()
    projects = ProjectManager(communication=communication, db_name=DB_NAME)
    secrets = SecretProfileManager(communication=communication)
    project_name = f"sdk_test_{uuid.uuid4().hex[:8]}"
    secret_name = f"sdk_test_{uuid.uuid4().hex[:8]}"
    sales = None
    chat = None
    embed = None
    try:
        sales = projects.create(project_name=project_name, project_type="autograph")
        chat = secrets.create(
            name=f"{secret_name}-chat",
            secret=os.environ[EnvVar.ARANGO_SDK_TEST_CHAT_API_KEY],
            provider="openai",
        )
        embed = secrets.create(
            name=f"{secret_name}-embed",
            secret=os.environ[EnvVar.ARANGO_SDK_TEST_EMBEDDING_API_KEY],
            provider="openai",
        )
        files = FileManager(communication, db_name=DB_NAME)
        for category in CATEGORIES:
            uploaded = files.upload_folder(CORPUS / category, scope=[project_name, category])
            assert uploaded, f"{category} has no files"
            assert all(item.status == "ok" for item in uploaded), category

        # Not wait=True: waiting inside deploy can outlive the platform request.
        sales.autograph.deploy(
            chat_api_provider="openai",
            embedding_api_provider="openai",
            chat_secret_profile_id=chat.profile_id,
            embedding_secret_profile_id=embed.profile_id,
            fps_recovery_username="fps-recovery",
            chat_model="gpt-4o",
            embedding_model="text-embedding-3-small",
        )
        assert sales.autograph.wait_until_ready(timeout=DEFAULT_READY_TIMEOUT)
        result = sales.autograph.ingest(CATEGORIES, timeout=INGEST_TIMEOUT)
        yield Ingested(
            project=sales,
            result=result,
            chat_profile_id=chat.profile_id,
            embed_profile_id=embed.profile_id,
        )
    finally:
        if sales is not None:
            with contextlib.suppress(ServiceError):
                for retriever in sales.autorag.list():
                    with contextlib.suppress(ServiceError):
                        retriever.undeploy()
            with contextlib.suppress(ServiceError):
                sales.autograph.undeploy()
        with contextlib.suppress(ServiceError):
            _delete_uploaded(communication, project_name)
        if chat is not None:
            with contextlib.suppress(ServiceError):
                communication.send_request("delete", f"{AcpPath.SECRETS}/{chat.profile_id}")
        if embed is not None:
            with contextlib.suppress(ServiceError):
                communication.send_request("delete", f"{AcpPath.SECRETS}/{embed.profile_id}")
        if sales is not None:
            with contextlib.suppress(ServiceError):
                communication.send_request("delete", f"{AcpPath.PROJECT}/{DB_NAME}/{project_name}")
        communication.close()


def test_ingest_completes(ingested: Ingested) -> None:
    """The demo categories build, get strategies, and import."""
    assert ingested.result.build.status == JobState.COMPLETED
    assert not ingested.result.build.error_code
    assert ingested.result.strategize.status == JobState.COMPLETED
    assert ingested.result.orchestration is not None
    assert ingested.result.orchestration.status == JobState.COMPLETED


def test_ask_returns_an_answer(ingested: Ingested) -> None:
    """A retriever on the ingested project answers and is then removed."""
    project = ingested.project
    deployed = project.autorag.deploy(
        chat_api_provider="openai",
        embedding_api_provider="openai",
        chat_secret_profile_id=ingested.chat_profile_id,
        embedding_secret_profile_id=ingested.embed_profile_id,
        chat_model="gpt-4o",
        embedding_model="text-embedding-3-small",
    )
    rag = deployed.autorag
    assert rag.wait_until_ready(timeout=DEFAULT_READY_TIMEOUT)
    answer = rag.ask("What do the articles say about drones?")
    assert answer.result.strip()
    assert answer.run_id
    removed = rag.undeploy()
    assert removed.service_id == rag.service_id
    assert rag.is_deployed is False
