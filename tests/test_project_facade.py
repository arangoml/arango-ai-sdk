import copy
import json
from pathlib import Path

import httpx
import pytest
import respx

from arango_ai import AuthenticationError, ConfigError, FileUpload, ServiceNotReadyError
from arango_ai.acp import ACP_BASE

from .conftest import BASE, make_jwt

FM_BASE = f"{BASE}/_platform/filemanager/_db/testdb/rag-input"
AG_BASE = f"{BASE}/autograph/wzfue"
PROJECT = {
    "projectName": "demo",
    "projectType": "autograph",
    "projectMetadata": {
        "autographService": {"serviceUrl": "https://internal/autograph/wzfue/"},
        "retrieverServices": [
            {"serviceId": "arangodb-graphrag-retriever-abc-0", "status": "DEPLOYED"}
        ],
    },
    "modelSettings": {
        "chatModel": "gpt-4.1",
        "chatApiProvider": "openai",
        "embeddingModel": "text-embedding-3-small",
        "embeddingApiProvider": "openai",
        "chatSecretProfileId": "p-chat",
        "embeddingSecretProfileId": "p-emb",
    },
}


@pytest.fixture(autouse=True)
def _auth() -> None:
    respx.post(f"{BASE}/_open/auth").respond(json={"jwt": make_jwt()})
    respx.get(f"{BASE}{ACP_BASE}/project_by_name/testdb/demo").respond(json=PROJECT)


@pytest.fixture
def project(client):
    # Construct the handle directly: the bind-time existence GET would fire
    # before @respx.mock activates (bind itself is covered in the ACP tests).
    from arango_ai.autograph import AutoGraphProject

    return AutoGraphProject(client, "demo")


# -- add_files --------------------------------------------------------------


@respx.mock
def test_add_files_paths_with_citable_urls(project, tmp_path: Path) -> None:
    doc = tmp_path / "report.pdf"
    doc.write_bytes(b"pdf-bytes")
    upload = respx.post(f"{FM_BASE}/batch").respond(
        json={"results": [{"name": "report.pdf", "status": "ok"}]}
    )

    result = project.add_files(
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


@respx.mock
def test_add_files_glob(project, tmp_path: Path) -> None:
    (tmp_path / "a.md").write_bytes(b"a")
    (tmp_path / "b.md").write_bytes(b"b")
    upload = respx.post(f"{FM_BASE}/batch").respond(
        json={
            "results": [
                {"name": "a.md", "status": "ok"},
                {"name": "b.md", "status": "ok"},
            ]
        }
    )

    result = project.add_files(str(tmp_path / "*.md"))

    assert len(result.ok) == 2
    manifest = _manifest_entries(upload.calls[0].request.content)
    assert [entry["name"] for entry in manifest] == ["a.md", "b.md"]


@respx.mock
def test_add_files_glob_without_matches_raises(project, tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="matched no files"):
        project.add_files(str(tmp_path / "*.pdf"))


@respx.mock
def test_add_files_folder_delegates_to_walk(project, tmp_path: Path) -> None:
    (tmp_path / "doc.md").write_bytes(b"content")
    upload = respx.post(f"{FM_BASE}/batch").respond(
        json={"results": [{"name": "doc.md", "status": "ok"}]}
    )

    result = project.add_files(tmp_path, category="docs")

    assert len(result.ok) == 1
    assert upload.called


@respx.mock
def test_add_files_folder_with_citable_urls_rejected(project, tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="explicit file list"):
        project.add_files(tmp_path, citable_urls={"a.md": "https://x"})


@respx.mock
def test_add_files_fileupload_gets_citable_url_merged(project) -> None:
    upload = FileUpload("spec.md", b"content", custom_metadata={"lang": "en"})
    route = respx.post(f"{FM_BASE}/batch").respond(
        json={"results": [{"name": "spec.md", "status": "ok"}]}
    )

    project.add_files([upload], citable_urls={"spec.md": "https://x/spec"})

    manifest = _manifest_entries(route.calls[0].request.content)
    assert manifest[0]["custom_metadata"] == {
        "lang": "en",
        "citable_url": "https://x/spec",
    }
    # The caller's FileUpload object stays untouched.
    assert upload.custom_metadata == {"lang": "en"}


def test_add_files_unmatched_citable_urls_raise(project, tmp_path: Path) -> None:
    doc = tmp_path / "report.pdf"
    doc.write_bytes(b"pdf-bytes")

    with pytest.raises(ConfigError, match="typo.pdf"):
        project.add_files([doc], citable_urls={"typo.pdf": "https://x"})


# -- workflow chain -----------------------------------------------------------


@respx.mock
def test_build_wait_chain(project) -> None:
    respx.get(f"{FM_BASE}/scopes").respond(
        json={"children": [{"segment": "docs", "file_count": 1}]}
    )
    respx.post(f"{AG_BASE}/v1/corpus/builds").respond(
        json={"corpusBuildId": "b-1", "graphName": "demo_CorpusGraph"}
    )
    status = respx.get(f"{AG_BASE}/v1/corpus/builds/b-1")
    status.side_effect = [
        httpx.Response(200, json={"status": "running", "progress": 40}),
        httpx.Response(200, json={"status": "completed", "documentCount": 3}),
    ]

    run = project.build()
    outcome = run.wait(interval=0)

    assert run.build_id == "b-1"
    assert run.graph_name == "demo_CorpusGraph"
    assert outcome["documentCount"] == 3


@respx.mock
def test_strategize_blocking_returns_plan(project) -> None:
    respx.post(f"{AG_BASE}/v1/rag-strategizer/analyze").respond(
        json={"strategizeJobId": "j-1"}
    )
    respx.get(f"{AG_BASE}/v1/rag-strategizer/jobs/j-1").respond(
        json={"status": "completed"}
    )
    respx.get(f"{AG_BASE}/v1/rag-strategizer/strategy").respond(
        json={"strategies": [], "totalStrategies": 4}
    )

    plan = project.strategize("moderate")

    assert plan["totalStrategies"] == 4


@respx.mock
def test_strategize_non_blocking_returns_job_id(project) -> None:
    respx.post(f"{AG_BASE}/v1/rag-strategizer/analyze").respond(
        json={"strategizeJobId": "j-9"}
    )

    assert project.strategize("high", extract_images=True, wait=False) == "j-9"


@respx.mock
def test_orchestrate_wait_chain(project) -> None:
    orchestrate = respx.post(f"{AG_BASE}/v1/orchestrate").respond(
        json={"orchestrationId": "o-1", "success": True}
    )
    respx.get(f"{AG_BASE}/v1/orchestrate/o-1").respond(
        json={"status": "completed", "totalJobs": 2, "completedJobs": 2}
    )

    outcome = project.orchestrate().wait(interval=0)

    assert outcome["completedJobs"] == 2
    body = json.loads(orchestrate.calls[0].request.content)
    # Secret ids resolved from the project's persisted model settings.
    assert body["chatSecretProfileIds"] == ["p-chat"]
    assert body["embeddingSecretProfileId"] == "p-emb"


def _project_with_orchestration_mirror(mirror: dict) -> dict:
    payload = copy.deepcopy(PROJECT)
    payload["projectMetadata"]["autographService"]["importerOrchestration"] = mirror
    return payload


@respx.mock
def test_orchestrate_wait_ignores_previous_runs_terminal_mirror(project) -> None:
    # The mirror still echoes the PREVIOUS run's terminal state when the
    # handle starts waiting; the pre-trigger baseline must suppress it until
    # the mirror visibly changes.
    stale = {"status": "completed", "totalJobs": 1, "completed": 1, "failed": 0}
    done = {"status": "completed", "totalJobs": 2, "completed": 2, "failed": 0}
    route = respx.get(f"{BASE}{ACP_BASE}/project_by_name/testdb/demo")
    # Stale during baseline capture, secret resolution, service-path reads,
    # and the first poll; fresh afterwards (extra entries absorb call-count
    # shifts — the guard tolerates any number of stale polls).
    route.side_effect = [
        httpx.Response(200, json=_project_with_orchestration_mirror(stale))
        for _ in range(4)
    ] + [
        httpx.Response(200, json=_project_with_orchestration_mirror(done))
        for _ in range(4)
    ]
    # No orchestrationId in the response: the wait runs on the mirror tier.
    respx.post(f"{AG_BASE}/v1/orchestrate").respond(json={"success": True})

    outcome = project.orchestrate().wait(interval=0)

    assert outcome["completedJobs"] == 2


# -- health gate --------------------------------------------------------------


@respx.mock
def test_wait_until_serving_transport_flap_keeps_polling(project) -> None:
    health = respx.get(f"{AG_BASE}/v1/health")
    health.side_effect = [
        httpx.ConnectError("boom"),
        httpx.Response(200),
        httpx.Response(200),
        httpx.Response(200),
    ]

    project.wait_until_serving(timeout=5, interval=0)

    assert health.call_count == 4


@respx.mock
def test_wait_until_serving_redirect_is_not_healthy(project) -> None:
    # A 3xx is a proxy/ingress answering, not the service: no healthy tick.
    health = respx.get(f"{AG_BASE}/v1/health")
    health.side_effect = [
        httpx.Response(302, headers={"location": "https://sso.example.com"}),
        httpx.Response(200),
        httpx.Response(200),
        httpx.Response(200),
    ]

    project.wait_until_serving(timeout=5, interval=0)

    assert health.call_count == 4


@respx.mock
def test_wait_until_serving_auth_failure_propagates(project) -> None:
    respx.post(f"{BASE}/_open/auth").respond(401, text="bad credentials")
    health = respx.get(f"{AG_BASE}/v1/health").respond(200)

    # Bad credentials must surface, not degrade into a full-timeout poll.
    with pytest.raises(AuthenticationError):
        project.wait_until_serving(timeout=5, interval=0)
    assert not health.called


# -- retrieval facade -----------------------------------------------------------


@respx.mock
def test_deploy_retriever_defaults_from_model_settings(project) -> None:
    service = respx.post(f"{BASE}{ACP_BASE}/service").respond(
        json={
            "serviceInfo": {
                "serviceId": "arangodb-graphrag-retriever-xyz-0",
                "status": "DEPLOYING",
            }
        }
    )

    info = project.deploy_retriever(wait=False)

    body = json.loads(service.calls[0].request.content)
    assert body["service_name"] == "arangodb-graphrag-retriever"
    env = body["env"]
    assert env["chat_model"] == "gpt-4.1"
    assert env["embedding_model"] == "text-embedding-3-small"
    assert env["chat_secret_profile_id"] == "p-chat"
    assert env["embedding_secret_profile_id"] == "p-emb"
    assert info["serviceId"] == "arangodb-graphrag-retriever-xyz-0"


@respx.mock
def test_deploy_retriever_passes_timeouts_through(project) -> None:
    respx.post(f"{BASE}{ACP_BASE}/service").respond(
        json={
            "serviceInfo": {
                "serviceId": "arangodb-graphrag-retriever-xyz-0",
                "status": "DEPLOYING",
            }
        }
    )
    respx.get(f"{BASE}{ACP_BASE}/service/arangodb-graphrag-retriever-xyz-0").respond(
        json={
            "serviceInfo": {
                "serviceId": "arangodb-graphrag-retriever-xyz-0",
                "status": "DEPLOYED",
            }
        }
    )
    health = respx.get(f"{BASE}/graphrag/retriever/xyz-0/v1/health").respond(
        200, json={"status": "OK"}
    )

    info = project.deploy_retriever(deploy_timeout=5, health_timeout=5)

    assert info["status"] == "DEPLOYED"
    assert health.call_count == 3  # the health streak ran under the new kwarg


@respx.mock
def test_deploy_without_model_settings_raises(client) -> None:
    bare = dict(PROJECT, modelSettings={})
    respx.get(f"{BASE}{ACP_BASE}/project_by_name/testdb/bare").respond(json=bare)

    with pytest.raises(ConfigError, match="chat_model"):
        client.autograph.project("bare").deploy_retriever(wait=False)


def _ndjson(*frames: dict) -> bytes:
    return b"\n".join(json.dumps({"result": frame}).encode() for frame in frames)


@respx.mock
def test_ask_resolves_single_metadata_retriever(project) -> None:
    query = respx.post(
        f"{BASE}/graphrag/retriever/abc-0/v1/graphrag-query-stream"
    ).respond(
        content=_ndjson(
            {"runId": "r-1", "delta": "The answer"},
            {"isFinal": True, "finalResult": "The answer."},
        )
    )

    result = project.ask("question?")

    assert str(result) == "The answer."
    assert result.run_id == "r-1"
    assert query.called


@respx.mock
def test_ask_prefers_cached_deploy(project) -> None:
    respx.post(f"{BASE}{ACP_BASE}/service").respond(
        json={
            "serviceInfo": {
                "serviceId": "arangodb-graphrag-retriever-new-0",
                "status": "DEPLOYING",
            }
        }
    )
    project.deploy_retriever(wait=False)
    query = respx.post(
        f"{BASE}/graphrag/retriever/new-0/v1/graphrag-query-stream"
    ).respond(content=_ndjson({"isFinal": True, "finalResult": "ok"}))

    project.ask("q")

    assert query.called


@respx.mock
def test_ask_without_any_retriever_raises(client) -> None:
    none = dict(PROJECT)
    none["projectMetadata"] = {
        "autographService": {"serviceUrl": "https://internal/autograph/wzfue/"},
        "retrieverServices": [],
    }
    respx.get(f"{BASE}{ACP_BASE}/project_by_name/testdb/none").respond(json=none)

    with pytest.raises(ServiceNotReadyError, match="no deployed retriever"):
        client.autograph.project("none").ask("q")


@respx.mock
def test_ask_with_multiple_retrievers_requires_explicit_id(client) -> None:
    many = dict(PROJECT)
    many["projectMetadata"] = {
        "autographService": {"serviceUrl": "https://internal/autograph/wzfue/"},
        "retrieverServices": [
            {"serviceId": "arangodb-graphrag-retriever-a-0"},
            {"serviceId": "arangodb-graphrag-retriever-b-0"},
        ],
    }
    respx.get(f"{BASE}{ACP_BASE}/project_by_name/testdb/many").respond(json=many)

    with pytest.raises(ConfigError, match="retriever_id"):
        client.autograph.project("many").ask("q")


def _manifest_entries(content: bytes) -> list[dict]:
    """Extract the manifest JSON array from a multipart body."""
    marker = b'name="manifest"'
    start = content.index(marker)
    json_start = content.index(b"[", start)
    depth = 0
    for i in range(json_start, len(content)):
        if content[i : i + 1] == b"[":
            depth += 1
        elif content[i : i + 1] == b"]":
            depth -= 1
            if depth == 0:
                return list(json.loads(content[json_start : i + 1]))
    raise AssertionError("manifest array not found")


@respx.mock
def test_add_files_rejects_duplicate_basenames(project, tmp_path: Path) -> None:
    # (scope, name) keys the store; two paths sharing a basename would
    # silently overwrite each other as versions (CodeRabbit finding).
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    (tmp_path / "a" / "report.pdf").write_bytes(b"a")
    (tmp_path / "b" / "report.pdf").write_bytes(b"b")

    with pytest.raises(ConfigError, match="duplicate stored file names"):
        project.add_files(
            [tmp_path / "a" / "report.pdf", tmp_path / "b" / "report.pdf"]
        )
