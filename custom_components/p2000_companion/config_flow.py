"""Config flow for P2000 Companion."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

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
from .parser import csv_to_list, normalize_service


def _as_csv(value: Any) -> str:
    """Return a comma separated string for a config value."""
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(item) for item in value if str(item).strip())
    return str(value)


def _schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Build the form schema."""
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_FEED_URL,
                default=defaults.get(CONF_FEED_URL, DEFAULT_FEED_URL),
            ): str,
            vol.Optional(
                CONF_CITIES,
                default=_as_csv(defaults.get(CONF_CITIES, "")),
            ): str,
            vol.Optional(
                CONF_SERVICES,
                default=_as_csv(defaults.get(CONF_SERVICES, "")),
            ): str,
            vol.Optional(
                CONF_PRIORITIES,
                default=_as_csv(defaults.get(CONF_PRIORITIES, "")),
            ): str,
            vol.Optional(
                CONF_EXCLUDE_WORDS,
                default=_as_csv(defaults.get(CONF_EXCLUDE_WORDS, "")),
            ): str,
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=int(defaults.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)),
            ): vol.All(vol.Coerce(int), vol.Range(min=30, max=3600)),
        }
    )


def _normalize_input(user_input: dict[str, Any]) -> dict[str, Any]:
    """Normalize form data before storing it."""
    data = dict(user_input)
    data[CONF_FEED_URL] = str(data.get(CONF_FEED_URL, DEFAULT_FEED_URL)).strip()
    data[CONF_CITIES] = csv_to_list(data.get(CONF_CITIES))
    data[CONF_SERVICES] = [normalize_service(s) for s in csv_to_list(data.get(CONF_SERVICES))]
    data[CONF_PRIORITIES] = [p.upper().replace(" ", "") for p in csv_to_list(data.get(CONF_PRIORITIES))]
    data[CONF_EXCLUDE_WORDS] = [w.lower() for w in csv_to_list(data.get(CONF_EXCLUDE_WORDS))]
    data[CONF_SCAN_INTERVAL] = int(data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
    return data


class P2000CompanionConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for P2000 Companion."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            data = _normalize_input(user_input)
            if not data[CONF_FEED_URL].startswith(("http://", "https://")):
                errors[CONF_FEED_URL] = "invalid_url"
            else:
                await self.async_set_unique_id(data[CONF_FEED_URL])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=DEFAULT_NAME, data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(user_input),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return P2000CompanionOptionsFlow(config_entry)


class P2000CompanionOptionsFlow(config_entries.OptionsFlow):
    """Handle options for P2000 Companion."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            data = _normalize_input(user_input)
            if not data[CONF_FEED_URL].startswith(("http://", "https://")):
                errors[CONF_FEED_URL] = "invalid_url"
            else:
                return self.async_create_entry(title="", data=data)

        defaults = {**self._config_entry.data, **self._config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=_schema(user_input or defaults),
            errors=errors,
        )
