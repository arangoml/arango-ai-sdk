"""Ingest the demo corpus and ask a retriever, against a live platform.

The ``system`` marker keeps this out of the short integration run. Credential
skip and the readiness wait come from ``tests/integration/conftest.py``. One
fixture uploads and ingests; the second test deploys AutoRAG on that project.
Cleanup runs even when a step fails.
"""

import contextlib
import os
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

from arango_ai_sdk._naming import AcpPath, EnvVar, FileManagerPath
from arango_ai_sdk.client import ArangoAIClient
from arango_ai_sdk.communication import Communication
from arango_ai_sdk.exceptions import CommunicationError
from arango_ai_sdk.projects.handle import AiProjectHandle
from arango_ai_sdk.projects.services.autograph.service import (
    DEFAULT_READY_TIMEOUT,
    IngestResult,
    JobState,
)

pytestmark = pytest.mark.system

# tests/integration/test_*.py -> repo root. The same layout is copied into the test image.
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
def ingested(file_manager_ready: None) -> Iterator[Ingested]:
    """Upload the demo corpus, deploy AutoGraph, ingest, and always clean up."""
    verify = os.environ.get(EnvVar.ARANGO_SDK_TEST_TLS_VERIFY, "true").lower() != "false"
    client = ArangoAIClient(
        os.environ[EnvVar.ARANGO_DEPLOYMENT_ENDPOINT],
        os.environ[EnvVar.ARANGO_SDK_TEST_USERNAME],
        os.environ[EnvVar.ARANGO_SDK_TEST_PASSWORD],
        os.environ[EnvVar.ARANGO_SDK_TEST_DB],
        verify=verify,
    )
    project_name = f"sdk_test_{uuid.uuid4().hex[:8]}"
    secret_name = f"sdk_test_{uuid.uuid4().hex[:8]}"
    sales = None
    chat = None
    embed = None
    try:
        sales = client.project.create(project_name=project_name, project_type="autograph")
        chat = client.secret_profile.create(
            name=f"{secret_name}-chat",
            secret=os.environ[EnvVar.ARANGO_SDK_TEST_CHAT_API_KEY],
            provider="openai",
        )
        embed = client.secret_profile.create(
            name=f"{secret_name}-embed",
            secret=os.environ[EnvVar.ARANGO_SDK_TEST_EMBEDDING_API_KEY],
            provider="openai",
        )
        for category in CATEGORIES:
            uploaded = client.files.upload_folder(CORPUS / category, scope=[project_name, category])
            assert uploaded, f"{category} has no files"
            assert all(item.status == "ok" for item in uploaded), category

        # Not wait=True: waiting inside deploy can outlive the platform request.
        sales.autograph.deploy(
            chat_api_provider="openai",
            embedding_api_provider="openai",
            chat_secret_profile_id=chat.profile_id,
            embedding_secret_profile_id=embed.profile_id,
            fps_recovery_username=os.environ[EnvVar.ARANGO_SDK_TEST_USERNAME],
            chat_model="gpt-4o",
            embedding_model="text-embedding-3-small",
        )
        assert sales.autograph.wait_until_ready(timeout=DEFAULT_READY_TIMEOUT)
        result = sales.autograph.ingest(
            CATEGORIES,
            timeout=INGEST_TIMEOUT,
            on_progress=lambda progress: print(
                f"{progress.step}: {progress.status.status}", flush=True
            ),
        )
        yield Ingested(
            project=sales,
            result=result,
            chat_profile_id=chat.profile_id,
            embed_profile_id=embed.profile_id,
        )
    finally:
        if sales is not None:
            with contextlib.suppress(CommunicationError):
                for retriever in sales.autorag.list():
                    with contextlib.suppress(CommunicationError):
                        retriever.undeploy()
            with contextlib.suppress(CommunicationError):
                sales.autograph.undeploy()
        with contextlib.suppress(CommunicationError):
            _delete_uploaded(client.communication, project_name)
        if chat is not None:
            with contextlib.suppress(CommunicationError):
                client.communication.send_request("delete", f"{AcpPath.SECRETS}/{chat.profile_id}")
        if embed is not None:
            with contextlib.suppress(CommunicationError):
                client.communication.send_request("delete", f"{AcpPath.SECRETS}/{embed.profile_id}")
        if sales is not None:
            with contextlib.suppress(CommunicationError):
                client.communication.send_request(
                    "delete", f"{AcpPath.PROJECT}/{DB_NAME}/{project_name}"
                )
        client.close()


def test_ingest_completes(ingested: Ingested) -> None:
    """The demo categories build, get strategies, and import."""
    assert ingested.result.build.status == JobState.COMPLETED
    assert not ingested.result.build.error_code
    assert ingested.result.build.document_count == 10
    assert ingested.result.strategize.status == JobState.COMPLETED
    assert ingested.result.strategies.total_strategies > 0
    assert ingested.result.orchestration is not None
    assert ingested.result.orchestration.status == JobState.COMPLETED
    assert ingested.result.orchestration.failed_jobs == 0


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
