"""Sensors for P2000 Companion."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import P2000Coordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: P2000Coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        P2000LastAlertSensor(coordinator, entry, filtered=False),
        P2000LastAlertSensor(coordinator, entry, filtered=True),
    ])


class P2000LastAlertSensor(CoordinatorEntity[P2000Coordinator], SensorEntity):
    """Last P2000 alert sensor."""

    _attr_icon = "mdi:alarm-light"

    def __init__(self, coordinator: P2000Coordinator, entry: ConfigEntry, filtered: bool) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self.filtered = filtered
        suffix = "filtered" if filtered else "feed"
        self._attr_unique_id = f"{entry.entry_id}_{suffix}"
        self._attr_name = "P2000 Last Filtered Alert" if filtered else "P2000 Last Feed Alert"

    @property
    def native_value(self):
        alert = self.coordinator.last_filtered_alert if self.filtered else self.coordinator.last_alert
        return alert.title if alert else "Geen melding"

    @property
    def extra_state_attributes(self):
        alert = self.coordinator.last_filtered_alert if self.filtered else self.coordinator.last_alert
        base = {
            "feed_url": self.coordinator.feed_url,
            "alerts_in_feed": self.coordinator.last_update_success_count,
            "new_alerts_last_update": self.coordinator.last_new_alerts_count,
            "filtered_alerts_last_update": self.coordinator.last_filtered_alerts_count,
        }
        if not alert:
            return base
        return {
            **base,
            "id": alert.id,
            "message": alert.message,
            "summary": alert.summary,
            "link": alert.link,
            "published": alert.published,
            "city": alert.city,
            "service": alert.service,
            "priority": alert.priority,
            "raw_text": alert.raw_text,
        }
