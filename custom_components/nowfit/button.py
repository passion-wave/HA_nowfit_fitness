"""Rate-limited manual refresh actions."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_CLUB_NAME,
    CONF_ENTRY_TYPE,
    ENTRY_MEMBER,
    ENTRY_PUBLIC,
    REFRESH_COOLDOWN,
)
from .entity import NowFitMemberEntity, NowFitPublicEntity


class RefreshMixin:
    _last_pressed: datetime | None = None

    def _accept_press(self) -> bool:
        now = datetime.now(ZoneInfo("UTC"))
        if self._last_pressed is not None and now - self._last_pressed < REFRESH_COOLDOWN:
            return False
        self._last_pressed = now
        return True


class PublicRefreshButton(RefreshMixin, NowFitPublicEntity, ButtonEntity):
    _attr_name = "Aktualisieren"
    _attr_icon = "mdi:refresh"

    def __init__(self, entry, coordinator) -> None:
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{self.club_id}:refresh"
        slug = entry.data[CONF_CLUB_NAME].casefold().replace("now fit ", "").replace(" ", "_")
        self._attr_suggested_object_id = f"nowfit_{slug}_refresh"

    async def async_press(self) -> None:
        if self._accept_press():
            await self.coordinator.async_request_refresh()


class MemberRefreshButton(RefreshMixin, NowFitMemberEntity, ButtonEntity):
    _attr_name = "Meine Daten aktualisieren"
    _attr_icon = "mdi:refresh"

    def __init__(self, entry, account, history) -> None:
        super().__init__(entry, account)
        self._history = history
        self._attr_unique_id = f"{entry.entry_id}:member:refresh"
        self._attr_suggested_object_id = "nowfit_member_refresh"

    async def async_press(self) -> None:
        if not self._accept_press():
            return
        await self.coordinator.async_request_refresh()
        await self._history.async_request_refresh()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    runtime = entry.runtime_data
    if entry.data[CONF_ENTRY_TYPE] == ENTRY_PUBLIC:
        async_add_entities([PublicRefreshButton(entry, runtime.occupancy_coordinator)])
    elif entry.data[CONF_ENTRY_TYPE] == ENTRY_MEMBER:
        async_add_entities(
            [MemberRefreshButton(entry, runtime.account_coordinator, runtime.history_coordinator)]
        )
