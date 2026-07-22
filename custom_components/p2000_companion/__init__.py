"""P2000 Companion integration."""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_PROVIDER,
    DEFAULT_PROVIDER,
    DOMAIN,
    PLATFORMS,
    PROVIDER_TELEGRAM,
)
from .coordinator import P2000Coordinator
from .telegram_coordinator import P2000TelegramCoordinator

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
CARD_URL = "/p2000_companion/p2000-companion-card.js"
CARD_PATH = Path(__file__).parent / "www" / "p2000-companion-card.js"
DATA_FRONTEND_REGISTERED = f"{DOMAIN}_frontend_registered"


async def _async_register_frontend(hass: HomeAssistant) -> None:
    """Serve and load the bundled Lovelace cards once per Home Assistant run."""
    if hass.data.get(DATA_FRONTEND_REGISTERED):
        return

    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(CARD_PATH), cache_headers=False)]
    )

    # Loading the module globally makes both cards immediately available in the
    # dashboard card picker. The static URL remains usable as a manual resource
    # fallback on installations where global frontend module loading is disabled.
    try:
        from homeassistant.components.frontend import add_extra_js_url

        add_extra_js_url(hass, CARD_URL)
    except (ImportError, AttributeError):
        _LOGGER.warning(
            "Could not automatically load the P2000 Companion cards. "
            "Add %s manually as a JavaScript module under Dashboard resources.",
            CARD_URL,
        )

    hass.data[DATA_FRONTEND_REGISTERED] = True


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up shared integration resources."""
    await _async_register_frontend(hass)
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate older P2000 Companion config entries."""
    if entry.version > 4:
        return False

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
    )
    from .parser import csv_to_list, normalize_service

    combined = {**entry.data, **entry.options}

    if entry.version == 1:
        monitor_name = str(
            combined.get(CONF_MONITOR_NAME) or entry.title or DEFAULT_NAME
        ).strip()
        feed_url = str(combined.get(CONF_FEED_URL) or DEFAULT_FEED_URL).strip()

        def _list_value(key: str) -> list[str]:
            value = combined.get(key, [])
            if isinstance(value, list):
                return [str(item).strip() for item in value if str(item).strip()]
            return csv_to_list(value)

        migrated_data = {
            CONF_PROVIDER: DEFAULT_PROVIDER,
            CONF_MONITOR_NAME: monitor_name,
            CONF_FEED_URL: feed_url,
            CONF_CITIES: _list_value(CONF_CITIES),
            CONF_SERVICES: [
                normalize_service(item) for item in _list_value(CONF_SERVICES)
            ],
            CONF_PRIORITIES: [
                item.upper().replace(" ", "")
                for item in _list_value(CONF_PRIORITIES)
            ],
            CONF_TEXT_CONTAINS: [
                item.lower() for item in _list_value(CONF_TEXT_CONTAINS)
            ],
            CONF_EXCLUDE_WORDS: [
                item.lower() for item in _list_value(CONF_EXCLUDE_WORDS)
            ],
            CONF_SCAN_INTERVAL: int(
                combined.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ),
            CONF_CREATE_FEED_SENSOR: bool(
                combined.get(CONF_CREATE_FEED_SENSOR, DEFAULT_CREATE_FEED_SENSOR)
            ),
        }
        hass.config_entries.async_update_entry(
            entry,
            title=monitor_name,
            data=migrated_data,
            options={},
            version=4,
        )
        return True

    # v2/v3 entries are RSS monitors. Add missing defaults while preserving
    # all existing filters and options.
    if entry.version in (2, 3):
        data = dict(entry.data)
        options = dict(entry.options)
        data.setdefault(CONF_PROVIDER, DEFAULT_PROVIDER)
        if entry.version == 2:
            target = options if options else data
            target.setdefault(CONF_CREATE_FEED_SENSOR, DEFAULT_CREATE_FEED_SENSOR)
        hass.config_entries.async_update_entry(
            entry,
            data=data,
            options=options,
            version=4,
        )


    return True


async def _async_remove_unused_feed_sensor(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """Remove the optional feed sensor when it is disabled in monitor options."""
    from .const import CONF_CREATE_FEED_SENSOR, DEFAULT_CREATE_FEED_SENSOR

    options = {**entry.data, **entry.options}
    if bool(options.get(CONF_CREATE_FEED_SENSOR, DEFAULT_CREATE_FEED_SENSOR)):
        return

    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id(
        "sensor", DOMAIN, f"{entry.entry_id}_feed"
    )
    if entity_id is not None:
        registry.async_remove(entity_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up P2000 Companion from a config entry."""
    await _async_register_frontend(hass)
    await _async_remove_unused_feed_sensor(hass, entry)

    provider = entry.data.get(CONF_PROVIDER, DEFAULT_PROVIDER)
    if provider == PROVIDER_TELEGRAM:
        coordinator = P2000TelegramCoordinator(hass, entry)
        await coordinator.async_load_cache()
        await coordinator.async_start()
        await coordinator.async_config_entry_first_refresh()
    else:
        coordinator = P2000Coordinator(hass, entry)
        await coordinator.async_load_cache()
        await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_update_options))
    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload an entry when monitor options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        if isinstance(coordinator, P2000TelegramCoordinator):
            await coordinator.async_stop()
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
