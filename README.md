# P2000 Companion

Custom Home Assistant integration for reading P2000 RSS feeds and firing events.

## Features

- Add via **Settings → Devices & services**
- RSS feed polling
- Always fires an event for every new feed item: `p2000_feed_alert`
- Fires a filtered event for matching alerts: `p2000_new_alert`
- Filters for cities, services, priorities and excluded words
- Normalizes priority formats like `A1`, `P 1`, `P1`, `PRIO 1` to `P1`

## Installation

Copy this folder into Home Assistant:

```text
/config/custom_components/p2000_companion
```

Restart Home Assistant.

Then add the integration:

```text
Settings → Devices & services → Add integration → P2000 Companion
```

Recommended feed for Haaglanden:

```text
https://alarmeringen.nl/feeds/region/haaglanden.rss
```

Example filters:

```text
Cities: Honselersdijk, Naaldwijk, De Lier
Services: ambulance, brandweer, politie
Priorities: P1, P2
Exclude words: test, oefening
```

## Events

### All feed alerts

```text
p2000_feed_alert
```

### Filtered alerts

```text
p2000_new_alert
```

Example automation:

```yaml
alias: P2000 Honselersdijk alarm
trigger:
  - platform: event
    event_type: p2000_new_alert
action:
  - service: notify.pushover
    data:
      title: "🚨 P2000 melding"
      message: "{{ trigger.event.data.title }}"
mode: single
```
