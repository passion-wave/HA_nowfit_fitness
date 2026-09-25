"""NowFit sensor entities."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_time_change

from .const import (
    CONF_CLUB_NAME,
    CONF_TIME_ZONE,
    ENTRY_MEMBER,
    ENTRY_PUBLIC,
    SOURCE_TIME_ZONE,
)
from .entity import NowFitMemberEntity, NowFitPublicEntity
from .models import AccountSnapshot, HistorySnapshot
from .training import derive_history


class OccupancySensor(NowFitPublicEntity, SensorEntity):
    _attr_name = "Auslastung"
    _attr_icon = "mdi:dumbbell"
    _attr_native_unit_of_measurement = "Personen"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, entry, coordinator) -> None:
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{self.club_id}:occupancy"
        slug = entry.data[CONF_CLUB_NAME].casefold().replace("now fit ", "").replace(" ", "_")
        self._attr_suggested_object_id = f"nowfit_{slug}_auslastung"

    @property
    def native_value(self) -> int | None:
        club = self.coordinator.data.club(self.club_id) if self.coordinator.data else None
        return club.checked_in if club else None

    @property
    def available(self) -> bool:
        return super().available and self.native_value is not None


class PublicLastSuccessSensor(NowFitPublicEntity, SensorEntity):
    _attr_name = "Letzter erfolgreicher Abruf"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:clock-check-outline"

    def __init__(self, entry, coordinator) -> None:
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{self.club_id}:last_success"
        slug = entry.data[CONF_CLUB_NAME].casefold().replace("now fit ", "").replace(" ", "_")
        self._attr_suggested_object_id = f"nowfit_{slug}_last_success"

    @property
    def native_value(self) -> datetime | None:
        return self.coordinator.last_success_at


class PublicStatusSensor(NowFitPublicEntity, SensorEntity):
    _attr_name = "Quellstatus"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["ready", "temporary_error", "rate_limited", "parse_error"]
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:cloud-check-outline"

    def __init__(self, entry, coordinator) -> None:
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{self.club_id}:source_status"
        slug = entry.data[CONF_CLUB_NAME].casefold().replace("now fit ", "").replace(" ", "_")
        self._attr_suggested_object_id = f"nowfit_{slug}_source_status"

    @property
    def native_value(self) -> str:
        return self.coordinator.source_status.value


@dataclass(frozen=True, kw_only=True)
class AccountDescription:
    key: str
    name: str
    value_fn: Callable[[AccountSnapshot], Any]
    icon: str
    unit: str | None = None
    device_class: SensorDeviceClass | None = None


ACCOUNT_SENSORS = (
    AccountDescription(
        key="checkins_week",
        name="Check-ins aktuelle Woche",
        value_fn=lambda x: x.checkins_week,
        icon="mdi:calendar-week",
    ),
    AccountDescription(
        key="checkins_month",
        name="Check-ins aktueller Monat",
        value_fn=lambda x: x.checkins_month,
        icon="mdi:calendar-month",
    ),
    AccountDescription(
        key="average_training_duration",
        name="Durchschnittliche Besuchsdauer",
        value_fn=lambda x: x.average_visit_minutes,
        icon="mdi:timer-outline",
        unit=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
    ),
    AccountDescription(
        key="week_goal_current",
        name="Wochenziel Stand",
        value_fn=lambda x: x.week_goal_current,
        icon="mdi:target",
    ),
    AccountDescription(
        key="week_goal_target",
        name="Wochenziel",
        value_fn=lambda x: x.week_goal_target,
        icon="mdi:target",
    ),
    AccountDescription(
        key="week_goal_percent",
        name="Wochenziel Erreichung",
        value_fn=lambda x: (
            round(x.week_goal_current / x.week_goal_target * 100, 1)
            if x.week_goal_current is not None and x.week_goal_target
            else None
        ),
        icon="mdi:percent",
        unit="%",
    ),
    AccountDescription(
        key="week_goal_display_percent",
        name="Wochenziel Anzeige",
        value_fn=lambda x: (
            min(max(round(x.week_goal_current / x.week_goal_target * 100, 1), 0), 100)
            if x.week_goal_current is not None and x.week_goal_target
            else None
        ),
        icon="mdi:gauge",
        unit="%",
    ),
    AccountDescription(
        key="week_remaining",
        name="Bis zum Wochenziel",
        value_fn=lambda x: (
            max(x.week_goal_target - x.week_goal_current, 0)
            if x.week_goal_current is not None and x.week_goal_target is not None
            else None
        ),
        icon="mdi:counter",
    ),
    AccountDescription(
        key="month_goal_current",
        name="Monatsziel Stand",
        value_fn=lambda x: x.month_goal_current,
        icon="mdi:target",
    ),
    AccountDescription(
        key="month_goal_target",
        name="Monatsziel",
        value_fn=lambda x: x.month_goal_target,
        icon="mdi:target",
    ),
    AccountDescription(
        key="month_goal_percent",
        name="Monatsziel Erreichung",
        value_fn=lambda x: (
            round(x.month_goal_current / x.month_goal_target * 100, 1)
            if x.month_goal_current is not None and x.month_goal_target
            else None
        ),
        icon="mdi:percent",
        unit="%",
    ),
    AccountDescription(
        key="month_goal_display_percent",
        name="Monatsziel Anzeige",
        value_fn=lambda x: (
            min(max(round(x.month_goal_current / x.month_goal_target * 100, 1), 0), 100)
            if x.month_goal_current is not None and x.month_goal_target
            else None
        ),
        icon="mdi:gauge",
        unit="%",
    ),
    AccountDescription(
        key="month_remaining",
        name="Bis zum Monatsziel",
        value_fn=lambda x: (
            max(x.month_goal_target - x.month_goal_current, 0)
            if x.month_goal_current is not None and x.month_goal_target is not None
            else None
        ),
        icon="mdi:counter",
    ),
)


class AccountSensor(NowFitMemberEntity, SensorEntity):
    def __init__(self, entry, coordinator, description: AccountDescription) -> None:
        super().__init__(entry, coordinator)
        self.description = description
        self._attr_unique_id = f"{entry.entry_id}:account:{description.key}"
        self._attr_suggested_object_id = f"nowfit_{description.key}"
        self._attr_name = description.name
        self._attr_icon = description.icon
        self._attr_native_unit_of_measurement = description.unit
        self._attr_device_class = description.device_class

    @property
    def native_value(self):
        return self.description.value_fn(self.coordinator.data) if self.coordinator.data else None


class AccountLastSuccessSensor(NowFitMemberEntity, SensorEntity):
    _attr_name = "Account letzter erfolgreicher Abruf"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry, coordinator) -> None:
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{entry.entry_id}:account:last_success"
        self._attr_suggested_object_id = "nowfit_account_last_success"

    @property
    def native_value(self):
        return self.coordinator.last_success_at


class MemberDiagnosticSensor(NowFitMemberEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry, account, history, key: str, name: str) -> None:
        super().__init__(entry, account)
        self._history = history
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}:diagnostic:{key}"
        self._attr_suggested_object_id = f"nowfit_{key}"
        if key == "auth_status":
            self._attr_device_class = SensorDeviceClass.ENUM
            self._attr_options = ["ready", "auth_required", "temporary_error"]
        elif key == "next_retry":
            self._attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self):
        if self._key == "auth_status":
            statuses = {self.coordinator.source_status, self._history.source_status}
            if any(status.value == "auth_required" for status in statuses):
                return "auth_required"
            if all(status.value == "ready" for status in statuses):
                return "ready"
            return "temporary_error"
        if self._key == "next_retry":
            retries = [self.coordinator.next_retry, self._history.next_retry]
            return min((retry for retry in retries if retry is not None), default=None)
        errors = [self.coordinator.last_error, self._history.last_error]
        return next((error for error in errors if error), None)


class HistorySensor(NowFitMemberEntity, SensorEntity):
    def __init__(self, entry, coordinator, key: str, name: str, icon: str) -> None:
        super().__init__(entry, coordinator)
        self.key = key
        self._attr_unique_id = f"{entry.entry_id}:history:{key}"
        self._attr_suggested_object_id = f"nowfit_{key}"
        self._attr_name = name
        self._attr_icon = icon
        if key in {"last_training_start", "last_training_end", "history_last_success"}:
            self._attr_device_class = SensorDeviceClass.TIMESTAMP
        if key == "last_training_duration":
            self._attr_device_class = SensorDeviceClass.DURATION
            self._attr_native_unit_of_measurement = UnitOfTime.MINUTES

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            async_track_time_change(self.hass, self._midnight, hour=0, minute=0, second=5)
        )

    @callback
    def _midnight(self, _now) -> None:
        self.async_write_ha_state()

    @property
    def native_value(self):
        data: HistorySnapshot | None = self.coordinator.data
        if data is None:
            return None
        if self.key == "history_last_success":
            return self.coordinator.last_success_at
        derived = derive_history(
            data,
            datetime.now(ZoneInfo("UTC")),
            ZoneInfo(str(self.entry.options.get(CONF_TIME_ZONE, SOURCE_TIME_ZONE))),
        )
        last = derived.last_visit
        return {
            "last_training_start": last.started_at if last else None,
            "last_training_end": last.ended_at if last else None,
            "last_training_duration": last.duration_minutes if last else None,
            "last_training_studio": last.studio if last else None,
            "trainings_this_week": derived.trainings_this_week,
            "trainings_this_month": derived.trainings_this_month,
            "days_since_last_training": derived.days_since_last_training,
            "history_coverage": data.coverage.value,
        }.get(self.key)


HISTORY_SENSORS = (
    ("last_training_start", "Letzter Besuch Start", "mdi:clock-start"),
    ("last_training_end", "Letzter Besuch Ende", "mdi:clock-end"),
    ("last_training_duration", "Letzte Besuchsdauer", "mdi:timer-outline"),
    ("last_training_studio", "Letztes Studio", "mdi:map-marker"),
    ("trainings_this_week", "Besuche diese Woche im verfügbaren Verlauf", "mdi:calendar-week"),
    ("trainings_this_month", "Besuche diesen Monat im verfügbaren Verlauf", "mdi:calendar-month"),
    ("days_since_last_training", "Tage seit letztem Besuch", "mdi:calendar-clock"),
    ("history_coverage", "Historienabdeckung", "mdi:database-eye-outline"),
    ("history_last_success", "Historie letzter erfolgreicher Abruf", "mdi:clock-check-outline"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    runtime = entry.runtime_data
    if runtime.entry_type == ENTRY_PUBLIC:
        c = runtime.occupancy_coordinator
        async_add_entities(
            [
                OccupancySensor(entry, c),
                PublicLastSuccessSensor(entry, c),
                PublicStatusSensor(entry, c),
            ]
        )
    elif runtime.entry_type == ENTRY_MEMBER:
        account = runtime.account_coordinator
        history = runtime.history_coordinator
        entities = [AccountSensor(entry, account, description) for description in ACCOUNT_SENSORS]
        entities.append(AccountLastSuccessSensor(entry, account))
        entities.extend(
            [
                MemberDiagnosticSensor(entry, account, history, "auth_status", "Anmeldestatus"),
                MemberDiagnosticSensor(entry, account, history, "last_error", "Letzter Fehler"),
                MemberDiagnosticSensor(entry, account, history, "next_retry", "Nächster Versuch"),
            ]
        )
        entities.extend(
            HistorySensor(entry, history, *description) for description in HISTORY_SENSORS
        )
        async_add_entities(entities)
