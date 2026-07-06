# P2000 Companion

Custom Home Assistant integration for reading P2000 RSS feeds and firing events.

## Features

- Add via **Settings → Devices & services**
- Change filters via **Configure / Options**
- RSS feed polling with one central listener
- Always fires an event for every new feed item: `p2000_feed_alert`
- Fires a filtered event for matching alerts: `p2000_new_alert`
- Filters for cities, services, priorities and excluded words
- Normalizes priority formats like `A1`, `P 1`, `P1`, `PRIO 1` to `P1`
- Creates two sensors:
  - `P2000 Last Feed Alert`
  - `P2000 Last Filtered Alert`

## Installation with HACS

1. In Home Assistant, open **HACS → Integrations**.
2. Open **⋮ → Custom repositories**.
3. Add your repository URL.
4. Category: **Integration**.
5. Install **P2000 Companion**.
6. Restart Home Assistant.
7. Add the integration via **Settings → Devices & services → Add integration → P2000 Companion**.

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

This event is fired for every new item in the RSS feed, even if it does not match your filters.

### Filtered alerts

```text
p2000_new_alert
```

This event is only fired when the alert matches your configured filters.

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

## Development notes

- Config-flow is enabled.
- Options-flow can update feed URL, places, services, priorities, exclude words and scan interval.
- The feed URL used by the coordinator now follows options changes after reload.


## v0.1.4

Bugfix: `CONF_SCAN_INTERVAL` import toegevoegd zodat setup niet meer crasht.

Diensten worden nu intern genormaliseerd naar vaste Engelse waarden:

- `ambulance`
- `fire`
- `police`
- `mmt`
- `lifeboat`

Nederlandse invoer zoals `brandweer`, `politie` en `traumaheli` wordt automatisch omgezet.
