import httpx
import pytest
import respx

from arango_ai import ApiError, AuthenticationError

from .conftest import BASE, make_jwt


@respx.mock
async def test_jwt_minted_once_and_attached(async_client) -> None:
    auth_route = respx.post(f"{BASE}/_open/auth").respond(json={"jwt": make_jwt()})
    identity = respx.get(f"{BASE}/_identity").respond(json={"user": "root"})

    assert await async_client.whoami() == "root"
    assert await async_client.whoami() == "root"

    assert auth_route.call_count == 1  # cached across calls
    sent = identity.calls[0].request.headers["Authorization"]
    assert sent.startswith("Bearer ")


@respx.mock
async def test_expired_token_is_reminted_proactively(async_client) -> None:
    # First token is already inside the refresh leeway.
    auth_route = respx.post(f"{BASE}/_open/auth")
    auth_route.side_effect = [
        httpx.Response(200, json={"jwt": make_jwt(expires_in=10)}),
        httpx.Response(200, json={"jwt": make_jwt(expires_in=3600)}),
    ]
    respx.get(f"{BASE}/_identity").respond(json={"user": "root"})

    await async_client.whoami()
    await async_client.whoami()

    assert auth_route.call_count == 2


@respx.mock
async def test_401_triggers_one_remint_and_retry(async_client) -> None:
    auth_route = respx.post(f"{BASE}/_open/auth").respond(json={"jwt": make_jwt()})
    identity = respx.get(f"{BASE}/_identity")
    identity.side_effect = [
        httpx.Response(401, json={"error": "expired"}),
        httpx.Response(200, json={"user": "root"}),
    ]

    assert await async_client.whoami() == "root"
    assert auth_route.call_count == 2  # initial mint + forced re-mint
    assert identity.call_count == 2


@respx.mock
async def test_second_401_propagates_as_api_error(async_client) -> None:
    respx.post(f"{BASE}/_open/auth").respond(json={"jwt": make_jwt()})
    respx.get(f"{BASE}/_identity").respond(401, json={"error": "nope"})

    with pytest.raises(ApiError) as excinfo:
        await async_client.whoami()
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "nope"


@respx.mock
async def test_failed_login_raises_authentication_error(async_client) -> None:
    respx.post(f"{BASE}/_open/auth").respond(401, text="bad credentials")

    with pytest.raises(AuthenticationError):
        await async_client.whoami()
