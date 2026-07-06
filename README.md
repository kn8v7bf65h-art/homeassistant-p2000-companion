# P2000 Companion

Custom Home Assistant integratie voor P2000/RSS-meldingen.

## Features

- Leest een P2000 RSS-feed, standaard Haaglanden.
- Configuratie via **Instellingen → Apparaten & diensten**.
- Opties aanpassen zonder YAML.
- Parser voor o.a. `A1`, `A2`, `B1`, `B2`, `P 1`, `P 2`, `PRIO 1`, `PRIO 2`.
- Dienstnormalisatie:
  - `ambulance`
  - `fire`
  - `police`
  - `mmt`
  - `lifeboat`
- Events:
  - `p2000_feed_alert` voor iedere nieuwe feedmelding.
  - `p2000_filtered_alert` voor iedere nieuwe melding die aan jouw filters voldoet.
  - `p2000_new_alert` blijft bestaan als legacy alias van `p2000_filtered_alert`.
- Sensoren:
  - `sensor.p2000_last_feed_alert`
  - `sensor.p2000_last_filtered_alert`

## Belangrijk in v0.2.0

Vanaf v0.2.0 worden **alle nieuwe meldingen** verwerkt. Als er tijdens één feed-update drie nieuwe meldingen binnenkomen, worden er ook drie events afgevuurd.

De integratie bewaart bekende melding-ID's persistent in Home Assistant storage. Daardoor krijg je na een herstart niet opnieuw oude meldingen als event.

## Voorbeeld automation

```yaml
alias: P2000 ambulance gefilterd
triggers:
  - trigger: event
    event_type: p2000_filtered_alert
conditions:
  - condition: template
    value_template: "{{ trigger.event.data.service == 'ambulance' }}"
actions:
  - action: notify.pushover
    data:
      title: "🚑 Ambulance melding"
      message: "{{ trigger.event.data.summary }}"
mode: single
```

## Feed

Voor Haaglanden:

```text
https://alarmeringen.nl/feeds/region/haaglanden.rss
```

## HACS

Voeg deze repository toe als custom repository in HACS met categorie **Integration**.
