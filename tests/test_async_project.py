import json
from pathlib import Path

import httpx
import pytest
import respx

from arango_ai import AsyncClient
from arango_ai.acp import ACP_BASE
from arango_ai.autograph import AsyncAutoGraphProject

from .conftest import BASE, make_jwt
from .test_project_facade import PROJECT, _manifest_entries, _ndjson

FM_BASE = f"{BASE}/_platform/filemanager/_db/testdb/rag-input"
AG_BASE = f"{BASE}/autograph/wzfue"


@pytest.fixture(autouse=True)
def _auth() -> None:
    respx.post(f"{BASE}/_open/auth").respond(json={"jwt": make_jwt()})
    respx.get(f"{BASE}{ACP_BASE}/project_by_name/testdb/demo").respond(json=PROJECT)


@pytest.fixture
def project(async_client: AsyncClient) -> AsyncAutoGraphProject:
    # Construct the handle directly: the bind-time existence GET would fire
    # before @respx.mock activates (bind itself is covered in the ACP tests).
    return AsyncAutoGraphProject(async_client, "demo")


# -- add_files --------------------------------------------------------------


@respx.mock
async def test_add_files_paths_with_citable_urls(project, tmp_path: Path) -> None:
    doc = tmp_path / "report.pdf"
    doc.write_bytes(b"pdf-bytes")
    upload = respx.post(f"{FM_BASE}/batch").respond(
        json={"results": [{"name": "report.pdf", "status": "ok"}]}
    )

    result = await project.add_files(
        [doc],
        category="tech",
        citable_urls={"report.pdf": "https://example.com/report"},
    )

    assert [entry["name"] for entry in result.ok] == ["report.pdf"]
    manifest = _manifest_entries(upload.calls[0].request.content)
    assert manifest[0]["scope"] == ["demo", "tech"]
    assert manifest[0]["custom_metadata"] == {
        "citable_url": "https://example.com/report"
    }


# -- workflow chain -----------------------------------------------------------


@respx.mock
async def test_build_wait_chain(project) -> None:
    respx.post(f"{AG_BASE}/v1/corpus/builds").respond(
        json={"corpusBuildId": "b-1", "graphName": "demo_CorpusGraph"}
    )
    status = respx.get(f"{AG_BASE}/v1/corpus/builds/b-1")
    status.side_effect = [
        httpx.Response(200, json={"status": "running", "progress": 40}),
        httpx.Response(200, json={"status": "completed", "documentCount": 3}),
    ]

    run = await project.build()
    outcome = await run.wait(interval=0)

    assert run.build_id == "b-1"
    assert run.graph_name == "demo_CorpusGraph"
    assert outcome["documentCount"] == 3


@respx.mock
async def test_strategize_blocking_returns_plan(project) -> None:
    respx.post(f"{AG_BASE}/v1/rag-strategizer/analyze").respond(
        json={"strategizeJobId": "j-1"}
    )
    respx.get(f"{AG_BASE}/v1/rag-strategizer/jobs/j-1").respond(
        json={"status": "completed"}
    )
    respx.get(f"{AG_BASE}/v1/rag-strategizer/strategy").respond(
        json={"strategies": [], "totalStrategies": 4}
    )

    plan = await project.strategize("moderate")

    assert plan["totalStrategies"] == 4


@respx.mock
async def test_orchestrate_wait_chain_resolves_secrets(project) -> None:
    orchestrate = respx.post(f"{AG_BASE}/v1/orchestrate").respond(
        json={"orchestrationId": "o-1", "success": True}
    )
    respx.get(f"{AG_BASE}/v1/orchestrate/o-1").respond(
        json={"status": "completed", "totalJobs": 2, "completedJobs": 2}
    )

    run = await project.orchestrate()
    outcome = await run.wait(interval=0)

    assert outcome["completedJobs"] == 2
    body = json.loads(orchestrate.calls[0].request.content)
    # Secret ids resolved from the project's persisted model settings.
    assert body["chatSecretProfileIds"] == ["p-chat"]
    assert body["embeddingSecretProfileId"] == "p-emb"


# -- retrieval facade -----------------------------------------------------------


@respx.mock
async def test_deploy_retriever_defaults_from_model_settings(project) -> None:
    service = respx.post(f"{BASE}{ACP_BASE}/service").respond(
        json={
            "serviceInfo": {
                "serviceId": "arangodb-graphrag-retriever-xyz-0",
                "status": "DEPLOYING",
            }
        }
    )

    info = await project.deploy_retriever(wait=False)

    body = json.loads(service.calls[0].request.content)
    assert body["service_name"] == "arangodb-graphrag-retriever"
    env = body["env"]
    assert env["chat_model"] == "gpt-4.1"
    assert env["embedding_model"] == "text-embedding-3-small"
    assert env["chat_secret_profile_id"] == "p-chat"
    assert env["embedding_secret_profile_id"] == "p-emb"
    assert info["serviceId"] == "arangodb-graphrag-retriever-xyz-0"


@respx.mock
async def test_ask_resolves_single_metadata_retriever(project) -> None:
    query = respx.post(
        f"{BASE}/graphrag/retriever/abc-0/v1/graphrag-query-stream"
    ).respond(
        content=_ndjson(
            {"runId": "r-1", "delta": "The answer"},
            {"isFinal": True, "finalResult": "The answer."},
        )
    )

    result = await project.ask("question?")

    assert str(result) == "The answer."
    assert result.run_id == "r-1"
    assert query.called


@respx.mock
async def test_ask_stream_yields_events(project) -> None:
    respx.post(f"{BASE}/graphrag/retriever/abc-0/v1/graphrag-query-stream").respond(
        content=_ndjson({"delta": "The answer"}, {"isFinal": True})
    )

    events = [event async for event in project.ask_stream("question?")]

    assert [type(e).__name__ for e in events] == ["TokenDelta", "Final"]
    assert events[-1].result.answer == "The answer"


# -- health gate --------------------------------------------------------------


@respx.mock
async def test_wait_until_serving_transport_flap_keeps_polling(project) -> None:
    health = respx.get(f"{AG_BASE}/v1/health")
    health.side_effect = [
        httpx.ConnectError("boom"),
        httpx.Response(200),
        httpx.Response(200),
        httpx.Response(200),
    ]

    await project.wait_until_serving(timeout=5, interval=0)

    assert health.call_count == 4


# -- teardown -------------------------------------------------------------------


@respx.mock
async def test_delete_uses_service_teardown_when_deployed(project) -> None:
    teardown = respx.delete(f"{AG_BASE}/v1/projects/demo").respond(
        json={"deleted": True, "warnings": ["views pending"]}
    )
    acp_delete = respx.delete(f"{BASE}{ACP_BASE}/project/testdb/demo").respond(
        json={"success": True}
    )

    result = await project.delete()

    assert result["deleted"] is True
    assert result["warnings"] == ["views pending"]
    assert teardown.calls[0].request.url.params["delete_files"] == "true"
    assert not acp_delete.called


@respx.mock
async def test_delete_falls_back_to_acp_without_service(async_client) -> None:
    respx.get(f"{BASE}{ACP_BASE}/project_by_name/testdb/bare").respond(
        json={"projectName": "bare", "projectType": "autograph"}
    )
    acp_delete = respx.delete(f"{BASE}{ACP_BASE}/project/testdb/bare").respond(
        json={"success": True}
    )

    result = await AsyncAutoGraphProject(async_client, "bare").delete()

    # Normalized to the service-teardown shape (no key-sniffing the phase).
    assert result == {"deleted": True, "warnings": []}
    assert acp_delete.called
