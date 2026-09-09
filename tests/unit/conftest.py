"""Fixtures for tests that never touch the network.

Namespaces receive their :class:`Communication` by constructor and call only
``send_request`` on it, so a stand-in with the same signature is all a unit
test needs: it records what the namespace sent and answers from a script.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, cast

import pytest
from requests_toolbelt import MultipartEncoder
from requests_toolbelt.multipart.decoder import MultipartDecoder

from arango_ai_sdk.communication import Communication


@dataclass
class Part:
    """One part of a recorded multipart body."""

    name: str
    content: bytes
    filename: str | None = None
    content_type: str | None = None

    @property
    def text(self) -> str:
        return self.content.decode()


@dataclass
class Call:
    """One ``send_request`` call as the namespace made it."""

    method: str
    path: str
    headers: dict[str, str]
    timeout: float | None
    params: dict[str, str] | None
    body: Any
    parts: list[Part] = field(default_factory=list)

    def part(self, name: str) -> Part:
        """Return the single part called ``name``."""
        (found,) = [p for p in self.parts if p.name == name]
        return found

    def named(self, name: str) -> list[Part]:
        """Return every part called ``name``, in body order."""
        return [p for p in self.parts if p.name == name]


class FakeCommunication:
    """Stand-in for :class:`Communication` that records calls and answers from a script.

    Each scripted answer is either a body to return or an exception to raise.
    A callable ``data`` is invoked ``attempts`` times, mirroring how the real
    layer rebuilds the body when it retries, so a test can check that every
    attempt gets a complete body.
    """

    def __init__(self, answers: list[Any] | None = None, attempts: int = 1) -> None:
        self.calls: list[Call] = []
        self.attempts = attempts
        self._answers = list(answers or [])

    def send_request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        data: Any = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> Any:
        content_type = (headers or {}).get("content-type", "")
        # Read each attempt's body before building the next one, as the real
        # layer does: a retry only starts once the previous body was consumed.
        for _ in range(self.attempts if callable(data) else 1):
            body = data() if callable(data) else data
            parts = _parts(body, content_type) if isinstance(body, MultipartEncoder) else []
            self.calls.append(Call(method, path, dict(headers or {}), timeout, params, body, parts))
        if not self._answers:
            raise AssertionError(f"no scripted answer left for {method.upper()} {path}")
        answer = self._answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer


def _parts(encoder: MultipartEncoder, content_type: str) -> list[Part]:
    """Decode a multipart body into its parts, with the disposition fields split out."""
    decoded = MultipartDecoder(encoder.to_string(), content_type)
    parts = []
    for raw in decoded.parts:
        disposition = raw.headers[b"Content-Disposition"].decode()
        name = re.search(r'name="([^"]*)"', disposition)
        filename = re.search(r'filename="([^"]*)"', disposition)
        part_type = raw.headers.get(b"Content-Type")
        parts.append(
            Part(
                name=name.group(1) if name else "",
                content=raw.content,
                filename=filename.group(1) if filename else None,
                content_type=part_type.decode() if part_type else None,
            )
        )
    return parts


@pytest.fixture
def fake_communication() -> Callable[..., FakeCommunication]:
    """Build a :class:`FakeCommunication` with scripted answers and attempts."""

    def build(answers: list[Any] | None = None, attempts: int = 1) -> FakeCommunication:
        return FakeCommunication(answers, attempts)

    return build


@pytest.fixture
def as_communication() -> Callable[[FakeCommunication], Communication]:
    """Hand a fake to code typed against the real class."""
    return lambda fake: cast(Communication, fake)
