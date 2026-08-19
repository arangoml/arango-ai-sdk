import httpx
import pytest
import respx

from arango_ai import ApiError
from arango_ai.http import error_detail, raise_for_status

from .conftest import BASE, make_jwt


def _response(status: int, **kwargs) -> httpx.Response:
    return httpx.Response(status, request=httpx.Request("GET", BASE), **kwargs)


def test_error_detail_prefers_error_key() -> None:
    r = _response(400, json={"error": "boom", "message": "other"})
    assert error_detail(r) == "boom"


def test_error_detail_falls_back_to_message() -> None:
    r = _response(400, json={"message": "from message"})
    assert error_detail(r) == "from message"


def test_error_detail_non_json_body() -> None:
    r = _response(502, text="<html>bad gateway</html>")
    assert error_detail(r) == "Request failed: 502"


def test_error_detail_ignores_non_string_error() -> None:
    r = _response(400, json={"error": {"code": 3}, "message": "usable"})
    assert error_detail(r) == "usable"


def test_raise_for_status_passes_success_through() -> None:
    r = _response(200, json={})
    assert raise_for_status(r) is r


def test_raise_for_status_raises_with_status_and_detail() -> None:
    with pytest.raises(ApiError) as excinfo:
        raise_for_status(_response(409, json={"error": "BUILD_IN_PROGRESS"}))
    assert excinfo.value.status_code == 409
    assert "BUILD_IN_PROGRESS" in excinfo.value.detail


@respx.mock
def test_client_sends_user_agent(client) -> None:
    respx.post(f"{BASE}/_open/auth").respond(json={"jwt": make_jwt()})
    identity = respx.get(f"{BASE}/_identity").respond(json={"user": "root"})

    client.whoami()

    assert identity.calls[0].request.headers["User-Agent"].startswith("arango-ai/")
