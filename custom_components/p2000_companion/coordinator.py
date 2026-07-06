"""Data coordinator for P2000 Companion."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

import feedparser

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

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


class P2000Coordinator(DataUpdateCoordinator[list[Alert]]):
    """Fetch RSS feed and fire events for new alerts."""

    def __init__(self, hass: HomeAssistant, entry) -> None:
        self.entry = entry
        self._seen_ids: set[str] = set()
        self.last_update_success_count = 0
        self.last_alert: Alert | None = None
        self.last_filtered_alert: Alert | None = None
        interval = int(entry.options.get(CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)))

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(seconds=interval),
        )

    @property
    def feed_url(self) -> str:
        """Return the currently configured feed URL, including option changes."""
        return str(self.entry.options.get(CONF_FEED_URL, self.entry.data.get(CONF_FEED_URL, "")))

    async def _async_update_data(self) -> list[Alert]:
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

        if not alerts:
            return []

        # On first run: remember existing feed items, but do not fire events for old items.
        if not self._seen_ids:
            self._seen_ids = {alert.id for alert in alerts}
            self.last_alert = alerts[0]
            self.last_filtered_alert = next((a for a in alerts if self._matches_filters(a)), None)
            return alerts

        new_alerts = [alert for alert in reversed(alerts) if alert.id not in self._seen_ids]
        for alert in new_alerts:
            self._seen_ids.add(alert.id)
            self.last_alert = alert
            self.hass.bus.async_fire(EVENT_FEED_ALERT, alert.as_event_data())

            if self._matches_filters(alert):
                self.last_filtered_alert = alert
                event_data = alert.as_event_data()
                self.hass.bus.async_fire(EVENT_FILTERED_ALERT, event_data)
                # Backwards compatibility for automations created before v0.1.5.
                self.hass.bus.async_fire(EVENT_LEGACY_FILTERED_ALERT, event_data)

        # Keep seen cache bounded.
        if len(self._seen_ids) > 500:
            current_ids = {alert.id for alert in alerts}
            self._seen_ids = current_ids | set(list(self._seen_ids)[-250:])

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
