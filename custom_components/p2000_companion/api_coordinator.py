"""P2000 Haaglanden API coordinator for P2000 Companion."""
from __future__ import annotations

from datetime import timedelta
import logging
import re
from typing import Any

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import (
    CONF_API_KEY,
    CONF_API_URL,
    CONF_SCAN_INTERVAL,
    DEFAULT_API_SCAN_INTERVAL,
    DEFAULT_API_URL,
    EVENT_FEED_ALERT,
    EVENT_FILTERED_ALERT,
    EVENT_LEGACY_FILTERED_ALERT,
)
from .coordinator import P2000Coordinator
from .parser import Alert, normalize_service, parse_city, parse_priority

_LOGGER = logging.getLogger(__name__)

MMT_PATTERN = re.compile(r"\b(mmt|lifeliner|lfl\d+|traumaheli)\b", re.IGNORECASE)
DEN_HAAG_PATTERN = re.compile(r"(?:'s[- ]?gravenhage|s[- ]?gravenhage|den haag)", re.IGNORECASE)
STREET_BEFORE_CITY_PATTERN = re.compile(
    r"\b([A-ZÀ-ÖØ-öø-ÿ][\w'’.-]*(?:straat|laan|weg|plein|kade|singel|dijk|gracht|hof|pad|park|steeg|markt|baan|boulevard|plantsoen|wal|haven|zoom|veld|akker|dreef))\s+(?:'s[- ]?gravenhage|s[- ]?gravenhage|den haag)\b",
    re.IGNORECASE,
)
MMT_PRESENTATION = {
    "type": "mmt",
    "icon": "🚁",
    "label": "MMT / Lifeliner",
}


def _api_city(message: str, api_city: str | None, link: str | None) -> str | None:
    """Return a normalized city, repairing known upstream parsing gaps."""
    if api_city:
        if DEN_HAAG_PATTERN.fullmatch(str(api_city).strip()):
            return "Den Haag"
        return str(api_city).strip()
    if DEN_HAAG_PATTERN.search(message):
        return "Den Haag"
    return parse_city(message, link)


def _api_street(message: str, api_street: str | None, city: str | None) -> str | None:
    """Return a cleaned street when the upstream API kept incident text in it."""
    if city == "Den Haag":
        match = STREET_BEFORE_CITY_PATTERN.search(message)
        if match:
            return match.group(1).strip()
    return str(api_street).strip(" ,") if api_street else None


class P2000ApiCoordinator(P2000Coordinator):
    """Poll the official P2000 Haaglanden API and fire P2000 events."""

    def __init__(self, hass, entry) -> None:
        super().__init__(hass, entry)
        interval = int(
            entry.options.get(
                CONF_SCAN_INTERVAL,
                entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_API_SCAN_INTERVAL),
            )
        )
        self.update_interval = timedelta(seconds=interval)
        self.api_metadata_by_id: dict[str, dict[str, Any]] = {}

    @property
    def feed_url(self) -> str:
        return str(
            self.entry.options.get(
                CONF_API_URL,
                self.entry.data.get(CONF_API_URL, DEFAULT_API_URL),
            )
        )

    @property
    def feed_urls(self) -> list[str]:
        return [self.feed_url]

    @property
    def api_key(self) -> str:
        return str(
            self.entry.options.get(
                CONF_API_KEY,
                self.entry.data.get(CONF_API_KEY, ""),
            )
        ).strip()

    def get_api_metadata(self, alert_id: str) -> dict[str, Any]:
        """Return structured API metadata for an alert."""
        return self.api_metadata_by_id.get(str(alert_id), {})

    async def _fetch_api(self) -> list[Alert]:
        session = async_get_clientsession(self.hass)
        headers = {"X-API-Key": self.api_key}
        try:
            async with session.get(self.feed_url, headers=headers, timeout=10) as response:
                response.raise_for_status()
                payload = await response.json()
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"Could not fetch P2000 Haaglanden API: {err}") from err

        if not payload.get("success"):
            raise UpdateFailed(payload.get("message") or "P2000 API returned success=false")

        data = payload.get("data") or {}
        items = data.get("meldingen") or []
        alerts: list[Alert] = []
        fresh_metadata: dict[str, dict[str, Any]] = {}

        for item in items:
            dienst = item.get("dienst") or {}
            locatie = item.get("locatie") or {}
            tijdstip = item.get("tijdstip") or {}
            api_id = str(item.get("id", "")).strip()
            if not api_id:
                continue

            message = str(item.get("melding") or "").strip()
            link = item.get("url")

            raw_service = dienst.get("type")
            service = normalize_service(raw_service)
            is_mmt = bool(MMT_PATTERN.search(message))
            if is_mmt:
                service = "mmt"

            raw_priority = item.get("prioriteit")
            priority = None
            if raw_priority:
                raw_priority_text = str(raw_priority)
                priority = (
                    parse_priority(raw_priority_text)
                    or raw_priority_text.upper().replace(" ", "")
                )

            city = _api_city(message, locatie.get("stad"), link)
            street = _api_street(message, locatie.get("straat"), city)
            location_full = (
                f"{street}, {city}"
                if street and city
                else (city or street or locatie.get("volledig"))
            )
            published = tijdstip.get("raw") or tijdstip.get("formatted")

            service_type = MMT_PRESENTATION["type"] if is_mmt else raw_service
            service_icon = MMT_PRESENTATION["icon"] if is_mmt else dienst.get("icon")
            service_label = MMT_PRESENTATION["label"] if is_mmt else dienst.get("label")

            alert = Alert(
                id=api_id,
                title=message,
                message=message,
                summary=message or None,
                link=link,
                published=published,
                city=city,
                service=service or None,
                priority=priority,
                raw_text=message,
                source_feed_url=self.feed_url,
            )
            alerts.append(alert)
            fresh_metadata[api_id] = {
                "api_id": item.get("id"),
                "service_type": service_type,
                "service_icon": service_icon,
                "service_color": dienst.get("color"),
                "service_label": service_label,
                "api_service_type": raw_service,
                "api_service_icon": dienst.get("icon"),
                "api_service_color": dienst.get("color"),
                "api_service_label": dienst.get("label"),
                "service_corrected": is_mmt,
                "priority_label": raw_priority,
                "kind": item.get("soort"),
                "location_street": street,
                "location_city": city,
                "location_full": location_full,
                "api_location_street": locatie.get("straat"),
                "api_location_city": locatie.get("stad"),
                "api_location_full": locatie.get("volledig"),
                "location_corrected": bool(city and not locatie.get("stad")) or street != locatie.get("straat"),
                "time_raw": tijdstip.get("raw"),
                "time_formatted": tijdstip.get("formatted"),
                "time_unix": tijdstip.get("unix"),
                "time_relative": tijdstip.get("relatief"),
                "capcodes": item.get("capcodes") or [],
                "api_generated_at": data.get("generated_at"),
            }

        self.api_metadata_by_id.update(fresh_metadata)
        return alerts

    def _event_data(self, alert: Alert) -> dict[str, Any]:
        data = alert.as_event_data()
        data.update(self.get_api_metadata(alert.id))
        data.update({
            "provider": "api",
            "monitor_name": self.monitor_name,
            "monitor_id": self.entry.entry_id,
            "monitor_event": self.monitor_event,
        })
        return data

    def _repair_service_cache(self, alerts: list[Alert]) -> bool:
        """Remove cached service entries whose alert is now reclassified."""
        service_by_id = {alert.id: alert.service for alert in alerts}
        changed = False
        for cached_service, cached_alert in list(self.last_filtered_alert_by_service.items()):
            corrected_service = service_by_id.get(cached_alert.id)
            if corrected_service and corrected_service != cached_service:
                self.last_filtered_alert_by_service.pop(cached_service, None)
                changed = True
        return changed

    async def _async_update_data(self) -> list[Alert]:
        if not self._cache_loaded:
            await self.async_load_cache()

        alerts = await self._fetch_api()
        self.last_update_success_count = len(alerts)
        self.last_new_alerts_count = 0
        self.last_filtered_alerts_count = 0

        if not alerts:
            return []

        cache_changed = self._repair_service_cache(alerts)
        self.last_alert = alerts[0]
        first_filtered = next((a for a in alerts if self._matches_filters(a)), None)
        if first_filtered:
            self.last_filtered_alert = first_filtered
        for candidate in alerts:
            if (
                candidate.service
                and candidate.service not in self.last_filtered_alert_by_service
                and self._matches_filters(candidate)
            ):
                self.last_filtered_alert_by_service[candidate.service] = candidate
                cache_changed = True

        if not self._seen_ids:
            self._seen_ids = {alert.id for alert in alerts}
            await self._async_save_cache()
            return alerts

        new_alerts = [alert for alert in reversed(alerts) if alert.id not in self._seen_ids]
        self.last_new_alerts_count = len(new_alerts)

        for alert in new_alerts:
            self._seen_ids.add(alert.id)
            self.last_alert = alert
            self.hass.bus.async_fire(EVENT_FEED_ALERT, self._event_data(alert))

            if self._matches_filters(alert):
                self.last_filtered_alert = alert
                if alert.service:
                    self.last_filtered_alert_by_service[alert.service] = alert
                self.last_filtered_alerts_count += 1
                event_data = self._event_data(alert)
                self.last_monitor_event = self.monitor_event
                self.hass.bus.async_fire(EVENT_FILTERED_ALERT, event_data)
                self.hass.bus.async_fire(EVENT_LEGACY_FILTERED_ALERT, event_data)
                self.hass.bus.async_fire(self.monitor_event, event_data)

        if new_alerts or cache_changed:
            await self._async_save_cache()
        return alerts
