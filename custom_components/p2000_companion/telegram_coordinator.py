"""Realtime Telethon provider for P2000 Companion."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any
from dataclasses import asdict

from homeassistant.config_entries import ConfigEntryAuthFailed
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_CITIES,
    CONF_EXCLUDE_WORDS,
    CONF_MONITOR_NAME,
    CONF_PRIORITIES,
    CONF_SERVICES,
    CONF_TELEGRAM_API_HASH,
    CONF_TELEGRAM_API_ID,
    CONF_TELEGRAM_CHAT,
    CONF_TELEGRAM_SESSION,
    CONF_TEXT_CONTAINS,
    DOMAIN,
    EVENT_FEED_ALERT,
    EVENT_FILTERED_ALERT,
    EVENT_LEGACY_FILTERED_ALERT,
    EVENT_MONITOR_PREFIX,
)
from .parser import Alert, parse_telegram_message, slugify_event_name

_LOGGER = logging.getLogger(__name__)
STORAGE_VERSION = 1
MAX_SEEN_IDS = 1000
KEEP_SEEN_IDS = 500


class P2000TelegramCoordinator(DataUpdateCoordinator[list[Alert]]):
    """Receive Telegram messages in realtime through a user session."""

    def __init__(self, hass: HomeAssistant, entry) -> None:
        self.entry = entry
        self.client = None
        self._event_builder = None
        self._seen_ids: set[str] = set()
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}_{entry.entry_id}_telegram_seen"
        )
        self.last_update_success_count = 0
        self.last_new_alerts_count = 0
        self.last_filtered_alerts_count = 0
        self.last_alert: Alert | None = None
        self.last_filtered_alert: Alert | None = None
        self.last_filtered_alert_by_service: dict[str, Alert] = {}
        self.last_monitor_event: str | None = None
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}_telegram",
            update_interval=timedelta(minutes=5),
        )

    @property
    def options(self) -> dict[str, Any]:
        return {**self.entry.data, **self.entry.options}

    @property
    def monitor_name(self) -> str:
        return str(self.options.get(CONF_MONITOR_NAME, self.entry.title)).strip() or self.entry.title

    @property
    def monitor_event(self) -> str:
        return f"{EVENT_MONITOR_PREFIX}{slugify_event_name(self.monitor_name)}"

    @property
    def feed_url(self) -> str:
        return f"telegram://{self.options.get(CONF_TELEGRAM_CHAT, '')}"

    @property
    def feed_urls(self) -> list[str]:
        return [self.feed_url]

    @property
    def chat_ref(self) -> int | str:
        value = str(self.options.get(CONF_TELEGRAM_CHAT, "")).strip()
        try:
            return int(value)
        except ValueError:
            return value

    async def async_load_cache(self) -> None:
        stored = await self._store.async_load()
        if stored:
            self._seen_ids = set(stored.get("seen_ids", []))
            for service, alert_data in stored.get("last_filtered_alert_by_service", {}).items():
                try:
                    self.last_filtered_alert_by_service[service] = Alert(**alert_data)
                except (TypeError, ValueError):
                    _LOGGER.warning("Could not restore stored %s alert", service)

    async def _async_save_cache(self) -> None:
        if len(self._seen_ids) > MAX_SEEN_IDS:
            self._seen_ids = set(list(self._seen_ids)[-KEEP_SEEN_IDS:])
        await self._store.async_save({
            "seen_ids": list(self._seen_ids),
            "last_filtered_alert_by_service": {
                service: asdict(alert)
                for service, alert in self.last_filtered_alert_by_service.items()
            },
        })

    async def async_start(self) -> None:
        """Connect Telethon and register the realtime message handler."""
        from telethon import TelegramClient, events
        from telethon.sessions import StringSession

        api_id = int(self.entry.data[CONF_TELEGRAM_API_ID])
        api_hash = self.entry.data[CONF_TELEGRAM_API_HASH]
        session = self.entry.data[CONF_TELEGRAM_SESSION]

        self.client = TelegramClient(
            StringSession(session),
            api_id,
            api_hash,
            sequential_updates=True,
        )
        await self.client.connect()
        if not await self.client.is_user_authorized():
            await self.client.disconnect()
            raise ConfigEntryAuthFailed("Telegram session is no longer authorized")

        self._event_builder = events.NewMessage(chats=self.chat_ref)
        self.client.add_event_handler(self._async_handle_message, self._event_builder)
        _LOGGER.info("Telegram provider connected for monitor %s", self.monitor_name)

    async def async_stop(self) -> None:
        if self.client is None:
            return
        if self._event_builder is not None:
            self.client.remove_event_handler(self._async_handle_message, self._event_builder)
        await self.client.disconnect()
        self.client = None

    async def _async_update_data(self) -> list[Alert]:
        """Maintain connection and populate the sensor with the latest message."""
        if self.client is None:
            raise UpdateFailed("Telegram client is not initialized")
        if not self.client.is_connected():
            try:
                await self.client.connect()
            except Exception as err:  # noqa: BLE001
                raise UpdateFailed(f"Could not reconnect Telegram: {err}") from err

        try:
            messages = await self.client.get_messages(self.chat_ref, limit=1)
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"Could not read Telegram chat {self.chat_ref}: {err}") from err

        alerts: list[Alert] = []
        for message in messages:
            text = message.raw_text or ""
            if not text.strip():
                continue
            alert = parse_telegram_message(
                text,
                chat_id=str(self.chat_ref),
                message_id=message.id,
                published=message.date.isoformat() if message.date else None,
            )
            alerts.append(alert)

        self.last_update_success_count = len(alerts)
        self.last_new_alerts_count = 0
        self.last_filtered_alerts_count = 0
        if alerts:
            self.last_alert = alerts[0]
            if self._matches_filters(alerts[0]):
                self.last_filtered_alert = alerts[0]
                if alerts[0].service:
                    self.last_filtered_alert_by_service[alerts[0].service] = alerts[0]
            if alerts[0].id not in self._seen_ids:
                self._seen_ids.add(alerts[0].id)
                await self._async_save_cache()
        return alerts

    async def _async_handle_message(self, event) -> None:
        text = event.raw_text or ""
        if not text.strip():
            return

        message = event.message
        alert = parse_telegram_message(
            text,
            chat_id=str(self.chat_ref),
            message_id=message.id,
            published=message.date.isoformat() if message.date else None,
        )
        if alert.id in self._seen_ids:
            return

        self._seen_ids.add(alert.id)
        await self._async_save_cache()
        self.last_alert = alert
        self.last_new_alerts_count = 1
        self.last_filtered_alerts_count = 0
        self.last_update_success_count = 1

        feed_event_data = self._event_data(alert)
        self.hass.bus.async_fire(EVENT_FEED_ALERT, feed_event_data)

        if self._matches_filters(alert):
            self.last_filtered_alert = alert
            if alert.service:
                self.last_filtered_alert_by_service[alert.service] = alert
            self.last_filtered_alerts_count = 1
            self.last_monitor_event = self.monitor_event
            self.hass.bus.async_fire(EVENT_FILTERED_ALERT, feed_event_data)
            self.hass.bus.async_fire(EVENT_LEGACY_FILTERED_ALERT, feed_event_data)
            self.hass.bus.async_fire(self.monitor_event, feed_event_data)

        # Persist both duplicate cache and per-service last alerts.
        await self._async_save_cache()

        # Push the new state to sensor entities immediately.
        self.async_set_updated_data([alert])

    def _event_data(self, alert: Alert) -> dict[str, Any]:
        data = alert.as_event_data()
        data.update(
            {
                "provider": "telegram",
                "monitor_name": self.monitor_name,
                "monitor_id": self.entry.entry_id,
                "monitor_event": self.monitor_event,
                "telegram_chat": str(self.chat_ref),
            }
        )
        return data

    def _matches_filters(self, alert: Alert) -> bool:
        options = self.options
        raw_text = (alert.raw_text or "").lower()
        city = (alert.city or "").lower()
        service = (alert.service or "").lower()
        priority = (alert.priority or "").upper()

        cities = [str(c).lower() for c in options.get(CONF_CITIES, []) if c]
        services = [str(s).lower().strip() for s in options.get(CONF_SERVICES, []) if s]
        priorities = [str(p).upper().replace(" ", "") for p in options.get(CONF_PRIORITIES, []) if p]
        text_contains = [str(w).lower() for w in options.get(CONF_TEXT_CONTAINS, []) if w]
        exclude_words = [str(w).lower() for w in options.get(CONF_EXCLUDE_WORDS, []) if w]

        if exclude_words and any(word in raw_text for word in exclude_words):
            return False
        if cities and not any(c in city or c in raw_text for c in cities):
            return False
        if text_contains and not any(word in raw_text for word in text_contains):
            return False
        if services and service not in services:
            return False
        if priorities and priority not in priorities:
            return False
        return True
