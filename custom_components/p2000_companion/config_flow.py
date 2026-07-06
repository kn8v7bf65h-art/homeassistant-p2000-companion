"""Config flow for P2000 Companion."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    CONF_CITIES,
    CONF_EXCLUDE_WORDS,
    CONF_FEED_URL,
    CONF_PRIORITIES,
    CONF_SCAN_INTERVAL,
    CONF_SERVICES,
    DEFAULT_FEED_URL,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .parser import csv_to_list


def _schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema({
        vol.Required(CONF_FEED_URL, default=defaults.get(CONF_FEED_URL, DEFAULT_FEED_URL)): str,
        vol.Optional(CONF_CITIES, default=", ".join(defaults.get(CONF_CITIES, []))): str,
        vol.Optional(CONF_SERVICES, default=", ".join(defaults.get(CONF_SERVICES, []))): str,
        vol.Optional(CONF_PRIORITIES, default=", ".join(defaults.get(CONF_PRIORITIES, []))): str,
        vol.Optional(CONF_EXCLUDE_WORDS, default=", ".join(defaults.get(CONF_EXCLUDE_WORDS, []))): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=defaults.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)): vol.All(int, vol.Range(min=30, max=3600)),
    })


def _normalize_input(user_input: dict[str, Any]) -> dict[str, Any]:
    data = dict(user_input)
    data[CONF_CITIES] = csv_to_list(data.get(CONF_CITIES))
    data[CONF_SERVICES] = [s.lower() for s in csv_to_list(data.get(CONF_SERVICES))]
    data[CONF_PRIORITIES] = [p.upper().replace(" ", "") for p in csv_to_list(data.get(CONF_PRIORITIES))]
    data[CONF_EXCLUDE_WORDS] = [w.lower() for w in csv_to_list(data.get(CONF_EXCLUDE_WORDS))]
    return data


class P2000ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            data = _normalize_input(user_input)
            await self.async_set_unique_id(data[CONF_FEED_URL])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=DEFAULT_NAME, data=data)

        return self.async_show_form(step_id="user", data_schema=_schema())

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return P2000OptionsFlow(config_entry)


class P2000OptionsFlow(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=_normalize_input(user_input))

        defaults = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(step_id="init", data_schema=_schema(defaults))
