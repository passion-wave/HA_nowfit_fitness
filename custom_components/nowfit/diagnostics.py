"""Privacy-preserving diagnostics for NowFit."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, ENTRY_MEMBER, VERSION

PARSER_VERSION = 1


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, object]:
    """Build diagnostics from a positive list; never collect raw entry data."""
    runtime = entry.runtime_data
    result: dict[str, object] = {
        "integration_version": VERSION,
        "home_assistant_version": hass.config.version,
        "entry_type": runtime.entry_type,
        "parser_version": PARSER_VERSION,
        "platforms": ["sensor", "binary_sensor", "button"],
    }
    if runtime.entry_type == ENTRY_MEMBER:
        account = runtime.account_coordinator
        history = runtime.history_coordinator
        result["account_source_ok"] = account.last_update_success
        result["history_source_ok"] = history.last_update_success
        if history.data is not None:
            result["history"] = {
                "row_count": history.data.raw_row_count,
                "duplicate_count": history.data.collapsed_duplicate_count,
                "rejected_count": history.data.rejected_row_count,
                "coverage": history.data.coverage.value,
            }
    else:
        public = runtime.occupancy_coordinator
        result["public_source_ok"] = public.last_update_success
        result["club_count"] = len(public.data.clubs) if public.data else 0
    return {DOMAIN: result}
