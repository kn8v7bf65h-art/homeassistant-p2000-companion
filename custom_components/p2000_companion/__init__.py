"""P2000 Companion integration."""
from __future__ import annotations

from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import P2000Coordinator

CARD_URL = "/p2000_companion/p2000-companion-card.js"
CARD_PATH = Path(__file__).parent / "www" / "p2000-companion-card.js"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register the bundled Lovelace card as a static Home Assistant resource."""
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(CARD_PATH), cache_headers=False)]
    )
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate older P2000 Companion config entries.

    Version 1 entries predate user-defined monitor profiles. They are upgraded
    in place so existing installations keep their feed and filter settings.
    """
    if entry.version > 2:
        return False

    if entry.version == 1:
        from .const import (
            CONF_CITIES,
            CONF_EXCLUDE_WORDS,
            CONF_FEED_URL,
            CONF_MONITOR_NAME,
            CONF_PRIORITIES,
            CONF_SCAN_INTERVAL,
            CONF_SERVICES,
            CONF_TEXT_CONTAINS,
            DEFAULT_FEED_URL,
            DEFAULT_NAME,
            DEFAULT_SCAN_INTERVAL,
        )
        from .parser import csv_to_list, normalize_service

        data = dict(entry.data)
        options = dict(entry.options)
        combined = {**data, **options}

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
        }

        hass.config_entries.async_update_entry(
            entry,
            title=monitor_name,
            data=migrated_data,
            options={},
            version=2,
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = P2000Coordinator(hass, entry)
    await coordinator.async_load_cache()
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_update_options))
    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
