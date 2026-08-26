# 🚨 P2000 Companion

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?logo=home-assistant-community-store)](https://www.hacs.xyz/docs/faq/custom_repositories/)
[![Validate](https://github.com/kn8v7bf65h-art/homeassistant-p2000-companion/actions/workflows/validate.yml/badge.svg)](https://github.com/kn8v7bf65h-art/homeassistant-p2000-companion/actions/workflows/validate.yml)
[![GitHub Release](https://img.shields.io/github/v/release/kn8v7bf65h-art/homeassistant-p2000-companion)](https://github.com/kn8v7bf65h-art/homeassistant-p2000-companion/releases)
[![License](https://img.shields.io/github/license/kn8v7bf65h-art/homeassistant-p2000-companion)](LICENSE)

Receive, filter and automate Dutch **P2000 emergency alerts** directly inside Home Assistant.

P2000 Companion supports the official **P2000 Haaglanden API**, RSS and Telegram, plus local filtering, monitor-specific events, persistent deduplication and Lovelace cards.

---

# Providers

## ✅ P2000 Haaglanden API

Recommended for Haaglanden. The integration uses one combined request for all emergency services:

```text
https://p2000haaglanden.nl/api/v1/meldingen?limit=10
```

Default polling interval: **10 seconds**. This equals **8,640 requests per day**, below a 10,000 requests/day limit.

Configure:

- API key
- API URL (pre-filled)
- Scan interval (minimum 10 seconds)
- Cities
- Services
- Priorities
- Include/exclude text filters

The API key is stored in the Home Assistant config entry and is not exposed as a sensor attribute or event field.

Structured API data is preserved, including:

- official alert ID
- service type, icon, color and label
- original priority label
- parsed street, city and full location
- alert kind
- raw, formatted, Unix and relative time
- capcodes
- detail URL
- API generated timestamp

Existing internal service names (`ambulance`, `fire`, `police`, `mmt`, `lifeboat`) and normalized priorities (`P0`, `P1`, `P2`, `P3`, `B1`, `B2`) remain available for backwards compatibility.

## ✅ RSS provider

Receive alerts from RSS feeds such as Alarmeringen.nl, regional feeds or custom feeds.

## ✅ Telegram provider

Receive alerts from Telegram channels using Telethon, including private/public channels and real-time events.

---

# Multiple monitors

Create multiple monitor profiles, for example:

- Ambulance Haaglanden
- Brandweer Westland
- Politie Den Haag
- MMT Zuid-Holland

Each monitor can have its own provider, places, services, priorities and text filters.

---

# Filtering

Filter locally in Home Assistant by:

- City
- Service
- Priority
- Keywords
- Excluded keywords

Supported normalized priorities:

- P0
- P1
- P2
- P3
- B1
- B2

Supported services:

- Ambulance
- Brandweer
- Politie
- KNRM
- MMT

For the P2000 Haaglanden API the original API priority (for example `A1`, `A2`, `PRIO 1`) is additionally exposed as `priority_label`.

---

# Home Assistant events

Every monitor generates its own event, for example:

```text
p2000_monitor_ambulance_haaglanden
```

Generic compatibility events remain available:

```text
p2000_feed_alert
p2000_filtered_alert
p2000_new_alert
```

API event data can include:

```text
id
message
city
service
priority
url
service_type
service_icon
service_color
service_label
priority_label
kind
location_street
location_city
location_full
time_raw
time_formatted
time_unix
time_relative
capcodes
api_generated_at
```

---

# Sensors

Every monitor includes a latest filtered alert sensor plus dedicated latest-alert sensors per emergency service.

Optional providers can also expose the latest unfiltered feed/API alert.

API-backed sensor attributes include the same structured metadata as the events, so dashboard cards and automations can directly use API-provided icon, color, location and relative time.

---

# Lovelace cards

Included custom dashboard cards:

- Incident Card
- Monitors Card

The frontend resource is loaded automatically where supported. If manual registration is required, add:

```text
/p2000_companion/p2000-companion-card.js
```

as a JavaScript Module under **Settings → Dashboards → Resources**.

---

# Installation

## HACS

Add this repository as a Custom Repository with category **Integration**:

```text
https://github.com/kn8v7bf65h-art/homeassistant-p2000-companion
```

Install through HACS and restart Home Assistant.

Then go to:

**Settings → Devices & Services → Add Integration → P2000 Companion**

Choose one of:

- P2000 Haaglanden API
- RSS-feed
- Telegram via Telethon

---

# API provider example

Create a monitor using **P2000 Haaglanden API** and enter your API key. The default URL already requests the latest 10 alerts and the default scan interval is 10 seconds.

You can then select services and locally filter cities such as Honselersdijk, Naaldwijk or Poeldijk without additional API calls.

A matching event can be used directly in an automation:

```yaml
triggers:
  - trigger: event
    event_type: p2000_new_alert
conditions:
  - condition: template
    value_template: >
      {{ trigger.event.data.city == 'Honselersdijk' }}
actions:
  - action: notify.pushover
    data:
      title: >
        {{ trigger.event.data.service_icon or '🚨' }}
        {{ trigger.event.data.service_label or trigger.event.data.service }}
        {% if trigger.event.data.priority_label %}
          - {{ trigger.event.data.priority_label }}
        {% endif %}
      message: >-
        {{ trigger.event.data.message }}
        {% if trigger.event.data.location_full %}
        📍 {{ trigger.event.data.location_full }}
        {% endif %}
        {% if trigger.event.data.time_relative %}
        🕒 {{ trigger.event.data.time_relative }}
        {% endif %}
```

---

# Deduplication

P2000 Companion stores seen alert IDs in Home Assistant storage. For the API provider the official numeric API alert ID is used.

The API returns newest-first; if multiple alerts arrive between two polls, all unseen alerts in the returned set are emitted **oldest → newest**. On the first refresh existing API results are marked as seen so Home Assistant does not send a burst of old notifications after setup or restart.

---

# Troubleshooting

If the API monitor cannot update, verify:

- API key
- API URL
- Daily request allowance
- Internet connectivity from Home Assistant
- Home Assistant logs

For a 10,000 requests/day plan, keep the scan interval at **10 seconds or higher**. Ten seconds uses 8,640 requests/day.

---

# Contributing

Bug reports and feature requests are welcome. Please include the Home Assistant version, P2000 Companion version, provider and relevant logs.

---

# License

MIT License
