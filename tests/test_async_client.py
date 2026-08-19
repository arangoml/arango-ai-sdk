import pytest
import respx

from arango_ai import AsyncClient, ConfigError

from .conftest import BASE, make_jwt


@respx.mock
async def test_context_manager_whoami_and_close() -> None:
    respx.post(f"{BASE}/_open/auth").respond(json={"jwt": make_jwt()})
    respx.get(f"{BASE}/_identity").respond(json={"user": "root"})

    async with AsyncClient(BASE, "root", "secret", database="testdb") as client:
        assert await client.whoami() == "root"
        http = client.http
    assert http.is_closed


def test_from_env_builds_config() -> None:
    client = AsyncClient.from_env(
        {
            "ARANGO_URL": BASE,
            "ARANGO_USERNAME": "root",
            "ARANGO_PASSWORD": "secret",
            "ARANGO_DATABASE": "testdb",
        }
    )
    assert client.config.base_url == BASE
    assert client.acp.database == "testdb"


def test_from_env_missing_variables_raises() -> None:
    with pytest.raises(ConfigError, match="ARANGO_URL"):
        AsyncClient.from_env({})
