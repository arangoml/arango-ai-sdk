import json

import httpx
import pytest
import respx

from arango_ai import ConfigError
from arango_ai.acp import ACP_BASE

from .conftest import BASE, make_jwt
from .test_autograph_onboarding import PROJECT_WITH_SERVICE


@pytest.fixture(autouse=True)
def _auth() -> None:
    respx.post(f"{BASE}/_open/auth").respond(json={"jwt": make_jwt()})


@respx.mock
async def test_create_project_full_onboarding(async_client) -> None:
    respx.post(f"{BASE}{ACP_BASE}/project").respond(json={})
    respx.get(f"{BASE}/_identity").respond(json={"user": "heiko"})
    secret_route = respx.post(f"{BASE}{ACP_BASE}/secrets").respond(
        json={"profile": {"profileId": "p-9"}}
    )
    service_route = respx.post(f"{BASE}{ACP_BASE}/service").respond(
        json={"serviceInfo": {"serviceId": "svc-1", "status": "DEPLOYING"}}
    )
    status_route = respx.get(f"{BASE}{ACP_BASE}/service/svc-1")
    status_route.side_effect = [
        httpx.Response(200, json={"serviceInfo": {"status": "DEPLOYING"}}),
        httpx.Response(200, json={"serviceInfo": {"status": "DEPLOYED"}}),
    ]
    respx.get(f"{BASE}{ACP_BASE}/project_by_name/testdb/demo").respond(
        json=PROJECT_WITH_SERVICE
    )
    # Route flap: a lone 200 must not count; three consecutive are needed.
    health_route = respx.get(f"{BASE}/autograph/wzfue/v1/health")
    health_route.side_effect = [
        httpx.Response(404),
        httpx.Response(200),
        httpx.Response(404),
        httpx.Response(200),
        httpx.Response(200),
        httpx.Response(200),
    ]

    project = await async_client.autograph.create_project(
        "demo", openai_api_key="sk-raw", serving_timeout=5
    )

    assert project.name == "demo"
    secret_body = json.loads(secret_route.calls[0].request.content)
    assert secret_body["secret_data"] == "sk-raw"
    assert secret_body["name"].startswith("demo-llm-")

    env = json.loads(service_route.calls[0].request.content)["env"]
    assert env["chat_secret_profile_id"] == "p-9"
    assert env["embedding_secret_profile_id"] == "p-9"  # one key, both roles
    assert env["fps_recovery_username"] == "heiko"
    assert "chat_api_key" not in env  # raw keys never travel in deploy envs

    assert status_route.call_count == 2
    assert health_route.call_count == 6  # flap resets the streak


@respx.mock
async def test_create_project_without_credentials_raises(async_client) -> None:
    respx.post(f"{BASE}{ACP_BASE}/project").respond(json={})

    with pytest.raises(ConfigError, match="openai_api_key"):
        await async_client.autograph.create_project("demo")
