"""Data coordinator for P2000 Companion."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

import feedparser

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store

from .const import (
    CONF_CITIES,
    CONF_EXCLUDE_WORDS,
    CONF_FEED_URL,
    CONF_PRIORITIES,
    CONF_SCAN_INTERVAL,
    CONF_SERVICES,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    EVENT_FEED_ALERT,
    EVENT_FILTERED_ALERT,
    EVENT_LEGACY_FILTERED_ALERT,
)
from .parser import Alert, parse_entry

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
MAX_SEEN_IDS = 1000
KEEP_SEEN_IDS = 500


class P2000Coordinator(DataUpdateCoordinator[list[Alert]]):
    """Fetch RSS feed and fire events for every new alert."""

    def __init__(self, hass: HomeAssistant, entry) -> None:
        self.entry = entry
        self._seen_ids: set[str] = set()
        self._store: Store[dict[str, Any]] = Store(
            hass,
            STORAGE_VERSION,
            f"{DOMAIN}_{entry.entry_id}_seen_alerts",
        )
        self._cache_loaded = False
        self.last_update_success_count = 0
        self.last_new_alerts_count = 0
        self.last_filtered_alerts_count = 0
        self.last_alert: Alert | None = None
        self.last_filtered_alert: Alert | None = None
        interval = int(entry.options.get(CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)))

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(seconds=interval),
        )

    async def async_load_cache(self) -> None:
        """Load persistent seen-alert cache before the first feed refresh."""
        stored = await self._store.async_load()
        if stored:
            self._seen_ids = set(stored.get("seen_ids", []))
        self._cache_loaded = True
        _LOGGER.debug("Loaded %s seen P2000 alert ids", len(self._seen_ids))

    async def _async_save_cache(self) -> None:
        """Persist seen-alert cache to Home Assistant storage."""
        if len(self._seen_ids) > MAX_SEEN_IDS:
            # Sets are unordered, but keeping a bounded sample is enough to prevent
            # recent duplicate events while avoiding unbounded storage growth.
            self._seen_ids = set(list(self._seen_ids)[-KEEP_SEEN_IDS:])
        await self._store.async_save({"seen_ids": list(self._seen_ids)})

    @property
    def feed_url(self) -> str:
        """Return the currently configured feed URL, including option changes."""
        return str(self.entry.options.get(CONF_FEED_URL, self.entry.data.get(CONF_FEED_URL, "")))

    async def _async_update_data(self) -> list[Alert]:
        if not self._cache_loaded:
            await self.async_load_cache()

        session = async_get_clientsession(self.hass)
        try:
            async with session.get(self.feed_url, timeout=20) as response:
                response.raise_for_status()
                text = await response.text()
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"Could not fetch P2000 feed: {err}") from err

        parsed = await self.hass.async_add_executor_job(feedparser.parse, text)
        alerts = [parse_entry(entry) for entry in parsed.entries]

        self.last_update_success_count = len(alerts)
        self.last_new_alerts_count = 0
        self.last_filtered_alerts_count = 0

        if not alerts:
            return []

        # Keep dashboard sensors useful immediately, even when there are no new events.
        self.last_alert = alerts[0]
        first_filtered = next((a for a in alerts if self._matches_filters(a)), None)
        if first_filtered:
            self.last_filtered_alert = first_filtered

        # First install with an empty cache: mark current feed as known so old feed
        # items do not trigger a burst of automations. Existing persistent cache does
        # allow missed new items since the last HA run to be processed.
        if not self._seen_ids:
            self._seen_ids = {alert.id for alert in alerts}
            await self._async_save_cache()
            return alerts

        # Process every new RSS item, oldest first, so automations fire in real order.
        new_alerts = [alert for alert in reversed(alerts) if alert.id not in self._seen_ids]
        self.last_new_alerts_count = len(new_alerts)

        if not new_alerts:
            return alerts

        for alert in new_alerts:
            self._seen_ids.add(alert.id)
            self.last_alert = alert
            self.hass.bus.async_fire(EVENT_FEED_ALERT, alert.as_event_data())

            if self._matches_filters(alert):
                self.last_filtered_alert = alert
                self.last_filtered_alerts_count += 1
                event_data = alert.as_event_data()
                self.hass.bus.async_fire(EVENT_FILTERED_ALERT, event_data)
                # Backwards compatibility for automations created before v0.1.5.
                self.hass.bus.async_fire(EVENT_LEGACY_FILTERED_ALERT, event_data)

        await self._async_save_cache()
        return alerts

    def _matches_filters(self, alert: Alert) -> bool:
        options: dict[str, Any] = {**self.entry.data, **self.entry.options}

        raw_text = (alert.raw_text or "").lower()
        city = (alert.city or "").lower()
        service = (alert.service or "").lower()
        priority = (alert.priority or "").upper()

        cities = [c.lower() for c in options.get(CONF_CITIES, []) if c]
        services = [str(s).lower().strip() for s in options.get(CONF_SERVICES, []) if s]
        priorities = [p.upper().replace(" ", "") for p in options.get(CONF_PRIORITIES, []) if p]
        exclude_words = [w.lower() for w in options.get(CONF_EXCLUDE_WORDS, []) if w]

        if exclude_words and any(word in raw_text for word in exclude_words):
            return False
        if cities and not any(c in city or c in raw_text for c in cities):
            return False
        if services and service not in services:
            return False
        if priorities and priority not in priorities:
            return False

        return True
