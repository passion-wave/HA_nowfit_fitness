"""Versioned persistence for session cookies and the login retry budget."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from aiohttp import CookieJar
from yarl import URL


def export_cookies(jar: CookieJar, now: datetime) -> list[dict[str, Any]]:
    """Export only unexpired NowFit cookies without logging them."""
    records: list[dict[str, Any]] = []
    for cookie in jar:
        domain = cookie["domain"] or "nowfit.memberarea.club"
        if domain.lstrip(".") != "nowfit.memberarea.club":
            continue
        max_age = cookie["max-age"]
        expires_at = now.timestamp() + int(max_age) if max_age and max_age.isdigit() else None
        records.append(
            {
                "name": cookie.key,
                "value": cookie.value,
                "domain": domain,
                "path": cookie["path"] or "/",
                "secure": bool(cookie["secure"]),
                "expires_at": expires_at,
            }
        )
    return records


def restore_cookies(jar: CookieJar, records: list[dict[str, Any]], now: datetime) -> int:
    restored = 0
    for item in records:
        if item.get("expires_at") is not None and float(item["expires_at"]) <= now.timestamp():
            continue
        if str(item.get("domain", "")).lstrip(".") != "nowfit.memberarea.club":
            continue
        jar.update_cookies(
            {str(item["name"]): str(item["value"])},
            response_url=URL.build(
                scheme="https",
                host="nowfit.memberarea.club",
                path=str(item.get("path") or "/"),
            ),
        )
        restored += 1
    return restored


class NowFitCookieStore:
    """Small HA Store wrapper; payload is versioned and contains no HTML."""

    def __init__(self, hass, entry_id: str) -> None:
        from homeassistant.helpers.storage import Store

        self._store = Store(hass, 1, f"nowfit.{entry_id}.session")
        self._last_cookies: list[dict[str, Any]] | None = None
        self._next_allowed_login_at: datetime | None = None

    async def async_load_into(self, jar: CookieJar, now: datetime) -> int:
        data = await self._store.async_load() or {}
        cookies = list(data.get("cookies", []))
        next_allowed = data.get("next_allowed_login_at")
        try:
            parsed = datetime.fromisoformat(str(next_allowed)) if next_allowed else None
            self._next_allowed_login_at = (
                parsed if parsed is not None and parsed.tzinfo is not None else None
            )
        except ValueError:
            self._next_allowed_login_at = None
        restored = restore_cookies(jar, cookies, now)
        self._last_cookies = export_cookies(jar, now)
        return restored

    async def async_save_from(
        self,
        jar: CookieJar,
        now: datetime,
    ) -> None:
        cookies = export_cookies(jar, now)
        await self._store.async_save(
            {
                "cookies": cookies,
                "next_allowed_login_at": (
                    self._next_allowed_login_at.isoformat()
                    if self._next_allowed_login_at is not None
                    else None
                ),
            }
        )
        self._last_cookies = cookies

    async def async_save_if_changed(self, jar: CookieJar, now: datetime) -> None:
        cookies = export_cookies(jar, now)
        if cookies != self._last_cookies:
            await self.async_save_from(jar, now)

    async def async_claim_relogin(self, now: datetime) -> bool:
        """Persistently allow at most one failed relogin per 30 minutes."""
        if self._next_allowed_login_at is not None and now < self._next_allowed_login_at:
            return False
        self._next_allowed_login_at = now + timedelta(minutes=30)
        await self._store.async_save(
            {
                "cookies": self._last_cookies or [],
                "next_allowed_login_at": self._next_allowed_login_at.isoformat(),
            }
        )
        return True

    async def async_clear_relogin_guard(self) -> None:
        """Clear the persistent guard after a complete successful login."""
        self._next_allowed_login_at = None
        await self._store.async_save(
            {"cookies": self._last_cookies or [], "next_allowed_login_at": None}
        )
