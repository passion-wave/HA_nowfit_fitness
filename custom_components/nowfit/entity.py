"""Shared entity classes."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_CLUB_ID, CONF_CLUB_NAME, DOMAIN, VERSION


class NowFitPublicEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, entry, coordinator) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self.club_id = entry.data[CONF_CLUB_ID]
        self.club_name = entry.data[CONF_CLUB_NAME]

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, f"club:{self.club_id}")},
            name=self.club_name,
            manufacturer="NowFit",
            model="Memberarea Club",
            sw_version=VERSION,
            configuration_url="https://nowfit.memberarea.club/CheckinCounter/GetClubsCheckinCounterPage",
        )


class NowFitMemberEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, entry, coordinator) -> None:
        super().__init__(coordinator)
        self.entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, f"member:{self.entry.entry_id}")},
            name=self.entry.title,
            manufacturer="NowFit",
            model="Memberarea Account",
            sw_version=VERSION,
            configuration_url="https://nowfit.memberarea.club/Person/MyAccount",
        )
