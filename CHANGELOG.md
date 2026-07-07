# Changelog

## v0.3.0

- Added support for multiple RSS feeds in the existing `feed_url` option by accepting comma-separated URLs.
- Added `text_contains` filter for matching raw alert text.
- Added `source_feed_url` to alert event data and sensor attributes.
- Added `feed_urls` attribute to sensors.
- Kept one event per new feed item and one filtered event per matching item.

## v0.2.0

- Process all new RSS items per update.
- Fire one event per new alert.
- Add persistent seen-alert cache.
