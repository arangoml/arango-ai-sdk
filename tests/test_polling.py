import httpx
import pytest

from arango_ai import InternalServerError, NotFoundError, WaitTimeoutError
from arango_ai._polling import wait_until


def test_wait_until_recovers_within_transient_budget() -> None:
    calls = {"n": 0}

    def check() -> str | None:
        calls["n"] += 1
        if calls["n"] <= 5:
            raise httpx.ConnectError("blip")
        return "done"

    outcome = wait_until(
        check, timeout=60, interval=0, description="x", tolerate_transient=True
    )

    # Exactly the budget of 5 consecutive transient failures is absorbed.
    assert outcome == "done"
    assert calls["n"] == 6


def test_wait_until_sixth_consecutive_transient_failure_propagates() -> None:
    calls = {"n": 0}

    def check() -> str | None:
        calls["n"] += 1
        raise InternalServerError(503, "down")

    with pytest.raises(InternalServerError):
        wait_until(
            check, timeout=60, interval=0, description="x", tolerate_transient=True
        )

    assert calls["n"] == 6


def test_wait_until_success_resets_transient_budget() -> None:
    # 5 failures, one successful-but-pending poll, 5 more failures: the
    # reset means none of them exceeds the consecutive budget.
    script: list[str] = ["fail"] * 5 + ["pending"] + ["fail"] * 5 + ["done"]

    def check() -> str | None:
        step = script.pop(0)
        if step == "fail":
            raise httpx.ConnectError("blip")
        return None if step == "pending" else step

    outcome = wait_until(
        check, timeout=60, interval=0, description="x", tolerate_transient=True
    )

    assert outcome == "done"
    assert script == []


def test_wait_until_never_retries_4xx_api_error() -> None:
    calls = {"n": 0}

    def check() -> str | None:
        calls["n"] += 1
        raise NotFoundError(404, "gone")

    # 4xx is a real answer about the request, not a transient blip.
    with pytest.raises(NotFoundError):
        wait_until(
            check, timeout=60, interval=0, description="x", tolerate_transient=True
        )

    assert calls["n"] == 1


def test_wait_until_without_tolerance_propagates_first_transient() -> None:
    def check() -> str | None:
        raise httpx.ConnectError("blip")

    with pytest.raises(httpx.ConnectError):
        wait_until(check, timeout=60, interval=0, description="x")


def test_wait_until_transient_failures_do_not_extend_deadline() -> None:
    def check() -> str | None:
        raise InternalServerError(500, "down")

    # timeout 0: the first tolerated failure still hits the deadline check.
    with pytest.raises(WaitTimeoutError):
        wait_until(
            check, timeout=0, interval=0, description="x", tolerate_transient=True
        )
