import json
from typing import Any

import httpx
import pytest
import respx

from arango_ai.acp import ACP_BASE
from arango_ai.autograph import AutoGraphProject
from arango_ai.autograph.ingestion import CorpusBuild, IngestionAPI
from arango_ai.exceptions import (
    BuildFailedError,
    BuildInProgressError,
    ConfigError,
    InternalServerError,
    OrchestrationError,
    WaitTimeoutError,
)

from .conftest import BASE, make_jwt

SERVICE_URL = "https://internal.host/autograph/wzfue/"
SVC = f"{BASE}/autograph/wzfue"


def project_payload(
    *,
    model_settings: dict[str, Any] | None = None,
    autograph_extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    service: dict[str, Any] = {"serviceUrl": SERVICE_URL}
    if autograph_extra:
        service.update(autograph_extra)
    payload: dict[str, Any] = {
        "projectName": "demo",
        "projectType": "autograph",
        "projectMetadata": {"autographService": service},
    }
    if model_settings is not None:
        payload["modelSettings"] = model_settings
    return payload


def mock_project(**kwargs: Any) -> None:
    """The service path is re-resolved per call, so every ingestion call
    needs the ACP project route answering."""
    respx.get(f"{BASE}{ACP_BASE}/project_by_name/testdb/demo").respond(
        json=project_payload(**kwargs)
    )


@pytest.fixture(autouse=True)
def _auth() -> None:
    respx.post(f"{BASE}/_open/auth").respond(json={"jwt": make_jwt()})


@pytest.fixture
def ingestion(client) -> IngestionAPI:
    return IngestionAPI(AutoGraphProject(client, "demo"))


# -- corpus build --------------------------------------------------------------


@respx.mock
def test_build_corpus_omits_categories_and_falls_back_graph_name(ingestion) -> None:
    mock_project()
    route = respx.post(f"{SVC}/v1/corpus/builds").respond(json={"corpusBuildId": "b-1"})

    build = ingestion.build_corpus()

    assert build == CorpusBuild(build_id="b-1", graph_name="demo_CorpusGraph")
    body = json.loads(route.calls[0].request.content)
    assert body == {"project": "demo", "incremental": False}


@respx.mock
def test_build_corpus_with_categories_and_real_graph_name(ingestion) -> None:
    mock_project()
    route = respx.post(f"{SVC}/v1/corpus/builds").respond(
        json={"corpusBuildId": "b-2", "graphName": "MyGraph"}
    )

    build = ingestion.build_corpus(categories=["cat_a", "cat_b"])

    assert build.graph_name == "MyGraph"
    body = json.loads(route.calls[0].request.content)
    assert body["categories"] == ["cat_a", "cat_b"]


@respx.mock
def test_build_corpus_409_raises_build_in_progress(ingestion) -> None:
    mock_project()
    respx.post(f"{SVC}/v1/corpus/builds").respond(409, json={"error": "busy"})

    with pytest.raises(BuildInProgressError):
        ingestion.build_corpus()


@respx.mock
def test_build_corpus_400_with_intent_in_message(ingestion) -> None:
    mock_project()
    respx.post(f"{SVC}/v1/corpus/builds").respond(
        400, json={"message": "rejected: BUILD_IN_PROGRESS"}
    )

    with pytest.raises(BuildInProgressError):
        ingestion.build_corpus()


@respx.mock
def test_wait_for_build_returns_completed_even_with_error_code(ingestion) -> None:
    mock_project()
    route = respx.get(f"{SVC}/v1/corpus/builds/b-1")
    route.side_effect = [
        httpx.Response(200, json={"status": "running", "progress": 50}),
        httpx.Response(
            200,
            json={
                "status": "COMPLETED",
                "progress": 100,
                "errorCode": "FILE_PARSER_PARTIAL_FAILURE",
            },
        ),
    ]

    status = ingestion.wait_for_build("b-1", timeout=5, interval=0)

    # Partial success must reach the caller, not be swallowed by the SDK.
    assert status["errorCode"] == "FILE_PARSER_PARTIAL_FAILURE"
    assert route.call_count == 2


@respx.mock
def test_wait_for_build_failed_raises_with_message_and_code(ingestion) -> None:
    mock_project()
    respx.get(f"{SVC}/v1/corpus/builds/b-1").respond(
        json={
            "status": "failed",
            "message": "LLM_AUTHENTICATION_FAILED: key rejected",
            "error": "generic compatibility text",
            "errorCode": "LLM_AUTHENTICATION_FAILED",
        }
    )

    with pytest.raises(BuildFailedError) as excinfo:
        ingestion.wait_for_build("b-1", timeout=5, interval=0)
    assert "key rejected" in str(excinfo.value)
    assert excinfo.value.error_code == "LLM_AUTHENTICATION_FAILED"


@respx.mock
def test_wait_for_build_nonempty_error_field_raises(ingestion) -> None:
    mock_project()
    respx.get(f"{SVC}/v1/corpus/builds/b-1").respond(
        json={"status": "running", "message": "40% parsed", "error": "exploded"}
    )

    with pytest.raises(BuildFailedError, match="exploded"):
        ingestion.wait_for_build("b-1", timeout=5, interval=0)


@respx.mock
def test_wait_for_build_timeout(ingestion) -> None:
    mock_project()
    respx.get(f"{SVC}/v1/corpus/builds/b-1").respond(json={"status": "running"})

    with pytest.raises(WaitTimeoutError):
        ingestion.wait_for_build("b-1", timeout=0, interval=0)


@respx.mock
def test_wait_for_build_tolerates_transient_500(ingestion) -> None:
    mock_project()
    route = respx.get(f"{SVC}/v1/corpus/builds/b-1")
    route.side_effect = [
        httpx.Response(500, json={"error": "gateway blip"}),
        httpx.Response(200, json={"status": "running"}),
        httpx.Response(200, json={"status": "completed"}),
    ]

    status = ingestion.wait_for_build("b-1", timeout=5, interval=0)

    # A lone 5xx mid-wait must not abort a multi-hour build watch.
    assert status["status"] == "completed"
    assert route.call_count == 3


@respx.mock
def test_wait_for_build_persistent_500_aborts_after_budget(ingestion) -> None:
    mock_project()
    route = respx.get(f"{SVC}/v1/corpus/builds/b-1").respond(
        500, json={"error": "down"}
    )

    with pytest.raises(InternalServerError):
        ingestion.wait_for_build("b-1", timeout=60, interval=0)

    # Budget of 5 consecutive transient failures; the sixth propagates.
    assert route.call_count == 6


# -- strategizer ----------------------------------------------------------------


def test_strategize_invalid_complexity(ingestion) -> None:
    with pytest.raises(ConfigError, match="complexity"):
        ingestion.strategize(complexity="medium")


def test_strategize_images_below_high_rejected(ingestion) -> None:
    with pytest.raises(ConfigError, match="high"):
        ingestion.strategize(complexity="moderate", extract_images=True)


@respx.mock
def test_strategize_images_at_very_high_full_body(ingestion) -> None:
    mock_project()
    route = respx.post(f"{SVC}/v1/rag-strategizer/analyze").respond(
        json={"strategizeJobId": "j-1"}
    )

    job_id = ingestion.strategize(
        complexity="very_high", extract_images=True, categories=["demo_cat"]
    )

    assert job_id == "j-1"
    body = json.loads(route.calls[0].request.content)
    assert body == {
        "project": "demo",
        "complexity": "very_high",
        "extractImagesDefault": True,
        "categories": ["demo_cat"],
    }


@respx.mock
def test_strategize_minimal_body_and_absent_job_id(ingestion) -> None:
    mock_project()
    route = respx.post(f"{SVC}/v1/rag-strategizer/analyze").respond(json={})

    job_id = ingestion.strategize(complexity="moderate")

    assert job_id is None
    body = json.loads(route.calls[0].request.content)
    assert body == {"project": "demo", "complexity": "moderate"}


@respx.mock
def test_wait_for_strategize_trusts_jobs_endpoint(ingestion) -> None:
    mock_project()
    route = respx.get(f"{SVC}/v1/rag-strategizer/jobs/j-1")
    route.side_effect = [
        httpx.Response(200, json={"status": "running", "progress": 40}),
        httpx.Response(
            200, json={"status": "completed", "progress": 100, "clustersDone": 4}
        ),
    ]

    status = ingestion.wait_for_strategize("j-1", timeout=5, interval=0)

    assert status["clustersDone"] == 4
    assert route.call_count == 2


@respx.mock
def test_wait_for_strategize_falls_back_to_metadata_on_404(ingestion) -> None:
    mock_project(
        autograph_extra={
            "ragstrategizer": {"status": "completed", "progress": 100, "message": "ok"}
        }
    )
    route = respx.get(f"{SVC}/v1/rag-strategizer/jobs/j-1")
    route.side_effect = [
        httpx.Response(200, json={"status": "running"}),
        httpx.Response(404),
    ]

    status = ingestion.wait_for_strategize("j-1", timeout=5, interval=0)

    assert status == {"status": "completed", "progress": 100, "message": "ok"}
    # The mirror's terminal echo must not shortcut the endpoint tier.
    assert route.call_count == 2


@respx.mock
def test_wait_for_strategize_baseline_suppresses_previous_terminal_echo(
    ingestion,
) -> None:
    # The mirror slot still holds the PREVIOUS run's terminal state right
    # after triggering; with the pre-trigger baseline the waiter must treat
    # that echo as "not yet" and only trust the fresh run's terminal state.
    stale = {"status": "completed", "progress": 100, "message": "old run"}
    running = {"status": "running", "progress": 40, "message": "going"}
    done = {"status": "completed", "progress": 100, "message": "new run"}
    route = respx.get(f"{BASE}{ACP_BASE}/project_by_name/testdb/demo")
    route.side_effect = [
        httpx.Response(200, json=project_payload(autograph_extra={"ragstrategizer": s}))
        for s in (stale, running, done)
    ]

    status = ingestion.wait_for_strategize(None, timeout=5, interval=0, baseline=stale)

    assert status["message"] == "new run"
    assert route.call_count == 3


@respx.mock
def test_wait_for_strategize_previous_failed_echo_does_not_raise(ingestion) -> None:
    stale = {"status": "failed", "message": "old failure"}
    done = {"status": "completed", "progress": 100, "message": "fresh"}
    route = respx.get(f"{BASE}{ACP_BASE}/project_by_name/testdb/demo")
    route.side_effect = [
        httpx.Response(200, json=project_payload(autograph_extra={"ragstrategizer": s}))
        for s in (stale, done)
    ]

    # Without the baseline guard this would raise BuildFailedError from the
    # previous run's echo before the new run ever gets polled.
    status = ingestion.wait_for_strategize(None, timeout=5, interval=0, baseline=stale)

    assert status["message"] == "fresh"
    assert route.call_count == 2


@respx.mock
def test_wait_for_strategize_without_job_id_uses_mirror_failure(ingestion) -> None:
    mock_project(
        autograph_extra={
            "ragstrategizer": {"status": "failed", "message": "quota exhausted"}
        }
    )

    with pytest.raises(BuildFailedError, match="quota exhausted"):
        ingestion.wait_for_strategize(None, timeout=5, interval=0)


@respx.mock
def test_strategies_raw_passthrough(ingestion) -> None:
    mock_project()
    payload = {
        "strategies": [{"clusterId": "c-1", "strategyType": "VectorRAG"}],
        "totalStrategies": 1,
        "strategyTypeCounts": {"VectorRAG": 1},
    }
    respx.get(f"{SVC}/v1/rag-strategizer/strategy").respond(json=payload)

    assert ingestion.strategies() == payload


@respx.mock
def test_update_strategy_patch_body_exact(ingestion) -> None:
    mock_project()
    route = respx.patch(f"{SVC}/v1/rag-strategizer/strategy/c-1").respond(
        json={"strategy": {"clusterId": "c-1", "strategyType": "FullGraphRAG"}}
    )

    strategy = ingestion.update_strategy(
        "c-1", graph_rag=True, entity_types=["person", "org"], extract_images=True
    )

    assert strategy == {"clusterId": "c-1", "strategyType": "FullGraphRAG"}
    body = json.loads(route.calls[0].request.content)
    assert body == {
        "strategyType": "FullGraphRAG",
        "entityTypes": ["person", "org"],
        "extractImages": True,
    }


@respx.mock
def test_update_strategy_vector_defaults_pass_through(ingestion) -> None:
    mock_project()
    route = respx.patch(f"{SVC}/v1/rag-strategizer/strategy/c-2").respond(
        json={"strategy": {"strategyType": "VectorRAG"}}
    )

    ingestion.update_strategy("c-2", graph_rag=False)

    body = json.loads(route.calls[0].request.content)
    # Server-side normalization is not duplicated client-side.
    assert body == {
        "strategyType": "VectorRAG",
        "entityTypes": [],
        "extractImages": False,
    }


# -- orchestration ---------------------------------------------------------------


@respx.mock
def test_orchestrate_omits_embedding_id_without_one_configured(ingestion) -> None:
    # No embedding fallback to the chat id: the field is omitted so the
    # service resolves its own embedding credentials (UI parity).
    mock_project(model_settings={"chatSecretProfileId": "p-1"})
    route = respx.post(f"{SVC}/v1/orchestrate").respond(
        json={"orchestrationId": "o-1", "success": True}
    )

    orchestration_id = ingestion.orchestrate()

    assert orchestration_id == "o-1"
    body = json.loads(route.calls[0].request.content)
    assert body == {
        "project": "demo",
        "replicas": 1,
        "maxRetries": 3,
        "chatSecretProfileIds": ["p-1"],
    }
    assert "embeddingSecretProfileId" not in body


@respx.mock
def test_orchestrate_uses_persisted_embedding_id_and_categories(ingestion) -> None:
    mock_project(
        model_settings={
            "chatSecretProfileId": "p-1",
            "embeddingSecretProfileId": "p-2",
        }
    )
    route = respx.post(f"{SVC}/v1/orchestrate").respond(json={"orchestrationId": "o-1"})

    ingestion.orchestrate(categories=["cat_a"], replicas=3)

    body = json.loads(route.calls[0].request.content)
    assert body["chatSecretProfileIds"] == ["p-1"]
    assert body["embeddingSecretProfileId"] == "p-2"
    assert body["categories"] == ["cat_a"]
    assert body["replicas"] == 3


@respx.mock
def test_orchestrate_explicit_ids_override_settings(ingestion) -> None:
    mock_project(model_settings={"chatSecretProfileId": "p-1"})
    route = respx.post(f"{SVC}/v1/orchestrate").respond(json={"orchestrationId": "o-1"})

    ingestion.orchestrate(
        chat_secret_profile_ids=["c-1", "c-2"], embedding_secret_profile_id="e-1"
    )

    body = json.loads(route.calls[0].request.content)
    assert body["chatSecretProfileIds"] == ["c-1", "c-2"]
    assert body["embeddingSecretProfileId"] == "e-1"


@respx.mock
def test_orchestrate_without_credentials_raises(ingestion) -> None:
    mock_project(model_settings={})

    with pytest.raises(ConfigError, match="chat secret profile"):
        ingestion.orchestrate()


def test_orchestrate_replicas_bounds(ingestion) -> None:
    with pytest.raises(ConfigError, match="replicas"):
        ingestion.orchestrate(replicas=0)
    with pytest.raises(ConfigError, match="replicas"):
        ingestion.orchestrate(replicas=11)


@respx.mock
def test_orchestrate_synchronous_rejection_raises(ingestion) -> None:
    mock_project(model_settings={"chatSecretProfileId": "p-1"})
    respx.post(f"{SVC}/v1/orchestrate").respond(
        json={"success": False, "message": "no strategies to import"}
    )

    with pytest.raises(OrchestrationError, match="no strategies"):
        ingestion.orchestrate()


@respx.mock
def test_wait_for_orchestration_completed_via_endpoint(ingestion) -> None:
    mock_project()
    route = respx.get(f"{SVC}/v1/orchestrate/o-1")
    route.side_effect = [
        httpx.Response(
            200, json={"status": "running", "totalJobs": 2, "completedJobs": 1}
        ),
        httpx.Response(
            200,
            json={
                "status": "completed",
                "totalJobs": 2,
                "completedJobs": 2,
                "failedJobs": 0,
            },
        ),
    ]

    status = ingestion.wait_for_orchestration("o-1", timeout=5, interval=0)

    assert status["completedJobs"] == 2
    assert route.call_count == 2


@respx.mock
def test_wait_for_orchestration_failed_includes_job_causes(ingestion) -> None:
    mock_project()
    respx.get(f"{SVC}/v1/orchestrate/o-1").respond(
        json={
            "status": "failed",
            "message": "1/2 jobs failed",
            "jobs": [
                {"ragPartitionId": "rp-1", "status": "completed"},
                {
                    "ragPartitionId": "rp-2",
                    "category": "contracts",
                    "status": "failed",
                    "errorMessage": "provider rejected the key",
                },
            ],
        }
    )

    with pytest.raises(OrchestrationError) as excinfo:
        ingestion.wait_for_orchestration("o-1", timeout=5, interval=0)
    message = str(excinfo.value)
    assert "1/2 jobs failed" in message
    assert "contracts: provider rejected the key" in message


@respx.mock
def test_wait_for_orchestration_metadata_fallback_normalizes_names(ingestion) -> None:
    mock_project(
        autograph_extra={
            "importerOrchestration": {
                "status": "completed",
                "totalJobs": 3,
                "running": 0,
                "completed": 3,
                "failed": 0,
                "message": "all done",
            }
        }
    )
    respx.get(f"{SVC}/v1/orchestrate/o-1").respond(404)

    status = ingestion.wait_for_orchestration("o-1", timeout=5, interval=0)

    # Mirror field names (completed/failed) come back as the endpoint's.
    assert status == {
        "status": "completed",
        "totalJobs": 3,
        "completedJobs": 3,
        "failedJobs": 0,
        "message": "all done",
    }


@respx.mock
def test_wait_for_orchestration_baseline_suppresses_previous_terminal_echo(
    ingestion,
) -> None:
    stale = {"status": "completed", "totalJobs": 1, "completed": 1, "failed": 0}
    running = {"status": "running", "totalJobs": 2, "completed": 1, "failed": 0}
    done = {
        "status": "completed",
        "totalJobs": 2,
        "completed": 2,
        "failed": 0,
        "message": "new run",
    }
    route = respx.get(f"{BASE}{ACP_BASE}/project_by_name/testdb/demo")
    route.side_effect = [
        httpx.Response(
            200, json=project_payload(autograph_extra={"importerOrchestration": s})
        )
        for s in (stale, running, done)
    ]

    status = ingestion.wait_for_orchestration(
        None, timeout=5, interval=0, baseline=stale
    )

    assert status["completedJobs"] == 2
    assert status["message"] == "new run"
    assert route.call_count == 3


# -- overview ---------------------------------------------------------------------


@respx.mock
def test_overview_raw_passthrough(ingestion) -> None:
    mock_project()
    payload = {
        "project": "demo",
        "corpusGraph": {"name": "demo_CorpusGraph", "status": "ready", "stale": True},
        "knowledgeGraph": {"name": "demo_KG", "status": "built"},
        "categories": [{"name": "cat_a", "needsCorpusUpdate": True}],
    }
    respx.get(f"{SVC}/v1/projects/demo/overview").respond(json=payload)

    assert ingestion.overview() == payload
