import httpx
import pytest
import respx

from arango_ai import APIConnectionError, ApiError, AuthenticationError

from .conftest import BASE, make_jwt


@respx.mock
def test_jwt_minted_once_and_attached(client) -> None:
    auth_route = respx.post(f"{BASE}/_open/auth").respond(json={"jwt": make_jwt()})
    identity = respx.get(f"{BASE}/_identity").respond(json={"user": "root"})

    assert client.whoami() == "root"
    assert client.whoami() == "root"

    assert auth_route.call_count == 1  # cached across calls
    sent = identity.calls[0].request.headers["Authorization"]
    assert sent.startswith("Bearer ")


@respx.mock
def test_login_body_carries_credentials(client) -> None:
    auth_route = respx.post(f"{BASE}/_open/auth").respond(json={"jwt": make_jwt()})
    respx.get(f"{BASE}/_identity").respond(json={"user": "root"})

    client.whoami()

    import json

    body = json.loads(auth_route.calls[0].request.content)
    assert body == {"username": "root", "password": "secret"}


@respx.mock
def test_expired_token_is_reminted_proactively(client) -> None:
    # First token is already inside the refresh leeway.
    auth_route = respx.post(f"{BASE}/_open/auth")
    auth_route.side_effect = [
        httpx.Response(200, json={"jwt": make_jwt(expires_in=10)}),
        httpx.Response(200, json={"jwt": make_jwt(expires_in=3600)}),
    ]
    respx.get(f"{BASE}/_identity").respond(json={"user": "root"})

    client.whoami()
    client.whoami()

    assert auth_route.call_count == 2


@respx.mock
def test_401_triggers_one_remint_and_retry(client) -> None:
    auth_route = respx.post(f"{BASE}/_open/auth").respond(json={"jwt": make_jwt()})
    identity = respx.get(f"{BASE}/_identity")
    identity.side_effect = [
        httpx.Response(401, json={"error": "expired"}),
        httpx.Response(200, json={"user": "root"}),
    ]

    assert client.whoami() == "root"
    assert auth_route.call_count == 2  # initial mint + forced re-mint
    assert identity.call_count == 2


@respx.mock
def test_second_401_propagates_as_api_error(client) -> None:
    respx.post(f"{BASE}/_open/auth").respond(json={"jwt": make_jwt()})
    respx.get(f"{BASE}/_identity").respond(401, json={"error": "nope"})

    with pytest.raises(ApiError) as excinfo:
        client.whoami()
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "nope"


@respx.mock
def test_failed_login_raises_authentication_error(client) -> None:
    respx.post(f"{BASE}/_open/auth").respond(401, text="bad credentials")

    with pytest.raises(AuthenticationError):
        client.whoami()


@respx.mock
def test_login_transport_error_wrapped_as_connection_error(client) -> None:
    # The mint must not leak raw httpx exceptions past the SDK's contract.
    respx.post(f"{BASE}/_open/auth").mock(side_effect=httpx.ConnectError("refused"))

    with pytest.raises(APIConnectionError):
        client.whoami()


@respx.mock
def test_token_without_exp_claim_still_works(client) -> None:
    auth_route = respx.post(f"{BASE}/_open/auth").respond(
        json={"jwt": make_jwt(expires_in=None)}
    )
    respx.get(f"{BASE}/_identity").respond(json={"user": "root"})

    client.whoami()
    client.whoami()

    # No exp claim: no proactive refresh, only 401 would force one.
    assert auth_route.call_count == 1


@respx.mock
def test_login_without_jwt_field_raises(client) -> None:
    respx.post(f"{BASE}/_open/auth").respond(json={"ok": True})

    with pytest.raises(AuthenticationError):
        client.whoami()


@respx.mock
def test_login_with_non_json_body_raises_authentication_error(client) -> None:
    respx.post(f"{BASE}/_open/auth").respond(200, text="<html>proxy page</html>")

    with pytest.raises(AuthenticationError, match="non-JSON"):
        client.whoami()


@respx.mock
def test_login_with_json_array_body_raises_authentication_error(client) -> None:
    respx.post(f"{BASE}/_open/auth").respond(200, json=["not", "an", "object"])

    with pytest.raises(AuthenticationError):
        client.whoami()
