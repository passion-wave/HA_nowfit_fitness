"""Options flow for safe user-tunable settings."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_ENTRY_TYPE,
    CONF_MIN_DURATION,
    CONF_PASSWORD,
    CONF_STORE_PASSWORD,
    CONF_TIME_ZONE,
    ENTRY_MEMBER,
    SOURCE_TIME_ZONE,
)


class NowFitOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if self.config_entry.data[CONF_ENTRY_TYPE] != ENTRY_MEMBER:
            return self.async_abort(reason="no_public_options")
        if user_input is not None:
            updated = dict(self.config_entry.data)
            updated[CONF_STORE_PASSWORD] = bool(user_input[CONF_STORE_PASSWORD])
            if not updated[CONF_STORE_PASSWORD]:
                updated.pop(CONF_PASSWORD, None)
            self.hass.config_entries.async_update_entry(self.config_entry, data=updated)
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_MIN_DURATION,
                        default=self.config_entry.options.get(CONF_MIN_DURATION, 1),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=1, max=120, step=1, mode="box")
                    ),
                    vol.Required(
                        CONF_TIME_ZONE,
                        default=self.config_entry.options.get(CONF_TIME_ZONE, SOURCE_TIME_ZONE),
                    ): selector.TextSelector(),
                    vol.Required(
                        CONF_STORE_PASSWORD,
                        default=self.config_entry.data.get(CONF_STORE_PASSWORD, False),
                    ): selector.BooleanSelector(),
                }
            ),
        )
