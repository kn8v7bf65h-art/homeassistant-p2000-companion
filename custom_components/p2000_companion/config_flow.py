"""Config flow for P2000 Companion monitor profiles."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_CITIES,
    CONF_CREATE_FEED_SENSOR,
    CONF_EXCLUDE_WORDS,
    CONF_FEED_URL,
    CONF_MONITOR_NAME,
    CONF_PRIORITIES,
    CONF_SCAN_INTERVAL,
    CONF_SERVICES,
    CONF_TEXT_CONTAINS,
    DEFAULT_CREATE_FEED_SENSOR,
    DEFAULT_FEED_URL,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .parser import csv_to_list, normalize_service


SERVICE_SELECT_OPTIONS: list[SelectOptionDict] = [
    SelectOptionDict(value="ambulance", label="Ambulance"),
    SelectOptionDict(value="fire", label="Brandweer"),
    SelectOptionDict(value="police", label="Politie"),
    SelectOptionDict(value="mmt", label="MMT / Lifeliner"),
    SelectOptionDict(value="lifeboat", label="KNRM / Reddingsdienst"),
]


def _as_csv(value: Any) -> str:
    """Return a comma-separated string for a config value."""
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(item) for item in value if str(item).strip())
    return str(value)


def _schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Build the monitor form schema."""
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_MONITOR_NAME,
                default=defaults.get(CONF_MONITOR_NAME, DEFAULT_NAME),
            ): vol.All(str, vol.Length(min=1, max=80)),
            vol.Required(
                CONF_FEED_URL,
                default=defaults.get(CONF_FEED_URL, DEFAULT_FEED_URL),
            ): str,
            vol.Optional(
                CONF_CITIES,
    CONF_CREATE_FEED_SENSOR,
                default=_as_csv(defaults.get(CONF_CITIES, "")),
            ): str,
            vol.Optional(
                CONF_SERVICES,
                description={
                    "suggested_value": [
                        normalize_service(service)
                        for service in csv_to_list(defaults.get(CONF_SERVICES))
                        if normalize_service(service)
                    ]
                },
            ): SelectSelector(
                SelectSelectorConfig(
                    options=SERVICE_SELECT_OPTIONS,
                    multiple=True,
                    mode=SelectSelectorMode.LIST,
                )
            ),
            vol.Optional(
                CONF_PRIORITIES,
                default=_as_csv(defaults.get(CONF_PRIORITIES, "")),
            ): str,
            vol.Optional(
                CONF_TEXT_CONTAINS,
                default=_as_csv(defaults.get(CONF_TEXT_CONTAINS, "")),
            ): str,
            vol.Optional(
                CONF_EXCLUDE_WORDS,
                default=_as_csv(defaults.get(CONF_EXCLUDE_WORDS, "")),
            ): str,
            vol.Optional(
                CONF_CREATE_FEED_SENSOR,
                default=bool(defaults.get(CONF_CREATE_FEED_SENSOR, DEFAULT_CREATE_FEED_SENSOR)),
            ): bool,
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=int(defaults.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)),
            ): vol.All(vol.Coerce(int), vol.Range(min=30, max=3600)),
        }
    )


def _normalize_input(user_input: dict[str, Any]) -> dict[str, Any]:
    """Normalize form data before storing it."""
    data = dict(user_input)
    data[CONF_MONITOR_NAME] = str(data.get(CONF_MONITOR_NAME, DEFAULT_NAME)).strip()
    data[CONF_FEED_URL] = ", ".join(csv_to_list(data.get(CONF_FEED_URL, DEFAULT_FEED_URL)))
    data[CONF_CITIES] = csv_to_list(data.get(CONF_CITIES))
    data[CONF_SERVICES] = [normalize_service(s) for s in csv_to_list(data.get(CONF_SERVICES))]
    data[CONF_PRIORITIES] = [p.upper().replace(" ", "") for p in csv_to_list(data.get(CONF_PRIORITIES))]
    data[CONF_TEXT_CONTAINS] = [w.lower() for w in csv_to_list(data.get(CONF_TEXT_CONTAINS))]
    data[CONF_EXCLUDE_WORDS] = [w.lower() for w in csv_to_list(data.get(CONF_EXCLUDE_WORDS))]
    data[CONF_CREATE_FEED_SENSOR] = bool(data.get(CONF_CREATE_FEED_SENSOR, DEFAULT_CREATE_FEED_SENSOR))
    data[CONF_SCAN_INTERVAL] = int(data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
    return data


def _valid_urls(value: str) -> bool:
    urls = csv_to_list(value)
    return bool(urls) and all(url.startswith(("http://", "https://")) for url in urls)


class P2000CompanionConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for a P2000 monitor profile."""

    VERSION = 3

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Create a user-defined monitor profile."""
        errors: dict[str, str] = {}

        if user_input is not None:
            data = _normalize_input(user_input)
            if not _valid_urls(data[CONF_FEED_URL]):
                errors[CONF_FEED_URL] = "invalid_url"
            elif not data[CONF_MONITOR_NAME]:
                errors[CONF_MONITOR_NAME] = "name_required"
            else:
                # Multiple monitors may intentionally use the same feed.
                return self.async_create_entry(title=data[CONF_MONITOR_NAME], data=data)

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
    """Edit a P2000 monitor profile."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage monitor options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            data = _normalize_input(user_input)
            if not _valid_urls(data[CONF_FEED_URL]):
                errors[CONF_FEED_URL] = "invalid_url"
            elif not data[CONF_MONITOR_NAME]:
                errors[CONF_MONITOR_NAME] = "name_required"
            else:
                self.hass.config_entries.async_update_entry(
                    self._config_entry,
                    title=data[CONF_MONITOR_NAME],
                )
                return self.async_create_entry(title="", data=data)

        defaults = {**self._config_entry.data, **self._config_entry.options}
        defaults.setdefault(CONF_MONITOR_NAME, self._config_entry.title or DEFAULT_NAME)
        return self.async_show_form(
            step_id="init",
            data_schema=_schema(user_input or defaults),
            errors=errors,
        )
