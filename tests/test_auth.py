import asyncio

import pytest

from custom_components.nowfit.auth import SessionManager
from custom_components.nowfit.exceptions import (
    InvalidCredentials,
    SessionExpired,
    UpstreamUnavailable,
)


class FakeClient:
    def __init__(self) -> None:
        self.calls = 0
        self.clears = 0

    def clear_session(self) -> None:
        self.clears += 1

    async def async_login(self, email, password, remember):
        self.calls += 1
        await asyncio.sleep(0)


async def test_relogin_is_single_flight() -> None:
    client = FakeClient()
    manager = SessionManager(client, "member@example.test", "secret", True)
    await asyncio.gather(manager.async_recover(0), manager.async_recover(0))
    assert client.calls == 1
    assert client.clears == 1
    assert manager.generation == 1


async def test_relogin_without_stored_password_requires_reauth() -> None:
    manager = SessionManager(FakeClient(), "member@example.test", None, False)
    with pytest.raises(SessionExpired, match="reauth_required"):
        await manager.async_recover(0)


async def test_relogin_budget_is_bounded() -> None:
    manager = SessionManager(FakeClient(), "member@example.test", "secret", True)
    await manager.async_recover(0)
    await manager.async_recover(1)
    with pytest.raises(SessionExpired, match="login_budget_exhausted"):
        await manager.async_recover(2)


class RejectingClient(FakeClient):
    async def async_login(self, email, password, remember):
        raise InvalidCredentials


async def test_rejected_stored_password_is_forgotten() -> None:
    manager = SessionManager(RejectingClient(), "member@example.test", "secret", True)
    with pytest.raises(InvalidCredentials):
        await manager.async_recover(0)
    with pytest.raises(SessionExpired, match="reauth_required"):
        await manager.async_recover(0)


async def test_persistent_relogin_guard_blocks_repeated_attempt() -> None:
    client = FakeClient()

    async def deny_claim() -> bool:
        return False

    manager = SessionManager(
        client,
        "member@example.test",
        "secret",
        True,
        claim_relogin=deny_claim,
    )

    with pytest.raises(UpstreamUnavailable, match="relogin_cooldown"):
        await manager.async_recover(0)
    assert client.calls == 0
    assert client.clears == 0


async def test_successful_guarded_relogin_clears_guard() -> None:
    events = []

    async def allow_claim() -> bool:
        events.append("claim")
        return True

    async def clear_guard() -> None:
        events.append("clear")

    manager = SessionManager(
        FakeClient(),
        "member@example.test",
        "secret",
        True,
        claim_relogin=allow_claim,
        relogin_succeeded=clear_guard,
    )

    await manager.async_recover(0)
    assert events == ["claim", "clear"]
