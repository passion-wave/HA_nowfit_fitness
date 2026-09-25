from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiohttp import CookieJar
from yarl import URL

from custom_components.nowfit.cookie_store import export_cookies, restore_cookies


async def test_cookie_roundtrip_and_expiry() -> None:
    now = datetime(2026, 9, 25, tzinfo=ZoneInfo("UTC"))
    jar = CookieJar()
    jar.update_cookies(
        {"session": "opaque"},
        response_url=URL("https://nowfit.memberarea.club/Account/Login"),
    )
    records = export_cookies(jar, now)
    assert records[0]["value"] == "opaque"
    restored = CookieJar()
    assert restore_cookies(restored, records, now) == 1
    records[0]["expires_at"] = (now - timedelta(seconds=1)).timestamp()
    assert restore_cookies(CookieJar(), records, now) == 0


async def test_foreign_cookie_is_not_restored() -> None:
    now = datetime(2026, 9, 25, tzinfo=ZoneInfo("UTC"))
    assert (
        restore_cookies(
            CookieJar(),
            [{"name": "x", "value": "y", "domain": "example.net", "path": "/"}],
            now,
        )
        == 0
    )
