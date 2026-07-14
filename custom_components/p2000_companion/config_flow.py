"""Config flow for P2000 Companion monitor profiles."""
from __future__ import annotations

import logging
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
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_CITIES,
    CONF_CREATE_FEED_SENSOR,
    CONF_EXCLUDE_WORDS,
    CONF_FEED_URL,
    CONF_MONITOR_NAME,
    CONF_PRIORITIES,
    CONF_PROVIDER,
    CONF_SCAN_INTERVAL,
    CONF_SERVICES,
    CONF_TELEGRAM_API_HASH,
    CONF_TELEGRAM_API_ID,
    CONF_TELEGRAM_CHAT,
    CONF_TELEGRAM_CODE,
    CONF_TELEGRAM_PASSWORD,
    CONF_TELEGRAM_PHONE,
    CONF_TELEGRAM_SESSION,
    CONF_TEXT_CONTAINS,
    DEFAULT_CREATE_FEED_SENSOR,
    DEFAULT_FEED_URL,
    DEFAULT_NAME,
    DEFAULT_PROVIDER,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PROVIDER_RSS,
    PROVIDER_TELEGRAM,
)
from .parser import csv_to_list, normalize_service

_LOGGER = logging.getLogger(__name__)

SERVICE_SELECT_OPTIONS: list[SelectOptionDict] = [
    SelectOptionDict(value="ambulance", label="Ambulance"),
    SelectOptionDict(value="fire", label="Brandweer"),
    SelectOptionDict(value="police", label="Politie"),
    SelectOptionDict(value="mmt", label="MMT / Lifeliner"),
    SelectOptionDict(value="lifeboat", label="KNRM / Reddingsdienst"),
]

PROVIDER_OPTIONS: list[SelectOptionDict] = [
    SelectOptionDict(value=PROVIDER_RSS, label="RSS-feed"),
    SelectOptionDict(value=PROVIDER_TELEGRAM, label="Telegram via Telethon"),
]


def _as_csv(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(item) for item in value if str(item).strip())
    return str(value)


def _services_default(defaults: dict[str, Any]) -> list[str]:
    return [
        normalize_service(service)
        for service in csv_to_list(defaults.get(CONF_SERVICES))
        if normalize_service(service)
    ]


def _filter_schema(defaults: dict[str, Any] | None = None) -> dict[Any, Any]:
    defaults = defaults or {}
    return {
        vol.Optional(CONF_CITIES, default=_as_csv(defaults.get(CONF_CITIES, ""))): str,
        vol.Optional(
            CONF_SERVICES,
            default=_services_default(defaults),
        ): SelectSelector(
            SelectSelectorConfig(
                options=SERVICE_SELECT_OPTIONS,
                multiple=True,
                mode=SelectSelectorMode.LIST,
            )
        ),
        vol.Optional(CONF_PRIORITIES, default=_as_csv(defaults.get(CONF_PRIORITIES, ""))): str,
        vol.Optional(CONF_TEXT_CONTAINS, default=_as_csv(defaults.get(CONF_TEXT_CONTAINS, ""))): str,
        vol.Optional(CONF_EXCLUDE_WORDS, default=_as_csv(defaults.get(CONF_EXCLUDE_WORDS, ""))): str,
    }


def _rss_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    fields: dict[Any, Any] = {
        vol.Required(CONF_MONITOR_NAME, default=defaults.get(CONF_MONITOR_NAME, DEFAULT_NAME)): vol.All(str, vol.Length(min=1, max=80)),
        vol.Required(CONF_FEED_URL, default=defaults.get(CONF_FEED_URL, DEFAULT_FEED_URL)): str,
        **_filter_schema(defaults),
        vol.Optional(CONF_CREATE_FEED_SENSOR, default=bool(defaults.get(CONF_CREATE_FEED_SENSOR, DEFAULT_CREATE_FEED_SENSOR))): bool,
        vol.Optional(CONF_SCAN_INTERVAL, default=int(defaults.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))): vol.All(vol.Coerce(int), vol.Range(min=30, max=3600)),
    }
    return vol.Schema(fields)


def _telegram_schema(defaults: dict[str, Any] | None = None, *, include_credentials: bool = True) -> vol.Schema:
    defaults = defaults or {}
    fields: dict[Any, Any] = {
        vol.Required(CONF_MONITOR_NAME, default=defaults.get(CONF_MONITOR_NAME, DEFAULT_NAME)): vol.All(str, vol.Length(min=1, max=80)),
    }
    if include_credentials:
        fields.update(
            {
                vol.Required(CONF_TELEGRAM_API_ID, default=defaults.get(CONF_TELEGRAM_API_ID, "")): vol.Coerce(int),
                vol.Required(CONF_TELEGRAM_API_HASH, default=defaults.get(CONF_TELEGRAM_API_HASH, "")): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
                vol.Required(CONF_TELEGRAM_PHONE, default=defaults.get(CONF_TELEGRAM_PHONE, "")): str,
            }
        )
    fields[vol.Required(CONF_TELEGRAM_CHAT, default=defaults.get(CONF_TELEGRAM_CHAT, ""))] = str
    fields.update(_filter_schema(defaults))
    return vol.Schema(fields)


def _normalize_filters(data: dict[str, Any]) -> dict[str, Any]:
    data[CONF_MONITOR_NAME] = str(data.get(CONF_MONITOR_NAME, DEFAULT_NAME)).strip()
    data[CONF_CITIES] = csv_to_list(data.get(CONF_CITIES))
    data[CONF_SERVICES] = [normalize_service(s) for s in csv_to_list(data.get(CONF_SERVICES))]
    data[CONF_PRIORITIES] = [p.upper().replace(" ", "") for p in csv_to_list(data.get(CONF_PRIORITIES))]
    data[CONF_TEXT_CONTAINS] = [w.lower() for w in csv_to_list(data.get(CONF_TEXT_CONTAINS))]
    data[CONF_EXCLUDE_WORDS] = [w.lower() for w in csv_to_list(data.get(CONF_EXCLUDE_WORDS))]
    return data


def _normalize_rss_input(user_input: dict[str, Any]) -> dict[str, Any]:
    data = _normalize_filters(dict(user_input))
    data[CONF_PROVIDER] = PROVIDER_RSS
    data[CONF_FEED_URL] = ", ".join(csv_to_list(data.get(CONF_FEED_URL, DEFAULT_FEED_URL)))
    data[CONF_CREATE_FEED_SENSOR] = bool(data.get(CONF_CREATE_FEED_SENSOR, DEFAULT_CREATE_FEED_SENSOR))
    data[CONF_SCAN_INTERVAL] = int(data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
    return data


def _normalize_telegram_input(user_input: dict[str, Any]) -> dict[str, Any]:
    data = _normalize_filters(dict(user_input))
    data[CONF_PROVIDER] = PROVIDER_TELEGRAM
    data[CONF_TELEGRAM_API_ID] = int(data[CONF_TELEGRAM_API_ID])
    data[CONF_TELEGRAM_API_HASH] = str(data[CONF_TELEGRAM_API_HASH]).strip()
    data[CONF_TELEGRAM_PHONE] = str(data[CONF_TELEGRAM_PHONE]).strip()
    data[CONF_TELEGRAM_CHAT] = str(data[CONF_TELEGRAM_CHAT]).strip()
    data[CONF_CREATE_FEED_SENSOR] = False
    return data


def _valid_urls(value: str) -> bool:
    urls = csv_to_list(value)
    return bool(urls) and all(url.startswith(("http://", "https://")) for url in urls)


class P2000CompanionConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for P2000 Companion."""

    VERSION = 4

    def __init__(self) -> None:
        self._provider = DEFAULT_PROVIDER
        self._pending: dict[str, Any] = {}
        self._telegram_client = None
        self._phone_code_hash: str | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            self._provider = user_input[CONF_PROVIDER]
            return await self.async_step_rss() if self._provider == PROVIDER_RSS else await self.async_step_telegram()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PROVIDER, default=DEFAULT_PROVIDER): SelectSelector(
                        SelectSelectorConfig(options=PROVIDER_OPTIONS, mode=SelectSelectorMode.LIST)
                    )
                }
            ),
        )

    async def async_step_rss(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            data = _normalize_rss_input(user_input)
            if not _valid_urls(data[CONF_FEED_URL]):
                errors[CONF_FEED_URL] = "invalid_url"
            else:
                return self.async_create_entry(title=data[CONF_MONITOR_NAME], data=data)
        return self.async_show_form(step_id="rss", data_schema=_rss_schema(user_input), errors=errors)

    async def async_step_telegram(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            data = _normalize_telegram_input(user_input)
            try:
                from telethon import TelegramClient
                from telethon.errors import FloodWaitError, PhoneNumberInvalidError
                from telethon.sessions import StringSession

                client = TelegramClient(StringSession(), data[CONF_TELEGRAM_API_ID], data[CONF_TELEGRAM_API_HASH])
                await client.connect()
                sent = await client.send_code_request(data[CONF_TELEGRAM_PHONE])
                self._telegram_client = client
                self._phone_code_hash = sent.phone_code_hash
                self._pending = data
                return await self.async_step_telegram_code()
            except PhoneNumberInvalidError:
                errors[CONF_TELEGRAM_PHONE] = "invalid_phone"
            except FloodWaitError:
                errors["base"] = "telegram_flood_wait"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Could not start Telegram authorization")
                errors["base"] = "telegram_connection_error"
        return self.async_show_form(step_id="telegram", data_schema=_telegram_schema(user_input), errors=errors)

    async def async_step_telegram_code(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                from telethon.errors import PhoneCodeExpiredError, PhoneCodeInvalidError, SessionPasswordNeededError

                await self._telegram_client.sign_in(
                    phone=self._pending[CONF_TELEGRAM_PHONE],
                    code=str(user_input[CONF_TELEGRAM_CODE]).strip(),
                    phone_code_hash=self._phone_code_hash,
                )
                return await self._async_finish_telegram()
            except SessionPasswordNeededError:
                return await self.async_step_telegram_password()
            except PhoneCodeInvalidError:
                errors[CONF_TELEGRAM_CODE] = "invalid_code"
            except PhoneCodeExpiredError:
                errors[CONF_TELEGRAM_CODE] = "expired_code"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Telegram sign-in code failed")
                errors["base"] = "telegram_login_error"
        return self.async_show_form(
            step_id="telegram_code",
            data_schema=vol.Schema({vol.Required(CONF_TELEGRAM_CODE): str}),
            errors=errors,
        )

    async def async_step_telegram_password(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                from telethon.errors import PasswordHashInvalidError

                await self._telegram_client.sign_in(password=user_input[CONF_TELEGRAM_PASSWORD])
                return await self._async_finish_telegram()
            except PasswordHashInvalidError:
                errors[CONF_TELEGRAM_PASSWORD] = "invalid_password"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Telegram 2FA sign-in failed")
                errors["base"] = "telegram_login_error"
        return self.async_show_form(
            step_id="telegram_password",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TELEGRAM_PASSWORD): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    )
                }
            ),
            errors=errors,
        )

    async def _async_finish_telegram(self) -> FlowResult:
        from telethon.sessions import StringSession

        self._pending[CONF_TELEGRAM_SESSION] = StringSession.save(self._telegram_client.session)
        await self._telegram_client.disconnect()
        self._telegram_client = None
        return self.async_create_entry(title=self._pending[CONF_MONITOR_NAME], data=self._pending)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        return P2000CompanionOptionsFlow(config_entry)


class P2000CompanionOptionsFlow(config_entries.OptionsFlow):
    """Edit an existing monitor profile."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        defaults = {**self._config_entry.data, **self._config_entry.options}
        provider = defaults.get(CONF_PROVIDER, PROVIDER_RSS)
        errors: dict[str, str] = {}

        if user_input is not None:
            if provider == PROVIDER_RSS:
                data = _normalize_rss_input(user_input)
                if not _valid_urls(data[CONF_FEED_URL]):
                    errors[CONF_FEED_URL] = "invalid_url"
                else:
                    self.hass.config_entries.async_update_entry(self._config_entry, title=data[CONF_MONITOR_NAME])
                    return self.async_create_entry(title="", data=data)
            else:
                # Credentials and session remain in entry.data; options only change monitor filters/chat.
                data = _normalize_filters(dict(user_input))
                data[CONF_PROVIDER] = PROVIDER_TELEGRAM
                data[CONF_TELEGRAM_CHAT] = str(data[CONF_TELEGRAM_CHAT]).strip()
                self.hass.config_entries.async_update_entry(self._config_entry, title=data[CONF_MONITOR_NAME])
                return self.async_create_entry(title="", data=data)

        defaults.setdefault(CONF_MONITOR_NAME, self._config_entry.title or DEFAULT_NAME)
        schema = _rss_schema(defaults) if provider == PROVIDER_RSS else _telegram_schema(defaults, include_credentials=False)
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
