import json

import httpx
import pytest
import respx

from arango_ai import ApiError, ConfigError
from arango_ai.acp import ACP_BASE
from arango_ai.autograph import build_autograph_env

from .conftest import BASE, make_jwt

SERVICE_URL = "https://internal.host/autograph/wzfue/"
PROJECT_WITH_SERVICE = {
    "projectName": "demo",
    "projectType": "autograph",
    "projectMetadata": {"autographService": {"serviceUrl": SERVICE_URL}},
    "modelSettings": {"chatSecretProfileId": "p-1"},
}


@pytest.fixture(autouse=True)
def _auth() -> None:
    respx.post(f"{BASE}/_open/auth").respond(json={"jwt": make_jwt()})


# -- env building ------------------------------------------------------------


def test_build_env_full_shape() -> None:
    env = build_autograph_env(
        database="db1",
        project_name="demo",
        chat_provider="openai",
        chat_model="gpt-4.1",
        embedding_provider="openai",
        embedding_model="text-embedding-3-small",
        chat_secret_profile_id="p-1",
        embedding_secret_profile_id="p-1",
        fps_recovery_username="heiko",
    )
    assert env == {
        "db_name": "db1",
        "genai_project_name": "demo",
        "chat_api_provider": "openai",
        "embedding_api_provider": "openai",
        "chat_model": "gpt-4.1",
        "embedding_model": "text-embedding-3-small",
        "chat_secret_profile_id": "p-1",
        "embedding_secret_profile_id": "p-1",
        "fps_recovery_username": "heiko",
    }


def test_build_env_optional_fields() -> None:
    env = build_autograph_env(
        database="db1",
        project_name="demo",
        chat_provider="custom",
        chat_model="m",
        embedding_provider="custom",
        embedding_model="e",
        chat_secret_profile_id="p-1",
        embedding_secret_profile_id="p-2",
        multimodal_model="mm",
        chat_api_url="https://llm.example.com/v1",
        embedding_api_url="https://emb.example.com/v1",
    )
    assert env["multimodal_model"] == "mm"
    assert env["chat_api_url"] == "https://llm.example.com/v1"
    assert env["embedding_api_url"] == "https://emb.example.com/v1"
    assert "fps_recovery_username" not in env


# -- create_project ------------------------------------------------------------


@respx.mock
def test_create_project_without_deploy_only_registers(client) -> None:
    project_route = respx.post(f"{BASE}{ACP_BASE}/project").respond(json={})
    service_route = respx.post(f"{BASE}{ACP_BASE}/service").respond(json={})

    project = client.autograph.create_project("demo", deploy=False)

    assert project.name == "demo"
    body = json.loads(project_route.calls[0].request.content)
    assert body["project_type"] == "autograph"
    assert not service_route.called


@respx.mock
def test_create_project_full_onboarding(client) -> None:
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

    project = client.autograph.create_project(
        "demo", openai_api_key="sk-raw", serving_timeout=5
    )

    assert project.name == "demo"
    secret_body = json.loads(secret_route.calls[0].request.content)
    assert secret_body["profile_type"] == "LLM"
    assert secret_body["provider"] == "openai"
    assert secret_body["secret_data"] == "sk-raw"
    assert secret_body["name"].startswith("demo-llm-")

    env = json.loads(service_route.calls[0].request.content)["env"]
    assert env["db_name"] == "testdb"
    assert env["genai_project_name"] == "demo"
    assert env["chat_secret_profile_id"] == "p-9"
    assert env["embedding_secret_profile_id"] == "p-9"  # one key, both roles
    assert env["fps_recovery_username"] == "heiko"
    assert "chat_api_key" not in env  # raw keys never travel in deploy envs

    assert status_route.call_count == 2
    assert health_route.call_count == 6  # flap resets the streak


@respx.mock
def test_create_project_with_explicit_profile_ids_skips_secret_creation(
    client,
) -> None:
    respx.post(f"{BASE}{ACP_BASE}/project").respond(json={})
    respx.get(f"{BASE}/_identity").respond(json={"user": "heiko"})
    secret_route = respx.post(f"{BASE}{ACP_BASE}/secrets").respond(json={})
    service_route = respx.post(f"{BASE}{ACP_BASE}/service").respond(
        json={"serviceInfo": {"serviceId": "svc-1", "status": "DEPLOYING"}}
    )

    client.autograph.create_project(
        "demo",
        chat_secret_profile_id="p-chat",
        embedding_secret_profile_id="p-emb",
        wait=False,
    )

    assert not secret_route.called
    env = json.loads(service_route.calls[0].request.content)["env"]
    assert env["chat_secret_profile_id"] == "p-chat"
    assert env["embedding_secret_profile_id"] == "p-emb"


@respx.mock
def test_create_project_identity_failure_is_best_effort(client) -> None:
    respx.post(f"{BASE}{ACP_BASE}/project").respond(json={})
    respx.get(f"{BASE}/_identity").respond(500, json={"error": "boom"})
    service_route = respx.post(f"{BASE}{ACP_BASE}/service").respond(
        json={"serviceInfo": {"serviceId": "svc-1", "status": "DEPLOYING"}}
    )

    client.autograph.create_project("demo", chat_secret_profile_id="p-1", wait=False)

    env = json.loads(service_route.calls[0].request.content)["env"]
    assert "fps_recovery_username" not in env


@respx.mock
def test_create_project_without_credentials_raises(client) -> None:
    respx.post(f"{BASE}{ACP_BASE}/project").respond(json={})

    with pytest.raises(ConfigError, match="openai_api_key"):
        client.autograph.create_project("demo")


# -- bind / list ---------------------------------------------------------------


@respx.mock
def test_project_bind_verifies_existence(client) -> None:
    respx.get(f"{BASE}{ACP_BASE}/project_by_name/testdb/demo").respond(
        json=PROJECT_WITH_SERVICE
    )

    project = client.autograph.project("demo")

    assert project.name == "demo"
    assert project.service_path() == "/autograph/wzfue"


@respx.mock
def test_project_bind_missing_raises(client) -> None:
    respx.get(f"{BASE}{ACP_BASE}/project_by_name/testdb/nope").respond(
        404, json={"error": "not found"}
    )

    with pytest.raises(ApiError) as excinfo:
        client.autograph.project("nope")
    assert excinfo.value.status_code == 404


@respx.mock
def test_list_projects_filters_autograph_type(client) -> None:
    respx.get(f"{BASE}{ACP_BASE}/all_projects/testdb").respond(
        json={
            "projects": {
                "ag1": {"projectType": "autograph"},
                "other": {"projectType": "graphrag"},
                "ag2": {"projectType": "autograph"},
            }
        }
    )

    assert client.autograph.list_projects() == ["ag1", "ag2"]


# -- project handle --------------------------------------------------------------


@respx.mock
def test_model_settings_read(client) -> None:
    respx.get(f"{BASE}{ACP_BASE}/project_by_name/testdb/demo").respond(
        json=PROJECT_WITH_SERVICE
    )

    project = client.autograph.project("demo")

    assert project.model_settings() == {"chatSecretProfileId": "p-1"}


@respx.mock
def test_delete_uses_service_teardown_when_deployed(client) -> None:
    respx.get(f"{BASE}{ACP_BASE}/project_by_name/testdb/demo").respond(
        json=PROJECT_WITH_SERVICE
    )
    teardown = respx.delete(f"{BASE}/autograph/wzfue/v1/projects/demo").respond(
        json={"deleted": True, "warnings": []}
    )
    acp_delete = respx.delete(f"{BASE}{ACP_BASE}/project/testdb/demo").respond(
        json={"success": True}
    )

    result = client.autograph.project("demo").delete()

    assert result == {"deleted": True, "warnings": []}
    assert teardown.calls[0].request.url.params["delete_files"] == "true"
    assert not acp_delete.called


@respx.mock
def test_delete_falls_back_to_acp_without_service(client) -> None:
    respx.get(f"{BASE}{ACP_BASE}/project_by_name/testdb/demo").respond(
        json={"projectName": "demo", "projectType": "autograph"}
    )
    acp_delete = respx.delete(f"{BASE}{ACP_BASE}/project/testdb/demo").respond(
        json={"success": True}
    )

    result = client.autograph.project("demo").delete()

    assert result == {"success": True}
    assert acp_delete.called
