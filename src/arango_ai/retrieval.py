"""Retriever namespace: deploy, health gate, and query (streaming + blocking).

The retriever is a generic ACP service (chart arangodb-graphrag-retriever)
served under a fixed gateway route pattern /graphrag/retriever/{id}/v1/...,
where {id} is the ACP serviceId with the chart prefix stripped (the Studio
UI's cleanServiceId). The only query endpoint streams NDJSON `result`
envelopes; the blocking `query` drains that stream client-side.

RetrieverAPI and AsyncRetrieverAPI are twins: request bodies, health-probe
interpretation, and the whole NDJSON frame protocol live in shared helpers
(_query_body, _health_tick, _FrameAccumulator); the twins add only the I/O.

Run history is deliberately not exposed in the alpha (V2 per PM decision).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, AsyncIterator, Iterator

import httpx

from ._polling import async_wait_for_streak, wait_for_streak
from .exceptions import (
    APIConnectionError,
    ApiError,
    APITimeoutError,
    ConfigError,
    QueryError,
    ServiceNotReadyError,
)
from .http import error_detail

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .client import AsyncClient, Client

__all__ = [
    "AsyncRetrieverAPI",
    "Final",
    "GRAPHRAG_RETRIEVER_PREFIX",
    "HEALTHY_CONSECUTIVE_OK",
    "Progress",
    "QueryEvent",
    "QueryResult",
    "RetrieverAPI",
    "TokenDelta",
    "build_retriever_env",
    "clean_service_id",
]

# ACP serviceIds carry the chart name; the gateway route carries only the pod
# part. Mirrors the UI's GRAPHRAG_RETRIEVER_PREFIX (formatServiceId.ts).
GRAPHRAG_RETRIEVER_PREFIX = "arangodb-graphrag-retriever-"

# Gateway routes flap while propagating; require this many consecutive 200s
# before treating the retriever as live (UI: HEALTHY_CONSECUTIVE_OK).
HEALTHY_CONSECUTIVE_OK = 3

_SERVICE_KIND = "graphragretriever"
_ROUTE_PREFIX = "/graphrag/retriever"
_QUERY_MODES = frozenset({"INSTANT", "DEEP_SEARCH"})


def clean_service_id(service_id: str, prefix: str = GRAPHRAG_RETRIEVER_PREFIX) -> str:
    """Strip the chart prefix from an ACP serviceId (UI: cleanServiceId).

    A bare prefix would strip to nothing, which cannot be a route segment,
    so the original id is returned instead (same guard as the UI).
    """
    if service_id.startswith(prefix):
        return service_id[len(prefix) :] or service_id
    return service_id


@dataclass(frozen=True)
class TokenDelta:
    """One streamed answer fragment."""

    text: str


@dataclass(frozen=True)
class Progress:
    """One Deep Search progress frame (snake_case fields, as sent)."""

    data: dict[str, Any]


@dataclass(frozen=True)
class QueryResult:
    """Final outcome of one retriever query.

    `progress` carries the same Progress objects the stream yielded, so
    both access paths share one shape.
    """

    answer: str
    run_id: str | None
    metadata: dict[str, Any] | None
    progress: list[Progress]

    def __str__(self) -> str:
        # print(project.ask(...)) should read as the answer, notebook-first.
        return self.answer


@dataclass(frozen=True)
class Final:
    """Terminal stream event carrying the assembled result."""

    result: QueryResult


QueryEvent = TokenDelta | Progress | Final


def build_retriever_env(
    *,
    database: str,
    project_name: str,
    chat_provider: str,
    chat_model: str,
    embedding_provider: str | None = None,
    embedding_model: str | None = None,
    chat_secret_profile_id: str | None = None,
    embedding_secret_profile_id: str | None = None,
    chat_api_url: str | None = None,
    embedding_api_url: str | None = None,
) -> dict[str, str]:
    """Deploy env for the retriever service (UI: buildRetrieverEnv).

    snake_case keys, optional keys omitted so the service falls back to its
    own defaults; api_url only for custom (OpenAI-compatible) providers.
    Chat and embedding credentials are independent: auto-reusing the chat
    secret for embedding sent the chat key to a corpus-locked embedding
    endpoint, which rejected queries with a 401 — so nothing is shared here,
    each role gets exactly what the caller gave. Always secret profile ids,
    never raw keys.
    """
    env: dict[str, str] = {
        "db_name": database,
        "genai_project_name": project_name,
        "chat_api_provider": chat_provider,
        "chat_model": chat_model,
    }
    if chat_provider == "custom":
        if not chat_api_url:
            raise ConfigError("chat_provider 'custom' requires chat_api_url")
        env["chat_api_url"] = chat_api_url
    if embedding_model is not None:
        provider = embedding_provider or "openai"
        env["embedding_api_provider"] = provider
        env["embedding_model"] = embedding_model
        if provider == "custom":
            if not embedding_api_url:
                raise ConfigError(
                    "embedding_provider 'custom' requires embedding_api_url"
                )
            env["embedding_api_url"] = embedding_api_url
    elif embedding_provider is not None:
        # A provider without a model would deploy a half-configured embedding
        # role that the service cannot complete on its own.
        raise ConfigError("embedding_provider given without embedding_model")
    if chat_secret_profile_id:
        env["chat_secret_profile_id"] = chat_secret_profile_id
    if embedding_secret_profile_id:
        env["embedding_secret_profile_id"] = embedding_secret_profile_id
    return env


def _health_url(cleaned_id: str) -> str:
    return f"{_ROUTE_PREFIX}/{cleaned_id}/v1/health"


def _query_url(cleaned_id: str) -> str:
    return f"{_ROUTE_PREFIX}/{cleaned_id}/v1/graphrag-query-stream"


def _health_tick(response: httpx.Response, service_id: str) -> bool:
    """Interpret one health probe: True only for a healthy 200.

    Mirrors the UI's useServiceHealth: a 4xx means the gateway route is
    still propagating (keep polling); a 5xx or an explicit FAIL body means
    the pod answered and is broken — more polling cannot fix that, so fail
    fast with the backend's message.
    """
    if response.status_code >= 500:
        raise ServiceNotReadyError(
            f"retriever {service_id} health check failed with "
            f"{response.status_code}: {error_detail(response)}"
        )
    if not 200 <= response.status_code < 300:
        # 4xx: the gateway route is still propagating. 3xx: a proxy or
        # ingress redirect answered, not the service — neither is healthy.
        return False
    try:
        body = response.json()
    except (json.JSONDecodeError, ValueError):
        # An unreadable 200 body still counts as healthy (UI behavior).
        body = None
    if isinstance(body, dict) and body.get("status") == "FAIL":
        raise ServiceNotReadyError(
            str(body.get("message") or "the retriever reported an unhealthy status")
        )
    return True


def _query_body(
    query: str,
    *,
    mode: str,
    include_metadata: bool,
    use_cache: bool,
    show_citations: bool,
    response_instructions: str | None,
    model: str | None,
) -> dict[str, Any]:
    """Wire body for one query, mode validated up front."""
    if mode not in _QUERY_MODES:
        raise ConfigError(f"mode must be one of {sorted(_QUERY_MODES)}, got {mode!r}")
    body: dict[str, Any] = {
        "query": query,
        "mode": mode,
        # Fixed discriminator on this endpoint (the UI always sends 0).
        "provider": 0,
        "include_metadata": include_metadata,
        "use_cache": use_cache,
        "show_citations": show_citations,
    }
    if response_instructions:
        body["response_instructions"] = response_instructions
    if model:
        # Per-query chat model override; omitted = deploy default.
        body["model"] = model
    return body


class _FrameAccumulator:
    """NDJSON stream state, mirroring the UI's useRetrieverQuery.

    feed() digests one line and returns the events to yield; final() closes
    the stream, raising QueryError when an in-stream errorCode arrived.
    Shared verbatim by the sync and async stream loops so the two protocols
    cannot drift.
    """

    def __init__(self) -> None:
        self._run_id: str | None = None
        self._error_code: str | None = None
        self._final_result: str | None = None
        self._metadata_raw: str | None = None
        self._deltas: list[str] = []
        self._progress: list[Progress] = []

    def feed(self, line: str) -> list[QueryEvent]:
        frame = _parse_frame(line)
        if frame is None:
            return []
        if self._run_id is None and frame.get("runId"):
            self._run_id = str(frame["runId"])
        if frame.get("errorCode"):
            # A failed query can arrive inside an HTTP 200 stream (e.g. the
            # credential precheck); surfaced after the stream ends, never as
            # an answer.
            self._error_code = str(frame["errorCode"])
        if frame.get("isFinal"):
            final = frame.get("finalResult")
            if final:
                self._final_result = str(final)
            raw = frame.get("metadata")
            if raw:
                self._metadata_raw = str(raw)
            return []
        events: list[QueryEvent] = []
        raw = frame.get("metadata")
        if raw:
            parsed = _json_dict_or_none(str(raw))
            if parsed is not None and parsed.get("type") == "progress":
                # The identical object is yielded now and collected for the
                # final QueryResult, so both access paths share one shape.
                progress = Progress(parsed)
                self._progress.append(progress)
                events.append(progress)
        delta = frame.get("delta")
        if delta:
            self._deltas.append(str(delta))
            events.append(TokenDelta(str(delta)))
        return events

    def final(self) -> Final:
        answer = self._final_result or "".join(self._deltas)
        if self._error_code:
            # The failure detail arrives as the final text (UI shows exactly
            # that); keep the code so callers can branch on it.
            raise QueryError(
                f"{self._error_code}: {answer}" if answer else self._error_code
            )
        return Final(
            QueryResult(
                answer=answer,
                run_id=self._run_id,
                metadata=(
                    _json_dict_or_none(self._metadata_raw)
                    if self._metadata_raw
                    else None
                ),
                progress=self._progress,
            )
        )


class RetrieverAPI:
    """Retriever service lifecycle and querying."""

    def __init__(self, client: "Client") -> None:
        self._client = client

    # -- deploy ----------------------------------------------------------------

    def deploy(
        self,
        project: str,
        *,
        chat_model: str,
        chat_provider: str = "openai",
        embedding_model: str | None = None,
        embedding_provider: str | None = None,
        chat_secret_profile_id: str | None = None,
        embedding_secret_profile_id: str | None = None,
        chat_api_url: str | None = None,
        embedding_api_url: str | None = None,
        wait: bool = True,
        deploy_timeout: float = 300.0,
        health_timeout: float = 300.0,
    ) -> dict[str, Any]:
        """Deploy a retriever for a project; by default gate on real health.

        Helm DEPLOYED only means the install was accepted, so `wait` also
        runs the health streak — queries only work once the pod answers.
        Returns the ACP serviceInfo (fresh after the deploy wait).
        """
        env = build_retriever_env(
            database=self._client.acp.database,
            project_name=project,
            chat_provider=chat_provider,
            chat_model=chat_model,
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
            chat_secret_profile_id=chat_secret_profile_id,
            embedding_secret_profile_id=embedding_secret_profile_id,
            chat_api_url=chat_api_url,
            embedding_api_url=embedding_api_url,
        )
        info = self._client.acp.start_service(_SERVICE_KIND, env)
        if wait:
            service_id = str(info.get("serviceId", ""))
            info = self._client.acp.wait_service_deployed(
                service_id, timeout=deploy_timeout
            )
            self.wait_healthy(service_id, timeout=health_timeout)
        return info

    # -- health ----------------------------------------------------------------

    def wait_healthy(
        self,
        service_id: str,
        *,
        needed: int = HEALTHY_CONSECUTIVE_OK,
        interval: float = 5.0,
        timeout: float = 300.0,
    ) -> None:
        """Block until the retriever answers `needed` consecutive healthy 200s.

        Any flap (4xx, network error) resets the streak; a FAIL body or a 5xx
        raises ServiceNotReadyError immediately (see _health_tick).
        """
        wait_for_streak(
            lambda: self._check_health(service_id),
            needed=needed,
            interval=interval,
            timeout=timeout,
            description=f"retriever service {service_id} to serve",
        )

    def _check_health(self, service_id: str) -> bool:
        cleaned = clean_service_id(service_id)
        try:
            response = self._client.http.get(_health_url(cleaned))
        except httpx.HTTPError:
            # Only transport flaps are "not yet". SDK-typed errors (e.g.
            # AuthenticationError from a failing token re-mint) propagate:
            # retrying them would hammer the login endpoint until timeout.
            return False
        return _health_tick(response, service_id)

    # -- query -----------------------------------------------------------------

    def query_stream(
        self,
        service_id: str,
        query: str,
        *,
        mode: str = "INSTANT",
        include_metadata: bool = True,
        use_cache: bool = False,
        show_citations: bool = False,
        response_instructions: str | None = None,
        model: str | None = None,
        timeout: float = 600.0,
    ) -> Iterator[QueryEvent]:
        """Stream one query: TokenDelta / Progress events, then one Final.

        Only streaming exists on the service; both modes answer as NDJSON
        `result` envelopes. An in-stream errorCode (a failed query delivered
        inside an HTTP 200) raises QueryError after the stream ends instead
        of yielding a Final. The default timeout matches the retriever
        route's 10-minute gateway deadline.
        """
        body = _query_body(
            query,
            mode=mode,
            include_metadata=include_metadata,
            use_cache=use_cache,
            show_citations=show_citations,
            response_instructions=response_instructions,
            model=model,
        )
        return self._stream(clean_service_id(service_id), body, timeout)

    def query(
        self,
        service_id: str,
        query: str,
        *,
        mode: str = "INSTANT",
        include_metadata: bool = True,
        use_cache: bool = False,
        show_citations: bool = False,
        response_instructions: str | None = None,
        model: str | None = None,
        timeout: float = 600.0,
    ) -> QueryResult:
        """Blocking query: drain the stream and return the assembled result.

        Progress frames travel inside the Final's QueryResult; deltas are
        discarded (the final answer already contains them).
        """
        result: QueryResult | None = None
        for event in self.query_stream(
            service_id,
            query,
            mode=mode,
            include_metadata=include_metadata,
            use_cache=use_cache,
            show_citations=show_citations,
            response_instructions=response_instructions,
            model=model,
            timeout=timeout,
        ):
            if isinstance(event, Final):
                result = event.result
        if result is None:  # defensive: _stream always ends in Final or raises
            raise QueryError("stream ended without a final frame")
        return result

    def _stream(
        self, cleaned_id: str, body: dict[str, Any], timeout: float
    ) -> Iterator[QueryEvent]:
        state = _FrameAccumulator()
        try:
            with self._client.http.stream(
                "POST", _query_url(cleaned_id), json=body, timeout=timeout
            ) as response:
                if response.status_code >= 400:
                    # Read before raising: the real backend message lives in
                    # the (still unread) body, and the stream closes with the
                    # context.
                    response.read()
                    raise ApiError(response.status_code, _query_error_detail(response))
                for line in response.iter_lines():
                    yield from state.feed(line)
        except httpx.RequestError as error:
            raise _stream_transport_error(error) from error
        yield state.final()


class AsyncRetrieverAPI:
    """Async twin of RetrieverAPI: same lifecycle, health gate, and stream."""

    def __init__(self, client: "AsyncClient") -> None:
        self._client = client

    # -- deploy ----------------------------------------------------------------

    async def deploy(
        self,
        project: str,
        *,
        chat_model: str,
        chat_provider: str = "openai",
        embedding_model: str | None = None,
        embedding_provider: str | None = None,
        chat_secret_profile_id: str | None = None,
        embedding_secret_profile_id: str | None = None,
        chat_api_url: str | None = None,
        embedding_api_url: str | None = None,
        wait: bool = True,
        deploy_timeout: float = 300.0,
        health_timeout: float = 300.0,
    ) -> dict[str, Any]:
        """Async twin of RetrieverAPI.deploy."""
        env = build_retriever_env(
            database=self._client.acp.database,
            project_name=project,
            chat_provider=chat_provider,
            chat_model=chat_model,
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
            chat_secret_profile_id=chat_secret_profile_id,
            embedding_secret_profile_id=embedding_secret_profile_id,
            chat_api_url=chat_api_url,
            embedding_api_url=embedding_api_url,
        )
        info = await self._client.acp.start_service(_SERVICE_KIND, env)
        if wait:
            service_id = str(info.get("serviceId", ""))
            info = await self._client.acp.wait_service_deployed(
                service_id, timeout=deploy_timeout
            )
            await self.wait_healthy(service_id, timeout=health_timeout)
        return info

    # -- health ----------------------------------------------------------------

    async def wait_healthy(
        self,
        service_id: str,
        *,
        needed: int = HEALTHY_CONSECUTIVE_OK,
        interval: float = 5.0,
        timeout: float = 300.0,
    ) -> None:
        """Async twin of RetrieverAPI.wait_healthy."""
        await async_wait_for_streak(
            lambda: self._check_health(service_id),
            needed=needed,
            interval=interval,
            timeout=timeout,
            description=f"retriever service {service_id} to serve",
        )

    async def _check_health(self, service_id: str) -> bool:
        cleaned = clean_service_id(service_id)
        try:
            response = await self._client.http.get(_health_url(cleaned))
        except httpx.HTTPError:
            # Only transport flaps are "not yet". SDK-typed errors (e.g.
            # AuthenticationError from a failing token re-mint) propagate:
            # retrying them would hammer the login endpoint until timeout.
            return False
        return _health_tick(response, service_id)

    # -- query -----------------------------------------------------------------

    def query_stream(
        self,
        service_id: str,
        query: str,
        *,
        mode: str = "INSTANT",
        include_metadata: bool = True,
        use_cache: bool = False,
        show_citations: bool = False,
        response_instructions: str | None = None,
        model: str | None = None,
        timeout: float = 600.0,
    ) -> AsyncIterator[QueryEvent]:
        """Async twin of RetrieverAPI.query_stream.

        Deliberately not an async generator itself so a bad mode raises
        ConfigError at the call, not at the first iteration (same eager
        validation as the sync twin).
        """
        body = _query_body(
            query,
            mode=mode,
            include_metadata=include_metadata,
            use_cache=use_cache,
            show_citations=show_citations,
            response_instructions=response_instructions,
            model=model,
        )
        return self._stream(clean_service_id(service_id), body, timeout)

    async def query(
        self,
        service_id: str,
        query: str,
        *,
        mode: str = "INSTANT",
        include_metadata: bool = True,
        use_cache: bool = False,
        show_citations: bool = False,
        response_instructions: str | None = None,
        model: str | None = None,
        timeout: float = 600.0,
    ) -> QueryResult:
        """Async twin of RetrieverAPI.query (drains the stream)."""
        result: QueryResult | None = None
        async for event in self.query_stream(
            service_id,
            query,
            mode=mode,
            include_metadata=include_metadata,
            use_cache=use_cache,
            show_citations=show_citations,
            response_instructions=response_instructions,
            model=model,
            timeout=timeout,
        ):
            if isinstance(event, Final):
                result = event.result
        if result is None:  # defensive: _stream always ends in Final or raises
            raise QueryError("stream ended without a final frame")
        return result

    async def _stream(
        self, cleaned_id: str, body: dict[str, Any], timeout: float
    ) -> AsyncIterator[QueryEvent]:
        state = _FrameAccumulator()
        try:
            async with self._client.http.stream(
                "POST", _query_url(cleaned_id), json=body, timeout=timeout
            ) as response:
                if response.status_code >= 400:
                    # Read before raising: the real backend message lives in
                    # the (still unread) body, and the stream closes with the
                    # context.
                    await response.aread()
                    raise ApiError(response.status_code, _query_error_detail(response))
                async for line in response.aiter_lines():
                    for event in state.feed(line):
                        yield event
        except httpx.RequestError as error:
            raise _stream_transport_error(error) from error
        yield state.final()


def _parse_frame(line: str) -> dict[str, Any] | None:
    """One NDJSON line -> the `result` envelope payload, or None to skip."""
    if not line.strip():
        return None
    try:
        envelope = json.loads(line)
    except json.JSONDecodeError:
        return None
    if not isinstance(envelope, dict):
        return None
    result = envelope.get("result")
    return result if isinstance(result, dict) else None


def _json_dict_or_none(raw: str) -> dict[str, Any] | None:
    """Parse a metadata JSON string; anything unparseable degrades to None.

    The answer is already complete when metadata is read, so a broken
    metadata payload must not fail the query (UI behaves the same).
    """
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _stream_transport_error(error: httpx.RequestError) -> APIConnectionError:
    """Typed wrapper for a transport failure while opening or reading a
    query stream — raw httpx exceptions must not leak past the SDK's
    one-base-type error contract."""
    if isinstance(error, httpx.TimeoutException):
        return APITimeoutError(f"query stream timed out: {error}")
    return APIConnectionError(f"query stream transport failed: {error}")


def _query_error_detail(response: httpx.Response) -> str:
    """Query failures nest the message: {"error": {"code": int, "message": str}}."""
    try:
        body = response.json()
    except (json.JSONDecodeError, ValueError):
        return error_detail(response)
    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str) and message:
                return message
    return error_detail(response)
