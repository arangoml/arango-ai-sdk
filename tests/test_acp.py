import json

import httpx
import pytest
import respx

from arango_ai import ConfigError, ServiceNotReadyError, WaitTimeoutError
from arango_ai.acp import ACP_BASE

from .conftest import BASE, make_jwt


@pytest.fixture(autouse=True)
def _auth() -> None:
    respx.post(f"{BASE}/_open/auth").respond(json={"jwt": make_jwt()})


@respx.mock
def test_create_project_sends_snake_case_body(client) -> None:
    route = respx.post(f"{BASE}{ACP_BASE}/project").respond(
        json={"projectName": "demo", "projectType": "autograph"}
    )

    client.acp.create_project("demo", project_type="autograph", description="d")

    body = json.loads(route.calls[0].request.content)
    assert body == {
        "project_name": "demo",
        "project_type": "autograph",
        "project_db_name": "testdb",
        "project_description": "d",
    }


@respx.mock
def test_create_project_omits_absent_description(client) -> None:
    route = respx.post(f"{BASE}{ACP_BASE}/project").respond(json={})

    client.acp.create_project("demo", project_type="autograph")

    body = json.loads(route.calls[0].request.content)
    assert "project_description" not in body


@respx.mock
def test_list_projects_unwraps_projects_map(client) -> None:
    respx.get(f"{BASE}{ACP_BASE}/all_projects/testdb").respond(
        json={"projects": {"demo": {"projectType": "autograph"}}}
    )

    assert client.acp.list_projects() == {"demo": {"projectType": "autograph"}}


@respx.mock
def test_get_and_delete_project_paths(client) -> None:
    get_route = respx.get(f"{BASE}{ACP_BASE}/project_by_name/testdb/demo").respond(
        json={"projectName": "demo"}
    )
    delete_route = respx.delete(f"{BASE}{ACP_BASE}/project/testdb/demo").respond(
        json={"success": True}
    )

    assert client.acp.get_project("demo")["projectName"] == "demo"
    assert client.acp.delete_project("demo")["success"] is True
    assert get_route.called and delete_route.called


@respx.mock
def test_project_name_path_segment_is_url_encoded(client) -> None:
    # Unquoted, '?'/'#' would truncate the path and target the project 'a'.
    get_route = respx.get(f"{BASE}{ACP_BASE}/project_by_name/testdb/a%3Fb%23c").respond(
        json={"projectName": "a?b#c"}
    )
    delete_route = respx.delete(f"{BASE}{ACP_BASE}/project/testdb/a%3Fb%23c").respond(
        json={"success": True}
    )

    client.acp.get_project("a?b#c")
    client.acp.delete_project("a?b#c")

    assert get_route.called and delete_route.called


@respx.mock
def test_create_secret_profile_body_and_unwrap(client) -> None:
    route = respx.post(f"{BASE}{ACP_BASE}/secrets").respond(
        json={"profile": {"profileId": "p-1", "name": "n"}}
    )

    profile = client.acp.create_secret_profile(
        "n", "sk-raw", provider="openai", description="key"
    )

    body = json.loads(route.calls[0].request.content)
    assert body == {
        "name": "n",
        "profile_type": "LLM",
        "secret_data": "sk-raw",
        "provider": "openai",
        "description": "key",
    }
    assert profile["profileId"] == "p-1"


@respx.mock
def test_list_secret_profiles_passes_only_set_filters(client) -> None:
    route = respx.get(f"{BASE}{ACP_BASE}/secrets").respond(json={"profiles": []})

    client.acp.list_secret_profiles(profile_type="LLM", name_contains="demo")

    params = dict(route.calls[0].request.url.params)
    assert params == {"profile_type": "LLM", "name_contains": "demo"}


@respx.mock
def test_list_secret_profiles_rejects_provider_with_pagination(client) -> None:
    route = respx.get(f"{BASE}{ACP_BASE}/secrets").respond(json={"profiles": []})

    # The backend 400s on provider combined with nonzero pagination; the SDK
    # surfaces the constraint before sending anything.
    with pytest.raises(ConfigError, match="provider"):
        client.acp.list_secret_profiles(provider="openai", limit=10)
    with pytest.raises(ConfigError, match="provider"):
        client.acp.list_secret_profiles(provider="openai", offset=5)
    assert not route.called

    # Zero values pass, matching the backend's truthiness-based check.
    client.acp.list_secret_profiles(provider="openai", limit=0, offset=0)
    assert route.called


@respx.mock
def test_start_service_maps_kind_to_chart_name(client) -> None:
    route = respx.post(f"{BASE}{ACP_BASE}/service").respond(
        json={"serviceInfo": {"serviceId": "svc-1", "status": "DEPLOYING"}}
    )

    info = client.acp.start_service("autograph", {"db_name": "testdb"})

    body = json.loads(route.calls[0].request.content)
    assert body["service_name"] == "arangodb-autograph"
    assert body["env"] == {"db_name": "testdb"}
    assert info["serviceId"] == "svc-1"


@respx.mock
def test_start_service_passes_unknown_kind_through(client) -> None:
    route = respx.post(f"{BASE}{ACP_BASE}/service").respond(json={"serviceInfo": {}})

    client.acp.start_service("arangodb-custom-thing", {})

    body = json.loads(route.calls[0].request.content)
    assert body["service_name"] == "arangodb-custom-thing"


@respx.mock
def test_wait_service_deployed_polls_to_terminal(client) -> None:
    route = respx.get(f"{BASE}{ACP_BASE}/service/svc-1")
    route.side_effect = [
        httpx.Response(200, json={"serviceInfo": {"status": "DEPLOYING"}}),
        httpx.Response(200, json={"serviceInfo": {"status": "DEPLOYING"}}),
        httpx.Response(200, json={"serviceInfo": {"status": "DEPLOYED"}}),
    ]

    info = client.acp.wait_service_deployed("svc-1", timeout=5, interval=0)

    assert info["status"] == "DEPLOYED"
    assert route.call_count == 3


@respx.mock
def test_wait_service_deployed_failed_raises(client) -> None:
    respx.get(f"{BASE}{ACP_BASE}/service/svc-1").respond(
        json={"serviceInfo": {"status": "FAILED", "description": "helm error"}}
    )

    with pytest.raises(ServiceNotReadyError) as excinfo:
        client.acp.wait_service_deployed("svc-1", timeout=5, interval=0)
    assert "helm error" in str(excinfo.value)


@respx.mock
def test_wait_service_deployed_timeout(client) -> None:
    respx.get(f"{BASE}{ACP_BASE}/service/svc-1").respond(
        json={"serviceInfo": {"status": "DEPLOYING"}}
    )

    with pytest.raises(WaitTimeoutError):
        client.acp.wait_service_deployed("svc-1", timeout=0.05, interval=0)
