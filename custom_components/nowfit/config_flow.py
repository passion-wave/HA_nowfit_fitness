"""Config and reauthentication flows for NowFit."""

from __future__ import annotations

from datetime import datetime
from hashlib import sha256
from typing import Any
from zoneinfo import ZoneInfo

import voluptuous as vol
from aiohttp import CookieJar
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession, async_get_clientsession

from .client import MemberClient, PublicClient
from .const import (
    CONF_CLUB_ID,
    CONF_CLUB_NAME,
    CONF_DISPLAY_NAME,
    CONF_EMAIL,
    CONF_ENTRY_TYPE,
    CONF_PASSWORD,
    CONF_STORE_PASSWORD,
    DOMAIN,
    ENTRY_MEMBER,
    ENTRY_PUBLIC,
)
from .cookie_store import export_cookies
from .exceptions import CannotConnect, InvalidCredentials, NowFitError, UnsupportedLogin
from .flow_helpers import club_selector_options
from .options_flow import NowFitOptionsFlow


class NowFitConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry):
        return NowFitOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        return self.async_show_menu(step_id="user", menu_options=[ENTRY_PUBLIC, ENTRY_MEMBER])

    async def async_step_public(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        client = PublicClient(async_get_clientsession(self.hass))
        try:
            clubs = await client.async_get_clubs()
        except CannotConnect:
            return self.async_abort(reason="cannot_connect")
        except NowFitError:
            return self.async_abort(reason="unexpected_response")
        clubs_by_id = {club.club_id: club.name for club in clubs}
        if user_input is not None:
            club_id = user_input[CONF_CLUB_ID]
            club_name = clubs_by_id[club_id]
            await self.async_set_unique_id(f"public:{club_id}")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=club_name,
                data={
                    CONF_ENTRY_TYPE: ENTRY_PUBLIC,
                    CONF_CLUB_ID: club_id,
                    CONF_CLUB_NAME: club_name,
                },
            )
        schema = vol.Schema(
            {
                vol.Required(CONF_CLUB_ID): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=club_selector_options(clubs),
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )
        return self.async_show_form(step_id="public", data_schema=schema, errors=errors)

    async def async_step_member(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            jar = CookieJar(unsafe=False)
            client = MemberClient(async_create_clientsession(self.hass, cookie_jar=jar))
            email = str(user_input[CONF_EMAIL]).strip()
            try:
                await client.async_login(
                    email,
                    str(user_input[CONF_PASSWORD]),
                    bool(user_input[CONF_STORE_PASSWORD]),
                )
            except InvalidCredentials:
                errors["base"] = "invalid_auth"
            except UnsupportedLogin:
                errors["base"] = "unsupported_login"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except NowFitError:
                errors["base"] = "unexpected_response"
            else:
                identity = sha256(email.casefold().encode()).hexdigest()[:24]
                await self.async_set_unique_id(f"member:{identity}")
                self._abort_if_unique_id_configured()
                data = {
                    CONF_ENTRY_TYPE: ENTRY_MEMBER,
                    CONF_EMAIL: email,
                    CONF_STORE_PASSWORD: bool(user_input[CONF_STORE_PASSWORD]),
                    CONF_DISPLAY_NAME: user_input.get(CONF_DISPLAY_NAME, ""),
                }
                if user_input[CONF_STORE_PASSWORD]:
                    data[CONF_PASSWORD] = str(user_input[CONF_PASSWORD])
                self.hass.data.setdefault(DOMAIN, {}).setdefault("pending_sessions", {})[
                    self.unique_id
                ] = export_cookies(jar, datetime.now(ZoneInfo("UTC")))
                return self.async_create_entry(
                    title=str(user_input.get(CONF_DISPLAY_NAME) or "Mein Training"),
                    data=data,
                )
        schema = vol.Schema(
            {
                vol.Required(CONF_EMAIL): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.EMAIL)
                ),
                vol.Required(CONF_PASSWORD): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                ),
                vol.Required(CONF_STORE_PASSWORD, default=False): selector.BooleanSelector(),
                vol.Optional(CONF_DISPLAY_NAME, default="Mein Training"): selector.TextSelector(),
            }
        )
        return self.async_show_form(step_id="member", data_schema=schema, errors=errors)

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        self._reauth_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        entry = self._reauth_entry
        if user_input is not None:
            client = MemberClient(async_create_clientsession(self.hass, cookie_jar=CookieJar()))
            try:
                await client.async_login(
                    entry.data[CONF_EMAIL],
                    str(user_input[CONF_PASSWORD]),
                    bool(entry.data.get(CONF_STORE_PASSWORD)),
                )
            except InvalidCredentials:
                errors["base"] = "invalid_auth"
            except NowFitError:
                errors["base"] = "cannot_connect"
            else:
                updated = dict(entry.data)
                if updated.get(CONF_STORE_PASSWORD):
                    updated[CONF_PASSWORD] = str(user_input[CONF_PASSWORD])
                return self.async_update_reload_and_abort(entry, data=updated)
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PASSWORD): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                    )
                }
            ),
            errors=errors,
        )
