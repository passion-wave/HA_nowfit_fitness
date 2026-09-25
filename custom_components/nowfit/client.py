"""Safe asynchronous HTTP clients for NowFit."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin, urlparse
from zoneinfo import ZoneInfo

import aiohttp
from multidict import MultiDict

from .const import (
    ACCOUNT_PATH,
    ALLOWED_HOST,
    BASE_URL,
    HISTORY_PATH,
    LOGIN_PATH,
    MAX_REDIRECTS,
    MAX_RESPONSE_BYTES,
    OCCUPANCY_PATH,
)
from .exceptions import (
    CannotConnect,
    InvalidCredentials,
    RateLimited,
    SessionExpired,
    UnexpectedContent,
    UnsafeRedirect,
    UpstreamUnavailable,
)
from .models import AccountSnapshot, ClubOccupancy
from .parsers import parse_account, parse_history, parse_login_form, parse_occupancy
from .parsers.history import RawVisit


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != ALLOWED_HOST
        or parsed.port not in {None, 443}
    ):
        raise UnsafeRedirect(url)


class NowFitHttpClient:
    """Bounded, same-origin HTTP wrapper."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session
        self._on_success: Callable[[], Awaitable[None]] | None = None

    def set_success_callback(self, callback: Callable[[], Awaitable[None]]) -> None:
        self._on_success = callback

    async def _request(
        self,
        method: str,
        path_or_url: str,
        *,
        request_timeout: int,
        data: MultiDict[str] | None = None,
    ) -> tuple[str, str]:
        url = urljoin(BASE_URL, path_or_url)
        _validate_url(url)
        try:
            for _ in range(MAX_REDIRECTS + 1):
                async with asyncio.timeout(request_timeout):
                    response = await self._session.request(
                        method,
                        url,
                        data=data,
                        allow_redirects=False,
                        headers={"Accept": "text/html"},
                    )
                if 300 <= response.status < 400:
                    location = response.headers.get("Location")
                    response.release()
                    if not location:
                        raise UnexpectedContent("redirect_without_location")
                    url = urljoin(url, location)
                    _validate_url(url)
                    method, data = "GET", None
                    continue
                if response.status == 429:
                    retry = response.headers.get("Retry-After")
                    response.release()
                    raise RateLimited(retry)
                if response.status >= 500:
                    response.release()
                    raise UpstreamUnavailable(f"http_{response.status}")
                if response.status in {401, 403}:
                    response.release()
                    raise SessionExpired(f"http_{response.status}")
                if response.status >= 400:
                    response.release()
                    raise UnexpectedContent(f"http_{response.status}")
                content_type = response.headers.get("Content-Type", "").casefold()
                if "html" not in content_type:
                    response.release()
                    raise UnexpectedContent("not_html")
                payload = await response.content.read(MAX_RESPONSE_BYTES + 1)
                final_url = str(response.url)
                response.release()
                if len(payload) > MAX_RESPONSE_BYTES:
                    raise UnexpectedContent("response_too_large")
                if self._on_success is not None:
                    await self._on_success()
                return payload.decode(response.charset or "utf-8", errors="replace"), final_url
            raise UnsafeRedirect("too_many_redirects")
        except (TimeoutError, aiohttp.ClientError) as err:
            raise CannotConnect(type(err).__name__) from err


class PublicClient(NowFitHttpClient):
    async def async_get_clubs(self) -> tuple[ClubOccupancy, ...]:
        html, _ = await self._request("GET", OCCUPANCY_PATH, request_timeout=15)
        return parse_occupancy(html)


class MemberClient(NowFitHttpClient):
    async def async_login(self, email: str, password: str, remember: bool) -> AccountSnapshot:
        login_html, login_url = await self._request("GET", LOGIN_PATH, request_timeout=20)
        form = parse_login_form(login_html, login_url)
        payload: MultiDict[str] = MultiDict(form.hidden_fields)
        payload.add(form.email_name, email.strip())
        payload.add(form.password_name, password)
        if form.remember_name:
            if remember:
                payload.add(form.remember_name, "true")
            payload.add(form.remember_name, "false")
        html, final_url = await self._request("POST", form.action, request_timeout=20, data=payload)
        if urlparse(final_url).path == LOGIN_PATH or 'type="password"' in html.casefold():
            raise InvalidCredentials("login_not_accepted")
        return await self.async_get_account()

    async def async_get_account(self) -> AccountSnapshot:
        html, final_url = await self._request("GET", ACCOUNT_PATH, request_timeout=20)
        if urlparse(final_url).path == LOGIN_PATH:
            raise SessionExpired("redirected_to_login")
        return parse_account(html, datetime.now(ZoneInfo("UTC")))

    async def async_get_history(self, timezone: ZoneInfo) -> tuple[RawVisit, ...]:
        html, final_url = await self._request("GET", HISTORY_PATH, request_timeout=20)
        if urlparse(final_url).path == LOGIN_PATH:
            raise SessionExpired("redirected_to_login")
        return parse_history(html, timezone)


def parse_retry_after(value: str | None, now: datetime) -> datetime | None:
    if not value:
        return None
    try:
        return now + timedelta(seconds=max(0, int(value)))
    except ValueError:
        try:
            return parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None
