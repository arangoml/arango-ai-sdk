import httpx
import pytest
import respx

from arango_ai import AsyncClient
from arango_ai.acp import ACP_BASE
from arango_ai.autograph import AsyncAutoGraphProject
from arango_ai.autograph.ingestion import AsyncIngestionAPI
from arango_ai.exceptions import BuildInProgressError

from .conftest import BASE, make_jwt
from .test_ingestion import SVC, mock_project, project_payload


@pytest.fixture(autouse=True)
def _auth() -> None:
    respx.post(f"{BASE}/_open/auth").respond(json={"jwt": make_jwt()})


@pytest.fixture
def ingestion(async_client: AsyncClient) -> AsyncIngestionAPI:
    return AsyncIngestionAPI(AsyncAutoGraphProject(async_client, "demo"))


# -- corpus build ---------------------------------------------------------------


@respx.mock
async def test_build_corpus_409_raises_build_in_progress(ingestion) -> None:
    mock_project()
    respx.post(f"{SVC}/v1/corpus/builds").respond(409, json={"error": "busy"})

    with pytest.raises(BuildInProgressError):
        await ingestion.build_corpus()


@respx.mock
async def test_build_corpus_400_with_intent_in_message(ingestion) -> None:
    mock_project()
    respx.post(f"{SVC}/v1/corpus/builds").respond(
        400, json={"message": "rejected: BUILD_IN_PROGRESS"}
    )

    with pytest.raises(BuildInProgressError):
        await ingestion.build_corpus()


# -- two-tier waiters -------------------------------------------------------------


@respx.mock
async def test_wait_for_strategize_falls_back_to_metadata_on_404(ingestion) -> None:
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

    status = await ingestion.wait_for_strategize("j-1", timeout=5, interval=0)

    assert status == {"status": "completed", "progress": 100, "message": "ok"}
    # The mirror's terminal echo must not shortcut the endpoint tier.
    assert route.call_count == 2


@respx.mock
async def test_wait_for_orchestration_metadata_fallback_normalizes_names(
    ingestion,
) -> None:
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

    status = await ingestion.wait_for_orchestration("o-1", timeout=5, interval=0)

    # Mirror field names (completed/failed) come back as the endpoint's.
    assert status == {
        "status": "completed",
        "totalJobs": 3,
        "completedJobs": 3,
        "failedJobs": 0,
        "message": "all done",
    }


@respx.mock
async def test_wait_for_orchestration_baseline_suppresses_previous_echo(
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

    status = await ingestion.wait_for_orchestration(
        None, timeout=5, interval=0, baseline=stale
    )

    assert status["completedJobs"] == 2
    assert status["message"] == "new run"
    assert route.call_count == 3
