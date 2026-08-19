import base64
import json
import time

import pytest

from arango_ai import Client

BASE = "https://platform.example.com"


def make_jwt(expires_in: float | None = 3600.0) -> str:
    """Unsigned JWT with an exp claim, shaped like what /_open/auth returns."""
    header = base64.urlsafe_b64encode(b'{"alg":"none"}').rstrip(b"=").decode()
    claims: dict[str, object] = {"iss": "arangodb"}
    if expires_in is not None:
        claims["exp"] = time.time() + expires_in
    payload = (
        base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    )
    return f"{header}.{payload}.sig"


@pytest.fixture
def client() -> Client:
    return Client(BASE, "root", "secret", database="testdb")


@pytest.fixture(autouse=True)
def _fast_polling(monkeypatch: pytest.MonkeyPatch) -> None:
    """Polling waits don't sleep in tests; deadlines still apply."""
    monkeypatch.setattr("arango_ai._polling._sleep", lambda _s: None)
