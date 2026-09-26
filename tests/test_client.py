from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from multidict import CIMultiDict
from yarl import URL

from custom_components.nowfit.client import (
    MemberClient,
    PublicClient,
    _validate_url,
    parse_retry_after,
)
from custom_components.nowfit.exceptions import (
    RateLimited,
    UnexpectedContent,
    UnsafeRedirect,
    UpstreamUnavailable,
)

FIXTURES = Path(__file__).parent / "fixtures"


class FakeContent:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    async def read(self, size: int) -> bytes:
        return self.payload[:size]


class FakeResponse:
    def __init__(self, status, body="", *, url="https://nowfit.memberarea.club/x", headers=None):
        self.status = status
        self.headers = CIMultiDict(headers or {"Content-Type": "text/html; charset=utf-8"})
        self.content = FakeContent(body.encode())
        self.url = URL(url)
        self.charset = "utf-8"
        self.released = False

    def release(self) -> None:
        self.released = True


class FakeSession:
    def __init__(self, *responses) -> None:
        self.responses = list(responses)
        self.requests = []

    async def request(self, method, url, **kwargs):
        self.requests.append((method, url, kwargs))
        return self.responses.pop(0)


def test_url_validation_rejects_wrong_scheme_host_and_port() -> None:
    _validate_url("https://nowfit.memberarea.club/Person/MyAccount")
    for url in (
        "http://nowfit.memberarea.club/",
        "https://example.net/",
        "https://nowfit.memberarea.club:444/",
    ):
        with pytest.raises(UnsafeRedirect):
            _validate_url(url)


def test_retry_after_seconds_and_date() -> None:
    now = datetime(2026, 9, 25, 12, tzinfo=ZoneInfo("UTC"))
    assert parse_retry_after("60", now) == now + timedelta(seconds=60)
    assert parse_retry_after("Fri, 25 Sep 2026 12:02:00 GMT", now) == now + timedelta(minutes=2)
    assert parse_retry_after("broken", now) is None


async def test_public_client_parses_response() -> None:
    response = FakeResponse(
        200,
        (FIXTURES / "occupancy.html").read_text(),
        url="https://nowfit.memberarea.club/CheckinCounter/GetClubsCheckinCounterPage",
    )
    clubs = await PublicClient(FakeSession(response)).async_get_clubs()
    assert clubs[1].checked_in == 17
    assert response.released


async def test_redirect_is_checked_before_following() -> None:
    session = FakeSession(FakeResponse(302, headers={"Location": "https://example.net/steal"}))
    with pytest.raises(UnsafeRedirect):
        await PublicClient(session).async_get_clubs()
    assert len(session.requests) == 1


async def test_rate_limit_and_content_guards() -> None:
    with pytest.raises(RateLimited):
        await PublicClient(
            FakeSession(FakeResponse(429, headers={"Retry-After": "60"}))
        ).async_get_clubs()
    with pytest.raises(UnexpectedContent, match="not_html"):
        await PublicClient(
            FakeSession(FakeResponse(200, headers={"Content-Type": "application/json"}))
        ).async_get_clubs()
    with pytest.raises(UnexpectedContent, match="response_too_large"):
        await PublicClient(
            FakeSession(FakeResponse(200, "x" * (2 * 1024 * 1024 + 1)))
        ).async_get_clubs()


async def test_upstream_error_identifies_only_safe_operation_and_status() -> None:
    client = MemberClient(FakeSession(FakeResponse(503)))

    with pytest.raises(UpstreamUnavailable, match=r"^http_503:account$"):
        await client.async_get_account()


async def test_member_login_preserves_browser_checkbox_order() -> None:
    login = (FIXTURES / "login.html").read_text()
    account = (FIXTURES / "account.html").read_text()
    session = FakeSession(
        FakeResponse(200, login, url="https://nowfit.memberarea.club/Account/Login"),
        FakeResponse(
            302,
            url="https://nowfit.memberarea.club/Account/Login",
            headers={"Location": "/Person/MyAccount"},
        ),
        FakeResponse(200, account, url="https://nowfit.memberarea.club/Person/MyAccount"),
        FakeResponse(200, account, url="https://nowfit.memberarea.club/Person/MyAccount"),
    )
    result = await MemberClient(session).async_login("member@example.test", "secret", True)
    payload = session.requests[1][2]["data"]
    assert payload.getall("RememberMe") == ["true", "false"]
    assert result.checkins_week == 2
