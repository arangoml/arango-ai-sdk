"""Polling primitives shared by every async-workflow wrapper.

The platform's long operations are all fire-and-poll; these helpers give the
SDK one consistent wait behavior (deadline, interval, typed timeout error).
"""

from __future__ import annotations

import asyncio
import time
from typing import Awaitable, Callable, TypeVar

from .exceptions import WaitTimeoutError

T = TypeVar("T")

# Test seams: monkeypatch arango_ai._polling._sleep / _async_sleep to fake time.
_sleep = time.sleep
_async_sleep = asyncio.sleep


def wait_until(
    check: Callable[[], T | None],
    *,
    timeout: float,
    interval: float,
    description: str,
) -> T:
    """Poll check() until it returns a non-None result or the deadline passes."""
    deadline = time.monotonic() + timeout
    while True:
        result = check()
        if result is not None:
            return result
        if time.monotonic() >= deadline:
            raise WaitTimeoutError(
                f"timed out after {timeout:.0f}s waiting for {description}"
            )
        _sleep(interval)


def wait_for_streak(
    check: Callable[[], bool],
    *,
    needed: int,
    interval: float,
    timeout: float,
    description: str,
) -> None:
    """Require `needed` consecutive successes.

    Gateway routes flap while propagating (a lone 200 sandwiched between
    404s has been observed), so a single success must not count as healthy.
    Mirrors the UI's SERVING_CONSECUTIVE_OK / HEALTHY_CONSECUTIVE_OK = 3.
    """
    deadline = time.monotonic() + timeout
    streak = 0
    while True:
        streak = streak + 1 if check() else 0
        if streak >= needed:
            return
        if time.monotonic() >= deadline:
            raise WaitTimeoutError(
                f"timed out after {timeout:.0f}s waiting for {description} "
                f"({needed} consecutive successes required)"
            )
        _sleep(interval)


async def async_wait_until(
    check: Callable[[], Awaitable[T | None]],
    *,
    timeout: float,
    interval: float,
    description: str,
) -> T:
    """Async twin of wait_until: identical loop, awaited check and sleep."""
    deadline = time.monotonic() + timeout
    while True:
        result = await check()
        if result is not None:
            return result
        if time.monotonic() >= deadline:
            raise WaitTimeoutError(
                f"timed out after {timeout:.0f}s waiting for {description}"
            )
        await _async_sleep(interval)


async def async_wait_for_streak(
    check: Callable[[], Awaitable[bool]],
    *,
    needed: int,
    interval: float,
    timeout: float,
    description: str,
) -> None:
    """Async twin of wait_for_streak: identical loop, awaited check and sleep."""
    deadline = time.monotonic() + timeout
    streak = 0
    while True:
        streak = streak + 1 if await check() else 0
        if streak >= needed:
            return
        if time.monotonic() >= deadline:
            raise WaitTimeoutError(
                f"timed out after {timeout:.0f}s waiting for {description} "
                f"({needed} consecutive successes required)"
            )
        await _async_sleep(interval)
