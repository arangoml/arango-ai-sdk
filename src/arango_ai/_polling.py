"""Polling primitives shared by every async-workflow wrapper.

The platform's long operations are all fire-and-poll; these helpers give the
SDK one consistent wait behavior (deadline, interval, typed timeout error).
"""

from __future__ import annotations

import time
from typing import Callable, TypeVar

from .exceptions import WaitTimeoutError

T = TypeVar("T")

# Test seam: monkeypatch arango_ai._polling._sleep to fake time.
_sleep = time.sleep


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
