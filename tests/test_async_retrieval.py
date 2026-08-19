import json

import httpx
import pytest
import respx

from arango_ai import ApiError, ConfigError, QueryError, ServiceNotReadyError
from arango_ai.acp import ACP_BASE
from arango_ai.retrieval import Final, Progress, TokenDelta

from .conftest import BASE, make_jwt
from .test_retrieval import ndjson

SERVICE_ID = "arangodb-graphrag-retriever-yaq6r"
HEALTH_URL = f"{BASE}/graphrag/retriever/yaq6r/v1/health"
QUERY_URL = f"{BASE}/graphrag/retriever/yaq6r/v1/graphrag-query-stream"


@pytest.fixture(autouse=True)
def _auth() -> None:
    respx.post(f"{BASE}/_open/auth").respond(json={"jwt": make_jwt()})


# -- deploy + health gate --------------------------------------------------------


@respx.mock
async def test_deploy_waits_for_deployed_then_health_streak(async_client) -> None:
    deploy_route = respx.post(f"{BASE}{ACP_BASE}/service").respond(
        json={"serviceInfo": {"serviceId": SERVICE_ID, "status": "DEPLOYING"}}
    )
    status_route = respx.get(f"{BASE}{ACP_BASE}/service/{SERVICE_ID}")
    status_route.side_effect = [
        httpx.Response(
            200, json={"serviceInfo": {"serviceId": SERVICE_ID, "status": "DEPLOYING"}}
        ),
        httpx.Response(
            200, json={"serviceInfo": {"serviceId": SERVICE_ID, "status": "DEPLOYED"}}
        ),
    ]
    # Route flap: a lone 200 must not count; three consecutive are needed.
    health_route = respx.get(HEALTH_URL)
    health_route.side_effect = [
        httpx.Response(404),
        httpx.Response(200, json={"status": "OK"}),
        httpx.Response(404),
        httpx.Response(200, json={"status": "OK"}),
        httpx.Response(200, json={"status": "OK"}),
        httpx.Response(200, json={"status": "OK"}),
    ]

    info = await async_client.retrievers.deploy(
        "demo",
        chat_model="m",
        chat_secret_profile_id="p-1",
        deploy_timeout=5,
        healthy_timeout=5,
    )

    assert info["status"] == "DEPLOYED"
    body = json.loads(deploy_route.calls[0].request.content)
    assert body["service_name"] == "arangodb-graphrag-retriever"
    assert body["env"]["chat_secret_profile_id"] == "p-1"
    assert status_route.call_count == 2
    assert health_route.call_count == 6  # flap resets the streak


@respx.mock
async def test_wait_healthy_fail_body_raises_immediately(async_client) -> None:
    route = respx.get(HEALTH_URL).respond(
        200, json={"status": "FAIL", "message": "bad credentials"}
    )

    with pytest.raises(ServiceNotReadyError, match="bad credentials"):
        await async_client.retrievers.wait_healthy(SERVICE_ID, timeout=5)
    assert route.call_count == 1


# -- query -------------------------------------------------------------------------


@respx.mock
async def test_query_body_defaults_and_drain(async_client) -> None:
    route = respx.post(QUERY_URL).mock(
        return_value=httpx.Response(
            200, content=ndjson({"isFinal": True, "finalResult": "hi"})
        )
    )

    result = await async_client.retrievers.query(SERVICE_ID, "what is x?")

    body = json.loads(route.calls[0].request.content)
    assert body == {
        "query": "what is x?",
        "mode": "INSTANT",
        "provider": 0,
        "include_metadata": True,
        "use_cache": False,
        "show_citations": False,
    }
    assert result.answer == "hi"


async def test_query_invalid_mode_raises_before_iteration(async_client) -> None:
    # Eager validation: the ConfigError must not wait for the first frame.
    with pytest.raises(ConfigError, match="mode"):
        async_client.retrievers.query_stream(SERVICE_ID, "q", mode="instant")


@respx.mock
async def test_query_stream_yields_typed_events_in_order(async_client) -> None:
    progress_frame = {"type": "progress", "stage": "synthesis", "status": "started"}
    respx.post(QUERY_URL).mock(
        return_value=httpx.Response(
            200,
            content=ndjson(
                {"metadata": json.dumps(progress_frame)},
                {"delta": "Hel"},
                {"delta": "lo"},
                {"isFinal": True, "runId": "r-9"},
            ),
        )
    )

    events = [
        event
        async for event in async_client.retrievers.query_stream(
            SERVICE_ID, "q", mode="DEEP_SEARCH"
        )
    ]

    assert [type(e) for e in events] == [Progress, TokenDelta, TokenDelta, Final]
    assert events[0].data == progress_frame
    assert [e.text for e in events[1:3]] == ["Hel", "lo"]
    final = events[3].result
    assert final.answer == "Hello"
    assert final.run_id == "r-9"
    assert final.progress == [progress_frame]


@respx.mock
async def test_query_error_code_in_200_stream_raises(async_client) -> None:
    respx.post(QUERY_URL).mock(
        return_value=httpx.Response(
            200,
            content=ndjson(
                {"errorCode": "CREDENTIAL_CHECK_FAILED"},
                {"isFinal": True, "finalResult": "Invalid API key for chat model."},
            ),
        )
    )

    with pytest.raises(QueryError) as excinfo:
        await async_client.retrievers.query(SERVICE_ID, "q")
    assert "CREDENTIAL_CHECK_FAILED" in str(excinfo.value)
    assert "Invalid API key" in str(excinfo.value)


@respx.mock
async def test_query_http_error_surfaces_backend_message(async_client) -> None:
    respx.post(QUERY_URL).mock(
        return_value=httpx.Response(
            500,
            json={"error": {"code": 500, "message": "chat model rejected the key"}},
        )
    )

    with pytest.raises(ApiError) as excinfo:
        await async_client.retrievers.query(SERVICE_ID, "q")
    assert excinfo.value.status_code == 500
    assert "chat model rejected the key" in str(excinfo.value)


@respx.mock
async def test_query_final_result_wins_over_deltas(async_client) -> None:
    respx.post(QUERY_URL).mock(
        return_value=httpx.Response(
            200,
            content=ndjson(
                {"delta": "partial"},
                {"isFinal": True, "finalResult": "The full answer."},
            ),
        )
    )

    result = await async_client.retrievers.query(SERVICE_ID, "q")

    assert result.answer == "The full answer."
