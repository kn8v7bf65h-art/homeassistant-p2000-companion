# P2000 Companion

Home Assistant custom integration for P2000 RSS feeds.

## v0.3.1 highlights

- Supports multiple RSS feeds in one integration entry.
- The `feed_url` field now accepts a comma-separated list, for example:
  - `https://alarmeringen.nl/feeds/region/haaglanden.rss`
  - `https://alarmeringen.nl/feeds/all.rss`
- Adds `text_contains` filtering for cases where the location is only present in the raw text.
- Continues to fire one event per new alert:
  - `p2000_feed_alert` for every new alert
  - `p2000_filtered_alert` for alerts matching your filters
  - `p2000_new_alert` remains as legacy alias
- Keeps the sensors:
  - `sensor.p2000_last_feed_alert`
  - `sensor.p2000_last_filtered_alert`

## Example: Haaglanden + national MMT feed

Add both feeds in the Feed URL field, comma-separated:

```text
https://alarmeringen.nl/feeds/region/haaglanden.rss, https://alarmeringen.nl/feeds/all.rss
```

Filter examples:

```text
Cities:
Honselersdijk, Naaldwijk, De Lier

Services:
ambulance, fire, police, mmt

Priorities:
P1, P2, B1, B2

Text contains:
Honselersdijk, Naaldwijk, De Lier
```

Use `text_contains` when the source feed does not expose a clean city field but the place name appears in the alert text.

## Events

Automation trigger for filtered alerts:

```yaml
triggers:
  - trigger: event
    event_type: p2000_filtered_alert
```

Use the summary:

```jinja
{{ trigger.event.data.summary }}
```


## v0.3.1
This release fixes duplicate events when the same P2000 alert is present in both a regional feed and the national feed.


## v0.3.2
Deze versie voorkomt dat dezelfde melding opnieuw events afvuurt wanneer de RSS-feed de melding na enkele minuten opnieuw publiceert met gewijzigde timestamp of trackingmetadata.
