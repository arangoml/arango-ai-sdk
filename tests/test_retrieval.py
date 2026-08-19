import json

import httpx
import pytest
import respx

from arango_ai import (
    ApiError,
    Client,
    ConfigError,
    QueryError,
    ServiceNotReadyError,
    WaitTimeoutError,
)
from arango_ai.acp import ACP_BASE
from arango_ai.retrieval import (
    GRAPHRAG_RETRIEVER_PREFIX,
    Final,
    Progress,
    RetrieverAPI,
    TokenDelta,
    build_retriever_env,
    clean_service_id,
)

from .conftest import BASE, make_jwt

SERVICE_ID = "arangodb-graphrag-retriever-yaq6r"
HEALTH_URL = f"{BASE}/graphrag/retriever/yaq6r/v1/health"
QUERY_URL = f"{BASE}/graphrag/retriever/yaq6r/v1/graphrag-query-stream"


@pytest.fixture(autouse=True)
def _auth() -> None:
    respx.post(f"{BASE}/_open/auth").respond(json={"jwt": make_jwt()})


@pytest.fixture
def retriever(client: Client) -> RetrieverAPI:
    return RetrieverAPI(client)


def ndjson(*frames: dict) -> bytes:
    """NDJSON body: one `result`-enveloped JSON object per line."""
    return b"".join(json.dumps({"result": frame}).encode() + b"\n" for frame in frames)


# -- clean_service_id ----------------------------------------------------------


def test_clean_service_id_strips_retriever_prefix() -> None:
    assert clean_service_id("arangodb-graphrag-retriever-abc12") == "abc12"


def test_clean_service_id_keeps_pod_suffix_dashes() -> None:
    assert clean_service_id("arangodb-graphrag-retriever-yaq6r-0") == "yaq6r-0"


def test_clean_service_id_passes_unprefixed_through() -> None:
    assert clean_service_id("yaq6r") == "yaq6r"


def test_clean_service_id_bare_prefix_returns_original() -> None:
    # Stripping to nothing can't be a route segment; the UI returns the
    # original id in that case and the SDK mirrors it.
    assert clean_service_id(GRAPHRAG_RETRIEVER_PREFIX) == GRAPHRAG_RETRIEVER_PREFIX


# -- env building ----------------------------------------------------------------


def test_build_env_minimal_shape() -> None:
    env = build_retriever_env(
        database="db1",
        project_name="demo",
        chat_provider="openai",
        chat_model="gpt-4.1",
    )
    assert env == {
        "db_name": "db1",
        "genai_project_name": "demo",
        "chat_api_provider": "openai",
        "chat_model": "gpt-4.1",
    }


def test_build_env_full_shape() -> None:
    env = build_retriever_env(
        database="db1",
        project_name="demo",
        chat_provider="custom",
        chat_model="m",
        embedding_provider="custom",
        embedding_model="e",
        chat_secret_profile_id="p-chat",
        embedding_secret_profile_id="p-emb",
        chat_api_url="https://llm.example.com/v1",
        embedding_api_url="https://emb.example.com/v1",
    )
    assert env == {
        "db_name": "db1",
        "genai_project_name": "demo",
        "chat_api_provider": "custom",
        "chat_model": "m",
        "chat_api_url": "https://llm.example.com/v1",
        "embedding_api_provider": "custom",
        "embedding_model": "e",
        "embedding_api_url": "https://emb.example.com/v1",
        "chat_secret_profile_id": "p-chat",
        "embedding_secret_profile_id": "p-emb",
    }


def test_build_env_api_urls_dropped_for_stock_providers() -> None:
    env = build_retriever_env(
        database="db1",
        project_name="demo",
        chat_provider="openai",
        chat_model="m",
        embedding_provider="openai",
        embedding_model="e",
        chat_api_url="https://llm.example.com/v1",
        embedding_api_url="https://emb.example.com/v1",
    )
    assert "chat_api_url" not in env
    assert "embedding_api_url" not in env


def test_build_env_custom_chat_requires_url() -> None:
    with pytest.raises(ConfigError, match="chat_api_url"):
        build_retriever_env(
            database="db1",
            project_name="demo",
            chat_provider="custom",
            chat_model="m",
        )


def test_build_env_custom_embedding_requires_url() -> None:
    with pytest.raises(ConfigError, match="embedding_api_url"):
        build_retriever_env(
            database="db1",
            project_name="demo",
            chat_provider="openai",
            chat_model="m",
            embedding_provider="custom",
            embedding_model="e",
        )


def test_build_env_embedding_provider_without_model_rejected() -> None:
    with pytest.raises(ConfigError, match="embedding_model"):
        build_retriever_env(
            database="db1",
            project_name="demo",
            chat_provider="openai",
            chat_model="m",
            embedding_provider="openai",
        )


# -- deploy ----------------------------------------------------------------------


@respx.mock
def test_deploy_sends_chart_name_and_exact_env(retriever: RetrieverAPI) -> None:
    route = respx.post(f"{BASE}{ACP_BASE}/service").respond(
        json={"serviceInfo": {"serviceId": SERVICE_ID, "status": "DEPLOYING"}}
    )

    info = retriever.deploy(
        "demo",
        chat_model="gpt-4.1",
        embedding_model="text-embedding-3-small",
        chat_secret_profile_id="p-chat",
        embedding_secret_profile_id="p-emb",
        wait=False,
    )

    body = json.loads(route.calls[0].request.content)
    assert body["service_name"] == "arangodb-graphrag-retriever"
    assert body["env"] == {
        "db_name": "testdb",
        "genai_project_name": "demo",
        "chat_api_provider": "openai",
        "chat_model": "gpt-4.1",
        "embedding_api_provider": "openai",
        "embedding_model": "text-embedding-3-small",
        "chat_secret_profile_id": "p-chat",
        "embedding_secret_profile_id": "p-emb",
    }
    # Raw keys never travel in deploy envs, only secret profile ids.
    assert not any("api_key" in key for key in body["env"])
    assert info["serviceId"] == SERVICE_ID


@respx.mock
def test_deploy_does_not_reuse_chat_secret_for_embedding(
    retriever: RetrieverAPI,
) -> None:
    route = respx.post(f"{BASE}{ACP_BASE}/service").respond(
        json={"serviceInfo": {"serviceId": SERVICE_ID}}
    )

    retriever.deploy(
        "demo",
        chat_model="m",
        embedding_model="e",
        chat_secret_profile_id="p-chat",
        wait=False,
    )

    env = json.loads(route.calls[0].request.content)["env"]
    assert "embedding_secret_profile_id" not in env


@respx.mock
def test_deploy_custom_chat_without_url_raises_before_http(
    retriever: RetrieverAPI,
) -> None:
    route = respx.post(f"{BASE}{ACP_BASE}/service").respond(json={})

    with pytest.raises(ConfigError, match="chat_api_url"):
        retriever.deploy("demo", chat_model="m", chat_provider="custom", wait=False)
    assert not route.called


@respx.mock
def test_deploy_waits_for_deployed_then_health_streak(
    retriever: RetrieverAPI,
) -> None:
    respx.post(f"{BASE}{ACP_BASE}/service").respond(
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

    info = retriever.deploy(
        "demo",
        chat_model="m",
        chat_secret_profile_id="p-1",
        deploy_timeout=5,
        healthy_timeout=5,
    )

    assert info["status"] == "DEPLOYED"
    assert status_route.call_count == 2
    assert health_route.call_count == 6  # flap resets the streak


# -- health gate -------------------------------------------------------------------


@respx.mock
def test_wait_healthy_404s_keep_polling_until_streak(
    retriever: RetrieverAPI,
) -> None:
    route = respx.get(HEALTH_URL)
    route.side_effect = [
        httpx.Response(404),
        httpx.Response(404),
        httpx.Response(200, json={"status": "OK"}),
        httpx.Response(200, json={"status": "OK"}),
        httpx.Response(200, json={"status": "OK"}),
    ]

    retriever.wait_healthy(SERVICE_ID, timeout=5)

    assert route.call_count == 5


@respx.mock
def test_wait_healthy_flap_resets_streak(retriever: RetrieverAPI) -> None:
    route = respx.get(HEALTH_URL)
    route.side_effect = [
        httpx.Response(200, json={"status": "OK"}),
        httpx.Response(200, json={"status": "OK"}),
        httpx.Response(404),  # one flap wipes two successes
        httpx.Response(200, json={"status": "OK"}),
        httpx.Response(200, json={"status": "OK"}),
        httpx.Response(200, json={"status": "OK"}),
    ]

    retriever.wait_healthy(SERVICE_ID, timeout=5)

    assert route.call_count == 6


@respx.mock
def test_wait_healthy_fail_body_raises_immediately(retriever: RetrieverAPI) -> None:
    route = respx.get(HEALTH_URL).respond(
        200, json={"status": "FAIL", "message": "bad credentials"}
    )

    with pytest.raises(ServiceNotReadyError, match="bad credentials"):
        retriever.wait_healthy(SERVICE_ID, timeout=5)
    assert route.call_count == 1


@respx.mock
def test_wait_healthy_5xx_raises_immediately(retriever: RetrieverAPI) -> None:
    route = respx.get(HEALTH_URL).respond(503, json={"error": "upstream down"})

    with pytest.raises(ServiceNotReadyError, match="upstream down"):
        retriever.wait_healthy(SERVICE_ID, timeout=5)
    assert route.call_count == 1


@respx.mock
def test_wait_healthy_timeout(retriever: RetrieverAPI) -> None:
    respx.get(HEALTH_URL).respond(404)

    with pytest.raises(WaitTimeoutError):
        retriever.wait_healthy(SERVICE_ID, timeout=0.05, interval=0)


# -- query body ----------------------------------------------------------------------


@respx.mock
def test_query_body_defaults(retriever: RetrieverAPI) -> None:
    route = respx.post(QUERY_URL).mock(
        return_value=httpx.Response(
            200, content=ndjson({"isFinal": True, "finalResult": "hi"})
        )
    )

    result = retriever.query(SERVICE_ID, "what is x?")

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


@respx.mock
def test_query_body_omits_empty_instructions(retriever: RetrieverAPI) -> None:
    route = respx.post(QUERY_URL).mock(
        return_value=httpx.Response(
            200, content=ndjson({"isFinal": True, "finalResult": "hi"})
        )
    )

    retriever.query(SERVICE_ID, "q", response_instructions="")

    body = json.loads(route.calls[0].request.content)
    assert "response_instructions" not in body
    assert "model" not in body


@respx.mock
def test_query_body_includes_optional_overrides(retriever: RetrieverAPI) -> None:
    route = respx.post(QUERY_URL).mock(
        return_value=httpx.Response(
            200, content=ndjson({"isFinal": True, "finalResult": "hi"})
        )
    )

    retriever.query(
        SERVICE_ID,
        "q",
        mode="DEEP_SEARCH",
        include_metadata=False,
        use_cache=True,
        show_citations=True,
        response_instructions="be terse",
        model="gpt-4.1-mini",
    )

    body = json.loads(route.calls[0].request.content)
    assert body["mode"] == "DEEP_SEARCH"
    assert body["include_metadata"] is False
    assert body["use_cache"] is True
    assert body["show_citations"] is True
    assert body["response_instructions"] == "be terse"
    assert body["model"] == "gpt-4.1-mini"


def test_query_invalid_mode_raises(retriever: RetrieverAPI) -> None:
    # Lowercase is a config error too: the wire wants the uppercase alias.
    with pytest.raises(ConfigError, match="mode"):
        retriever.query_stream(SERVICE_ID, "q", mode="instant")


# -- stream semantics ------------------------------------------------------------------


@respx.mock
def test_query_accumulates_deltas_without_final_result(
    retriever: RetrieverAPI,
) -> None:
    respx.post(QUERY_URL).mock(
        return_value=httpx.Response(
            200,
            content=ndjson(
                {"runId": "r-1", "delta": "Hel"},
                {"delta": "lo"},
                {"isFinal": True},
            ),
        )
    )

    result = retriever.query(SERVICE_ID, "q")

    assert result.answer == "Hello"
    assert result.run_id == "r-1"
    assert result.metadata is None
    assert result.progress == []


@respx.mock
def test_query_final_result_wins_over_deltas(retriever: RetrieverAPI) -> None:
    respx.post(QUERY_URL).mock(
        return_value=httpx.Response(
            200,
            content=ndjson(
                {"delta": "partial"},
                {"isFinal": True, "finalResult": "The full answer."},
            ),
        )
    )

    result = retriever.query(SERVICE_ID, "q")

    assert result.answer == "The full answer."


@respx.mock
def test_query_without_final_frame_falls_back_to_deltas(
    retriever: RetrieverAPI,
) -> None:
    respx.post(QUERY_URL).mock(
        return_value=httpx.Response(200, content=ndjson({"delta": "partial"}))
    )

    result = retriever.query(SERVICE_ID, "q")

    assert result.answer == "partial"


@respx.mock
def test_query_parses_metadata_json_string(retriever: RetrieverAPI) -> None:
    metadata = {
        "citation_mapping": {
            "1": {
                "chunk_id": "c-1",
                "citable_url": "https://docs.example.com/a",
                "content": "chunk text",
            }
        },
        "graph_metadata": {"documents": ["d1"], "edges": ["e1"]},
    }
    respx.post(QUERY_URL).mock(
        return_value=httpx.Response(
            200,
            content=ndjson(
                {"delta": "x"},
                {
                    "isFinal": True,
                    "finalResult": "x",
                    "metadata": json.dumps(metadata),
                },
            ),
        )
    )

    result = retriever.query(SERVICE_ID, "q")

    assert result.metadata == metadata


@respx.mock
def test_query_collects_progress_frames_in_order(retriever: RetrieverAPI) -> None:
    frame1 = {
        "type": "progress",
        "stage": "plan_creation",
        "status": "started",
        "message": "planning",
    }
    frame2 = {
        "type": "progress",
        "stage": "step_execution",
        "status": "step_completed",
        "step_id": 1,
        "total_steps": 2,
    }
    respx.post(QUERY_URL).mock(
        return_value=httpx.Response(
            200,
            content=ndjson(
                {"metadata": json.dumps(frame1)},
                {"metadata": json.dumps(frame2)},
                {"delta": "answer"},
                {"isFinal": True},
            ),
        )
    )

    result = retriever.query(SERVICE_ID, "q", mode="DEEP_SEARCH")

    assert result.progress == [frame1, frame2]
    assert result.answer == "answer"


@respx.mock
def test_query_error_code_in_200_stream_raises(retriever: RetrieverAPI) -> None:
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
        retriever.query(SERVICE_ID, "q")
    assert "CREDENTIAL_CHECK_FAILED" in str(excinfo.value)
    assert "Invalid API key" in str(excinfo.value)


@respx.mock
def test_query_http_error_surfaces_backend_message(retriever: RetrieverAPI) -> None:
    respx.post(QUERY_URL).mock(
        return_value=httpx.Response(
            500,
            json={"error": {"code": 500, "message": "chat model rejected the key"}},
        )
    )

    with pytest.raises(ApiError) as excinfo:
        retriever.query(SERVICE_ID, "q")
    assert excinfo.value.status_code == 500
    assert "chat model rejected the key" in str(excinfo.value)


@respx.mock
def test_query_stream_yields_typed_events_in_order(retriever: RetrieverAPI) -> None:
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

    events = list(retriever.query_stream(SERVICE_ID, "q", mode="DEEP_SEARCH"))

    assert [type(e) for e in events] == [Progress, TokenDelta, TokenDelta, Final]
    assert events[0].data == progress_frame
    assert [e.text for e in events[1:3]] == ["Hel", "lo"]
    final = events[3].result
    assert final.answer == "Hello"
    assert final.run_id == "r-9"
    assert final.progress == [progress_frame]


@respx.mock
def test_query_stream_skips_empty_and_garbage_lines(retriever: RetrieverAPI) -> None:
    content = (
        b"\n"
        + json.dumps({"result": {"delta": "a"}}).encode()
        + b"\n\n   \nnot-json\n"
        + json.dumps({"result": {"isFinal": True}}).encode()
        + b"\n"
    )
    respx.post(QUERY_URL).mock(return_value=httpx.Response(200, content=content))

    result = retriever.query(SERVICE_ID, "q")

    assert result.answer == "a"
