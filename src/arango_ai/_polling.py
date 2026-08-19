"""Polling primitives shared by every async-workflow wrapper.

The platform's long operations are all fire-and-poll; these helpers give the
SDK one consistent wait behavior (deadline, interval, typed timeout error,
and bounded tolerance for transient poll failures — a multi-hour build must
not abort because one status request hit a gateway blip).
"""

from __future__ import annotations

import asyncio
import time
from typing import Awaitable, Callable, TypeVar

import httpx

from .exceptions import ApiError, WaitTimeoutError

T = TypeVar("T")

# Test seams: monkeypatch arango_ai._polling._sleep / _async_sleep to fake time.
_sleep = time.sleep
_async_sleep = asyncio.sleep

# How many CONSECUTIVE transient poll failures a waiter absorbs before the
# last one propagates. Successes reset the counter, so only persistent
# breakage aborts a long wait.
TRANSIENT_POLL_BUDGET = 5


def transient_poll_error(error: BaseException) -> bool:
    """Failures worth retrying inside a wait: transport blips and 5xx.

    4xx are real answers about the request and always propagate.
    """
    if isinstance(error, httpx.RequestError):
        return True
    return isinstance(error, ApiError) and error.status_code >= 500


def wait_until(
    check: Callable[[], T | None],
    *,
    timeout: float,
    interval: float,
    description: str,
    tolerate_transient: bool = False,
) -> T:
    """Poll check() until it returns a non-None result or the deadline passes."""
    deadline = time.monotonic() + timeout
    failures = 0
    while True:
        try:
            result = check()
        except Exception as error:
            failures += 1
            if (
                not tolerate_transient
                or not transient_poll_error(error)
                or failures > TRANSIENT_POLL_BUDGET
            ):
                raise
            result = None
        else:
            failures = 0
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
    tolerate_transient: bool = False,
) -> T:
    """Async twin of wait_until: identical loop, awaited check and sleep."""
    deadline = time.monotonic() + timeout
    failures = 0
    while True:
        try:
            result = await check()
        except Exception as error:
            failures += 1
            if (
                not tolerate_transient
                or not transient_poll_error(error)
                or failures > TRANSIENT_POLL_BUDGET
            ):
                raise
            result = None
        else:
            failures = 0
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
