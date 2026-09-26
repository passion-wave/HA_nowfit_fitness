"""NowFit integration setup."""

from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from aiohttp import CookieJar
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_create_clientsession, async_get_clientsession

from .auth import SessionManager
from .client import MemberClient, PublicClient
from .const import (
    CONF_EMAIL,
    CONF_ENTRY_TYPE,
    CONF_MIN_DURATION,
    CONF_PASSWORD,
    CONF_STORE_PASSWORD,
    CONF_TIME_ZONE,
    DOMAIN,
    ENTRY_MEMBER,
    ENTRY_PUBLIC,
    SOURCE_TIME_ZONE,
)
from .cookie_store import NowFitCookieStore, restore_cookies
from .coordinator import AccountCoordinator, HistoryCoordinator, OccupancyCoordinator
from .exceptions import InvalidCredentials, NowFitError, SessionExpired
from .flow_helpers import safe_error_code
from .models import NowFitRuntimeData

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    kind = entry.data[CONF_ENTRY_TYPE]
    if kind == ENTRY_PUBLIC:
        client = PublicClient(async_get_clientsession(hass))
        occupancy = OccupancyCoordinator(hass, entry, client)
        try:
            await occupancy.async_config_entry_first_refresh()
        except Exception as err:
            raise ConfigEntryNotReady from err
        entry.runtime_data = NowFitRuntimeData(entry_type=kind, occupancy_coordinator=occupancy)
    elif kind == ENTRY_MEMBER:
        jar = CookieJar(unsafe=False)
        session = async_create_clientsession(hass, cookie_jar=jar)
        client = MemberClient(session)
        password = entry.data.get(CONF_PASSWORD)
        store = NowFitCookieStore(hass, entry.entry_id)
        auth = SessionManager(
            client,
            entry.data[CONF_EMAIL],
            password,
            bool(entry.data.get(CONF_STORE_PASSWORD)),
            claim_relogin=lambda: store.async_claim_relogin(datetime.now(ZoneInfo("UTC"))),
            relogin_succeeded=store.async_clear_relogin_guard,
        )
        await store.async_load_into(jar, datetime.now(ZoneInfo("UTC")))
        pending = (
            hass.data.setdefault(DOMAIN, {})
            .setdefault("pending_sessions", {})
            .pop(entry.unique_id, None)
        )
        if pending:
            restore_cookies(jar, pending, datetime.now(ZoneInfo("UTC")))
            await store.async_save_from(jar, datetime.now(ZoneInfo("UTC")))
        client.set_success_callback(
            lambda: store.async_save_if_changed(jar, datetime.now(ZoneInfo("UTC")))
        )
        account = AccountCoordinator(hass, entry, client, auth)
        history = HistoryCoordinator(
            hass,
            entry,
            client,
            auth,
            int(entry.options.get(CONF_MIN_DURATION, 1)),
            str(entry.options.get(CONF_TIME_ZONE, SOURCE_TIME_ZONE)),
        )
        try:
            await account.async_config_entry_first_refresh()
            await history.async_config_entry_first_refresh()
        except (SessionExpired, InvalidCredentials) as err:
            raise ConfigEntryAuthFailed from err
        except NowFitError as err:
            message = f"{type(err).__name__}:{safe_error_code(err)}"
            _LOGGER.warning("Member setup temporarily unavailable: %s", message)
            raise ConfigEntryNotReady(message) from err
        entry.runtime_data = NowFitRuntimeData(
            entry_type=kind,
            account_coordinator=account,
            history_coordinator=history,
            auth_manager=auth,
            extra={"cookie_store": store, "cookie_jar": jar},
        )
    else:
        return False
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if entry.version > 1:
        return False
    return True
