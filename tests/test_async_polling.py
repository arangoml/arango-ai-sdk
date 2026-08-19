import pytest

from arango_ai import WaitTimeoutError
from arango_ai._polling import async_wait_for_streak, async_wait_until


async def test_wait_until_returns_first_non_none() -> None:
    results: list[str | None] = [None, None, "done"]

    async def check() -> str | None:
        return results.pop(0)

    outcome = await async_wait_until(
        check, timeout=5, interval=0, description="a thing"
    )

    assert outcome == "done"
    assert results == []


async def test_wait_until_timeout_raises_with_description() -> None:
    async def check() -> str | None:
        return None

    with pytest.raises(WaitTimeoutError, match="a thing"):
        await async_wait_until(check, timeout=0.05, interval=0, description="a thing")


async def test_wait_for_streak_flap_resets() -> None:
    # Two successes, one flap, then three in a row: the flap must wipe the
    # first streak, so all six probes are consumed.
    results = [True, True, False, True, True, True]

    async def check() -> bool:
        return results.pop(0)

    await async_wait_for_streak(
        check, needed=3, interval=0, timeout=5, description="health"
    )

    assert results == []


async def test_wait_for_streak_timeout() -> None:
    async def check() -> bool:
        return False

    with pytest.raises(WaitTimeoutError, match="3 consecutive"):
        await async_wait_for_streak(
            check, needed=3, interval=0, timeout=0.05, description="health"
        )
