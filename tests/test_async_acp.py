import json

import httpx
import pytest
import respx

from arango_ai import ServiceNotReadyError
from arango_ai.acp import ACP_BASE

from .conftest import BASE, make_jwt


@pytest.fixture(autouse=True)
def _auth() -> None:
    respx.post(f"{BASE}/_open/auth").respond(json={"jwt": make_jwt()})


@respx.mock
async def test_create_project_sends_snake_case_body(async_client) -> None:
    route = respx.post(f"{BASE}{ACP_BASE}/project").respond(
        json={"projectName": "demo", "projectType": "autograph"}
    )

    await async_client.acp.create_project(
        "demo", project_type="autograph", description="d"
    )

    body = json.loads(route.calls[0].request.content)
    assert body == {
        "project_name": "demo",
        "project_type": "autograph",
        "project_db_name": "testdb",
        "project_description": "d",
    }


@respx.mock
async def test_wait_service_deployed_polls_to_terminal(async_client) -> None:
    route = respx.get(f"{BASE}{ACP_BASE}/service/svc-1")
    route.side_effect = [
        httpx.Response(200, json={"serviceInfo": {"status": "DEPLOYING"}}),
        httpx.Response(200, json={"serviceInfo": {"status": "DEPLOYING"}}),
        httpx.Response(200, json={"serviceInfo": {"status": "DEPLOYED"}}),
    ]

    info = await async_client.acp.wait_service_deployed("svc-1", timeout=5, interval=0)

    assert info["status"] == "DEPLOYED"
    assert route.call_count == 3


@respx.mock
async def test_wait_service_deployed_failed_raises(async_client) -> None:
    respx.get(f"{BASE}{ACP_BASE}/service/svc-1").respond(
        json={"serviceInfo": {"status": "FAILED", "description": "helm error"}}
    )

    with pytest.raises(ServiceNotReadyError) as excinfo:
        await async_client.acp.wait_service_deployed("svc-1", timeout=5, interval=0)
    assert "helm error" in str(excinfo.value)
