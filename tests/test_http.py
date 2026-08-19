import httpx
import pytest
import respx

from arango_ai import ApiError, ConflictError, InternalServerError, NotFoundError
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


def test_error_detail_reads_fastapi_string_detail() -> None:
    # The File Manager is FastAPI: its HTTPExceptions carry {"detail": "..."}.
    r = _response(400, json={"detail": "scope must be non-empty"})
    assert error_detail(r) == "scope must be non-empty"


def test_error_detail_joins_fastapi_list_detail() -> None:
    # FastAPI validation errors carry detail as a LIST of error objects.
    r = _response(
        422,
        json={
            "detail": [
                {"loc": ["body", "scope"], "msg": "field required"},
                {"loc": ["body", "ids"], "msg": "value is not a valid list"},
            ]
        },
    )
    assert error_detail(r) == "field required; value is not a valid list"


def test_raise_for_status_passes_success_through() -> None:
    r = _response(200, json={})
    assert raise_for_status(r) is r


def test_raise_for_status_raises_with_status_and_detail() -> None:
    with pytest.raises(ApiError) as excinfo:
        raise_for_status(_response(409, json={"error": "BUILD_IN_PROGRESS"}))
    assert excinfo.value.status_code == 409
    assert "BUILD_IN_PROGRESS" in excinfo.value.detail


def test_raise_for_status_maps_status_to_typed_subclasses() -> None:
    with pytest.raises(NotFoundError):
        raise_for_status(_response(404, json={"error": "gone"}))
    with pytest.raises(ConflictError):
        raise_for_status(_response(409, json={"error": "busy"}))
    with pytest.raises(InternalServerError) as excinfo:
        raise_for_status(_response(503, json={"error": "down"}))
    # Catching the ApiError base always works.
    assert isinstance(excinfo.value, ApiError)
    assert excinfo.value.status_code == 503


@respx.mock
def test_client_sends_user_agent(client) -> None:
    respx.post(f"{BASE}/_open/auth").respond(json={"jwt": make_jwt()})
    identity = respx.get(f"{BASE}/_identity").respond(json={"user": "root"})

    client.whoami()

    assert identity.calls[0].request.headers["User-Agent"].startswith("arango-ai/")
