"""JWT authentication against the platform gateway.

The gateway authenticates every route with an ArangoDB JWT. The Studio UI
gets this for free as a same-origin session cookie; the SDK is cross-origin,
so it mints the JWT itself via POST /_open/auth and attaches it as an
Authorization bearer on every request.

Long-running builds outlive the ~1h token, so the auth layer re-mints
proactively near expiry (decoded from the JWT exp claim, no signature
verification client-side) and retries exactly once on an unexpected 401.

JwtAuth and AsyncJwtAuth share every mint/refresh/retry decision through
_JwtTokenState; only the transport (blocking vs awaited) differs.
"""

from __future__ import annotations

import asyncio
import base64
import json
import threading
import time
import typing

import httpx

from .exceptions import APIConnectionError, APITimeoutError, AuthenticationError

# Re-mint when less than this many seconds remain on the token.
_EXPIRY_LEEWAY_S = 60.0


def _decode_expiry(jwt: str) -> float | None:
    """Best-effort read of the exp claim; None when undecodable.

    Deliberately broad except: this decoder is advisory (an unknown expiry
    just disables proactive refresh, the 401-retry still covers it), so no
    oddly-shaped token may ever crash a request.
    """
    try:
        payload_b64 = jwt.split(".")[1]
        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        exp = payload.get("exp")
        return float(exp) if exp is not None else None
    except Exception:  # noqa: BLE001 - advisory decode, see docstring
        return None


def _is_expiring(expires_at: float | None) -> bool:
    """Inside the proactive-refresh leeway; an unknown expiry never expires."""
    return expires_at is not None and expires_at - time.time() < _EXPIRY_LEEWAY_S


def _jwt_from_response(response: httpx.Response) -> str:
    """The minted JWT out of an /_open/auth response, or the typed error."""
    if response.status_code >= 400:
        raise AuthenticationError(
            f"/_open/auth failed with HTTP {response.status_code}: "
            f"{response.text[:300]}"
        )
    jwt = response.json().get("jwt")
    if not jwt:
        raise AuthenticationError("login succeeded but no 'jwt' in response")
    return str(jwt)


class _JwtTokenState:
    """Credentials and token state shared by the sync and async auth hooks."""

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
        self._jwt: str | None = None
        self._expires_at: float | None = None

    @property
    def _login_body(self) -> dict[str, str]:
        return {"username": self._username, "password": self._password}

    def _store(self, jwt: str) -> str:
        self._jwt = jwt
        self._expires_at = _decode_expiry(jwt)
        return jwt


class JwtAuth(_JwtTokenState, httpx.Auth):
    """httpx auth hook: mint, attach, proactively refresh, retry once on 401.

    Sync-only by design: httpx would otherwise silently run the base class's
    no-op flow on an async transport, so AsyncClient pairs with AsyncJwtAuth
    below instead of reusing this hook.
    """

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        *,
        verify_tls: bool = True,
        timeout: float = 30.0,
    ) -> None:
        super().__init__(
            base_url, username, password, verify_tls=verify_tls, timeout=timeout
        )
        self._lock = threading.Lock()

    def _mint(self) -> str:
        try:
            response = httpx.post(
                f"{self._base_url}/_open/auth",
                json=self._login_body,
                verify=self._verify_tls,
                timeout=self._timeout,
            )
        except httpx.TimeoutException as error:
            raise APITimeoutError(f"login timed out: {error}") from error
        except httpx.RequestError as error:
            raise APIConnectionError(f"login failed to connect: {error}") from error
        return _jwt_from_response(response)

    def token(self, *, force: bool = False) -> str:
        """Current JWT, minting or re-minting when needed. Thread-safe."""
        with self._lock:
            jwt = self._jwt
            if force or jwt is None or _is_expiring(self._expires_at):
                jwt = self._store(self._mint())
            return jwt

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


class AsyncJwtAuth(_JwtTokenState, httpx.Auth):
    """Async twin of JwtAuth: same mint/refresh/retry semantics, awaited I/O."""

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        *,
        verify_tls: bool = True,
        timeout: float = 30.0,
    ) -> None:
        super().__init__(
            base_url, username, password, verify_tls=verify_tls, timeout=timeout
        )
        self._lock = asyncio.Lock()

    async def _mint(self) -> str:
        # A short-lived client per mint: minting happens rarely (login plus
        # roughly hourly), and the main client cannot be reused — its auth
        # hook is this object, which would recurse into another mint.
        try:
            async with httpx.AsyncClient(
                verify=self._verify_tls, timeout=self._timeout
            ) as http:
                response = await http.post(
                    f"{self._base_url}/_open/auth", json=self._login_body
                )
        except httpx.TimeoutException as error:
            raise APITimeoutError(f"login timed out: {error}") from error
        except httpx.RequestError as error:
            raise APIConnectionError(f"login failed to connect: {error}") from error
        return _jwt_from_response(response)

    async def token(self, *, force: bool = False) -> str:
        """Current JWT, minting or re-minting when needed. Task-safe."""
        async with self._lock:
            jwt = self._jwt
            if force or jwt is None or _is_expiring(self._expires_at):
                jwt = self._store(await self._mint())
            return jwt

    async def async_auth_flow(
        self, request: httpx.Request
    ) -> typing.AsyncGenerator[httpx.Request, httpx.Response]:
        request.headers["Authorization"] = f"Bearer {await self.token()}"
        response = yield request
        if response.status_code == 401:
            # One retry with a fresh token; a second 401 propagates to the
            # caller as a normal ApiError.
            request.headers["Authorization"] = f"Bearer {await self.token(force=True)}"
            yield request
