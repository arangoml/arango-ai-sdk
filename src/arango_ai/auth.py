"""JWT authentication against the platform gateway.

The gateway authenticates every route with an ArangoDB JWT. The Studio UI
gets this for free as a same-origin session cookie; the SDK is cross-origin,
so it mints the JWT itself via POST /_open/auth and attaches it as an
Authorization bearer on every request.

Long-running builds outlive the ~1h token, so the auth layer re-mints
proactively near expiry (decoded from the JWT exp claim, no signature
verification client-side) and retries exactly once on an unexpected 401.
"""

from __future__ import annotations

import base64
import binascii
import json
import threading
import time
import typing

import httpx

from .exceptions import AuthenticationError

# Re-mint when less than this many seconds remain on the token.
_EXPIRY_LEEWAY_S = 60.0


def _decode_expiry(jwt: str) -> float | None:
    """Best-effort read of the exp claim; None when undecodable."""
    try:
        payload_b64 = jwt.split(".")[1]
        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        exp = payload.get("exp")
        return float(exp) if exp is not None else None
    except (IndexError, ValueError, binascii.Error):
        return None


class JwtAuth(httpx.Auth):
    """httpx auth hook: mint, attach, proactively refresh, retry once on 401."""

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        *,
        verify_tls: bool = True,
        timeout: float = 30.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._username = username
        self._password = password
        self._verify_tls = verify_tls
        self._timeout = timeout
        self._lock = threading.Lock()
        self._jwt: str | None = None
        self._expires_at: float | None = None

    def _mint(self) -> str:
        response = httpx.post(
            f"{self._base_url}/_open/auth",
            json={"username": self._username, "password": self._password},
            verify=self._verify_tls,
            timeout=self._timeout,
        )
        if response.status_code >= 400:
            raise AuthenticationError(
                f"/_open/auth failed with HTTP {response.status_code}: "
                f"{response.text[:300]}"
            )
        jwt = response.json().get("jwt")
        if not jwt:
            raise AuthenticationError("login succeeded but no 'jwt' in response")
        return str(jwt)

    def token(self, *, force: bool = False) -> str:
        """Current JWT, minting or re-minting when needed. Thread-safe."""
        with self._lock:
            expired = (
                self._expires_at is not None
                and self._expires_at - time.time() < _EXPIRY_LEEWAY_S
            )
            if force or self._jwt is None or expired:
                self._jwt = self._mint()
                self._expires_at = _decode_expiry(self._jwt)
            return self._jwt

    def sync_auth_flow(
        self, request: httpx.Request
    ) -> typing.Generator[httpx.Request, httpx.Response, None]:
        request.headers["Authorization"] = f"Bearer {self.token()}"
        response = yield request
        if response.status_code == 401:
            # One retry with a fresh token; a second 401 propagates to the
            # caller as a normal ApiError.
            request.headers["Authorization"] = f"Bearer {self.token(force=True)}"
            yield request

    def async_auth_flow(
        self, request: httpx.Request
    ) -> typing.AsyncGenerator[httpx.Request, httpx.Response]:
        raise NotImplementedError(
            "the alpha SDK is sync-only; async support is planned post-alpha"
        )
