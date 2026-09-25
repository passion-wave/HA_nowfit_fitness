"""NowFit history binary sensors."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_time_change

from .const import CONF_ENTRY_TYPE, CONF_TIME_ZONE, ENTRY_MEMBER, SOURCE_TIME_ZONE
from .entity import NowFitMemberEntity
from .training import derive_history


class TrainedOnDayBinarySensor(NowFitMemberEntity, BinarySensorEntity):
    """Expose a visit only when the source can support the assertion."""

    def __init__(self, entry, coordinator, key: str, name: str) -> None:
        super().__init__(entry, coordinator)
        self._key = key
        self._attr_unique_id = f"{entry.entry_id}:history:{key}"
        self._attr_suggested_object_id = f"nowfit_{key}"
        self._attr_name = name
        self._attr_icon = "mdi:calendar-check"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            async_track_time_change(self.hass, self._midnight, hour=0, minute=0, second=5)
        )

    @callback
    def _midnight(self, _now) -> None:
        self.async_write_ha_state()

    def _value(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        derived = derive_history(
            self.coordinator.data,
            datetime.now(ZoneInfo("UTC")),
            ZoneInfo(str(self.entry.options.get(CONF_TIME_ZONE, SOURCE_TIME_ZONE))),
        )
        return getattr(derived, self._key)

    @property
    def is_on(self) -> bool | None:
        return self._value()

    @property
    def available(self) -> bool:
        return super().available and self._value() is not None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    if entry.data[CONF_ENTRY_TYPE] != ENTRY_MEMBER:
        return
    coordinator = entry.runtime_data.history_coordinator
    async_add_entities(
        [
            TrainedOnDayBinarySensor(entry, coordinator, "trained_today", "Heute trainiert"),
            TrainedOnDayBinarySensor(entry, coordinator, "trained_yesterday", "Gestern trainiert"),
        ]
    )
