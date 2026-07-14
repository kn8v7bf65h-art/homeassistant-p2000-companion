"""Sensors for P2000 Companion monitor profiles."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_CREATE_FEED_SENSOR,
    CONF_PROVIDER,
    DEFAULT_CREATE_FEED_SENSOR,
    DEFAULT_PROVIDER,
    DOMAIN,
    PROVIDER_TELEGRAM,
)
from .coordinator import P2000Coordinator
from .telegram_coordinator import P2000TelegramCoordinator

Coordinator = P2000Coordinator | P2000TelegramCoordinator

SERVICE_SENSOR_INFO: dict[str, tuple[str, str]] = {
    "ambulance": ("Laatste ambulancemelding", "mdi:ambulance"),
    "fire": ("Laatste brandweermelding", "mdi:fire-truck"),
    "police": ("Laatste politiemelding", "mdi:police-badge"),
    "mmt": ("Laatste MMT-melding", "mdi:helicopter"),
    "lifeboat": ("Laatste KNRM-melding", "mdi:lifebuoy"),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up monitor sensors."""
    coordinator: Coordinator = hass.data[DOMAIN][entry.entry_id]
    options = {**entry.data, **entry.options}

    entities: list[SensorEntity] = [
        P2000LastAlertSensor(coordinator, entry, filtered=True),
        *[
            P2000LastServiceAlertSensor(coordinator, entry, service)
            for service in SERVICE_SENSOR_INFO
        ],
    ]

    if (
        options.get(CONF_PROVIDER, DEFAULT_PROVIDER) != PROVIDER_TELEGRAM
        and bool(options.get(CONF_CREATE_FEED_SENSOR, DEFAULT_CREATE_FEED_SENSOR))
    ):
        entities.insert(0, P2000LastAlertSensor(coordinator, entry, filtered=False))

    async_add_entities(entities)


class P2000BaseSensor(CoordinatorEntity, SensorEntity):
    """Shared sensor behavior."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: Coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entry = entry
        provider = entry.data.get(CONF_PROVIDER, DEFAULT_PROVIDER)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=coordinator.monitor_name,
            manufacturer="P2000 Companion",
            model=(
                "Telegram-monitorprofiel"
                if provider == PROVIDER_TELEGRAM
                else "RSS-monitorprofiel"
            ),
            configuration_url=(
                "https://github.com/kn8v7bf65h-art/"
                "homeassistant-p2000-companion"
            ),
        )

    def _base_attributes(self) -> dict:
        return {
            "monitor_name": self.coordinator.monitor_name,
            "monitor_id": self.entry.entry_id,
            "monitor_event": self.coordinator.monitor_event,
            "provider": self.entry.data.get(CONF_PROVIDER, DEFAULT_PROVIDER),
            "feed_url": self.coordinator.feed_url,
            "feed_urls": self.coordinator.feed_urls,
            "alerts_in_feed": self.coordinator.last_update_success_count,
            "new_alerts_last_update": self.coordinator.last_new_alerts_count,
            "filtered_alerts_last_update": self.coordinator.last_filtered_alerts_count,
        }

    def _alert_attributes(self, alert) -> dict:
        base = self._base_attributes()
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


class P2000LastAlertSensor(P2000BaseSensor):
    """Last feed or filtered alert for one monitor."""

    _attr_icon = "mdi:alarm-light"

    def __init__(
        self,
        coordinator: Coordinator,
        entry: ConfigEntry,
        filtered: bool,
    ) -> None:
        super().__init__(coordinator, entry)
        self.filtered = filtered
        suffix = "filtered" if filtered else "feed"
        self._attr_unique_id = f"{entry.entry_id}_{suffix}"
        self._attr_name = (
            "Laatste gefilterde melding" if filtered else "Laatste feedmelding"
        )

    @property
    def native_value(self):
        alert = (
            self.coordinator.last_filtered_alert
            if self.filtered
            else self.coordinator.last_alert
        )
        return alert.title if alert else "Geen melding"

    @property
    def extra_state_attributes(self):
        alert = (
            self.coordinator.last_filtered_alert
            if self.filtered
            else self.coordinator.last_alert
        )
        return self._alert_attributes(alert)


class P2000LastServiceAlertSensor(P2000BaseSensor):
    """Keep the last filtered alert for one emergency service."""

    def __init__(
        self,
        coordinator: Coordinator,
        entry: ConfigEntry,
        service: str,
    ) -> None:
        super().__init__(coordinator, entry)
        self.service = service
        name, icon = SERVICE_SENSOR_INFO[service]
        self._attr_unique_id = f"{entry.entry_id}_service_{service}"
        self._attr_name = name
        self._attr_icon = icon

    @property
    def native_value(self):
        alert = self.coordinator.last_filtered_alert_by_service.get(self.service)
        return alert.title if alert else "Geen melding"

    @property
    def extra_state_attributes(self):
        alert = self.coordinator.last_filtered_alert_by_service.get(self.service)
        return {
            **self._alert_attributes(alert),
            "service_filter": self.service,
        }
