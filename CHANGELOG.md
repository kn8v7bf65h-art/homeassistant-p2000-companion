# Changelog

## 1.2.1

### Fixed
- Added automatic config-entry migration from legacy version 1 entries to the version 2 monitor-profile format.
- Existing feed URLs, cities, services, priorities, text filters, exclusions and scan interval are preserved during migration.
- Prevents the Home Assistant error `Migration handler not found for entry P2000 Companion`.

## 1.2.0

### Lovelace dashboard card

- Added the bundled **P2000 Companion Incident Card**.
- Dynamic service icon and incident styling for ambulance, fire, police, MMT and KNRM.
- Displays summary, city, priority, publication time and monitor statistics.
- Optional compact layout, incident link and raw P2000 text.
- Includes a visual Lovelace card editor.
- Card is served locally by the integration at `/p2000_companion/p2000-companion-card.js`.

## 1.1.0

- User-created monitor/filter profiles.
- Each profile has its own feeds, filters, sensors and monitor-specific event.
- Existing general feed and filtered events remain available.

## 1.0.0

- First stable public release.
