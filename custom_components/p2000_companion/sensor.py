"""Sensors for P2000 Companion monitor profiles."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_CREATE_FEED_SENSOR, DEFAULT_CREATE_FEED_SENSOR, DOMAIN
from .coordinator import P2000Coordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: P2000Coordinator = hass.data[DOMAIN][entry.entry_id]
    options = {**entry.data, **entry.options}
    entities: list[SensorEntity] = [
        P2000LastAlertSensor(coordinator, entry, filtered=True),
    ]
    if bool(options.get(CONF_CREATE_FEED_SENSOR, DEFAULT_CREATE_FEED_SENSOR)):
        entities.insert(0, P2000LastAlertSensor(coordinator, entry, filtered=False))
    async_add_entities(entities)


class P2000LastAlertSensor(CoordinatorEntity[P2000Coordinator], SensorEntity):
    """Last alert sensor for one user-defined monitor."""

    _attr_icon = "mdi:alarm-light"
    _attr_has_entity_name = True

    def __init__(self, coordinator: P2000Coordinator, entry: ConfigEntry, filtered: bool) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self.filtered = filtered
        suffix = "filtered" if filtered else "feed"
        self._attr_unique_id = f"{entry.entry_id}_{suffix}"
        self._attr_name = "Laatste gefilterde melding" if filtered else "Laatste feedmelding"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=coordinator.monitor_name,
            manufacturer="P2000 Companion",
            model="RSS-monitorprofiel",
            configuration_url="https://github.com/kn8v7bf65h-art/homeassistant-p2000-companion",
        )

    @property
    def native_value(self):
        alert = self.coordinator.last_filtered_alert if self.filtered else self.coordinator.last_alert
        return alert.title if alert else "Geen melding"

    @property
    def extra_state_attributes(self):
        alert = self.coordinator.last_filtered_alert if self.filtered else self.coordinator.last_alert
        base = {
            "monitor_name": self.coordinator.monitor_name,
            "monitor_id": self.entry.entry_id,
            "monitor_event": self.coordinator.monitor_event,
            "feed_url": self.coordinator.feed_url,
            "feed_urls": self.coordinator.feed_urls,
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
            "source_feed_url": alert.source_feed_url,
        }
