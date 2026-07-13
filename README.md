# 🚨 P2000 Companion

Een Home Assistant-integratie voor Nederlandse P2000-meldingen via RSS-feeds.

## Nieuw in v1.1: monitorprofielen

Een **monitorprofiel** is een volledig door de gebruiker ingestelde combinatie van feeds en filters. Voeg P2000 Companion opnieuw toe voor ieder extra profiel.

Voorbeelden:

- **Westland Ambulance** — Haaglanden, ambulance, P1/P2, Honselersdijk/Naaldwijk/De Lier
- **MMT Honselersdijk** — landelijke feed, dienst `mmt`, tekst bevat `Honselersdijk`
- **Brandweer Haaglanden** — Haaglanden, dienst `fire`, P1/P2

Elk profiel krijgt een eigen Home Assistant-apparaat, eigen sensoren en een eigen event.

## Installeren via HACS

1. Voeg deze repository als aangepaste HACS-integratie toe.
2. Installeer P2000 Companion en herstart Home Assistant.
3. Ga naar **Instellingen → Apparaten & diensten → Integratie toevoegen → P2000 Companion**.
4. Maak je eerste monitor.
5. Kies opnieuw **Integratie toevoegen → P2000 Companion** om extra monitoren te maken.

## Instellingen per monitor

- Naam van monitor
- Eén of meer kommagescheiden RSS-feeds
- Plaatsen
- Diensten: `ambulance`, `fire`, `police`, `mmt`, `lifeboat`
- Prioriteiten: `P1`, `P2`, `P3`, `B1`, `B2`
- Tekst bevat — een match op één van de ingevulde termen is voldoende
- Woorden uitsluiten
- Verversinterval

## Events

Voor iedere nieuwe feedmelding:

```text
p2000_feed_alert
```

Voor iedere passende melding:

```text
p2000_filtered_alert
p2000_new_alert
```

Daarnaast krijgt iedere monitor een eigen event. Een monitor met de naam `MMT Honselersdijk` maakt:

```text
p2000_monitor_mmt_honselersdijk
```

De exacte eventnaam staat als attribuut `monitor_event` op de sensoren.

### Voorbeeldautomatisering zonder extra voorwaarden

```yaml
alias: MMT Honselersdijk
triggers:
  - trigger: event
    event_type: p2000_monitor_mmt_honselersdijk
actions:
  - action: notify.pushover
    data:
      title: "🚁 MMT-melding"
      message: "{{ trigger.event.data.summary }}"
mode: queued
max: 10
```

`mode: queued` zorgt dat meerdere gelijktijdige meldingen na elkaar worden afgehandeld.

## Sensoren

Ieder profiel maakt twee sensoren onder een eigen apparaat. De entiteits-ID's worden door Home Assistant afgeleid van de profielnaam en kunnen in de UI worden aangepast.

Attributen bevatten onder andere:

- `monitor_name`
- `monitor_id`
- `monitor_event`
- `summary`
- `city`
- `service`
- `priority`
- `source_feed_url`
- aantallen nieuwe en gefilterde meldingen

## Voorbeeldfeeds

Haaglanden:

```text
https://alarmeringen.nl/feeds/region/haaglanden.rss
```

Landelijk:

```text
https://alarmeringen.nl/feeds/all.rss
```

## Lovelace Incident Card

Version 1.2.0 includes a bundled dashboard card for displaying the last feed or filtered alert of any monitor profile.

### Add the JavaScript resource once

Go to:

**Settings → Dashboards → Resources → Add resource**

Use:

```text
/p2000_companion/p2000-companion-card.js
```

Resource type:

```text
JavaScript Module
```

Restart Home Assistant and refresh the browser. The card then appears in the dashboard card picker as **P2000 Companion Incident Card**.

### Example YAML

```yaml
type: custom:p2000-companion-card
entity: sensor.mmt_honselersdijk_laatste_gefilterde_melding
title: MMT Honselersdijk
compact: false
show_link: true
show_raw: false
```

The visual card editor lets you choose the entity and presentation options without editing YAML.

## Upgrading from 1.0 or 1.1

Version 1.2.1 automatically migrates existing configuration entries to the monitor-profile format. Your feed URLs and filters are retained; removing and re-adding the integration is not required.
