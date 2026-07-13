# P2000 Companion

Home Assistant-integratie voor Nederlandse P2000-meldingen via RSS-feeds, met zelf te beheren monitorprofielen, events, sensoren en twee meegeleverde dashboardkaarten.

## Nieuw in 2.0.0: minder systeemvervuiling

Per monitor wordt standaard alleen de sensor **Laatste gefilterde melding** aangemaakt. De vaak identieke sensor **Laatste feedmelding** is optioneel en kan per monitor worden ingeschakeld via **Instellingen → Apparaten & diensten → P2000 Companion → Configureren**.


## Functies

- Meerdere RSS-feeds per monitorprofiel
- Zelf aan te maken monitor-/filterprofielen
- Filters op plaats, dienst, prioriteit, tekst en uitsluitwoorden
- Diensten: ambulance, brandweer, politie, MMT/Lifeliner en KNRM
- Prioriteiten: P1, P2, P3, B1 en B2
- Eén event per nieuwe melding
- Persistente deduplicatie
- Eigen events per monitorprofiel
- Twee ingebouwde Lovelace-kaarten met visuele editor

## Installatie via HACS

1. Voeg deze repository als aangepaste HACS-repository toe met categorie **Integration**.
2. Installeer P2000 Companion.
3. Herstart Home Assistant.
4. Voeg één of meerdere monitorprofielen toe via **Instellingen → Apparaten & diensten → Integratie toevoegen → P2000 Companion**.

## Dashboardkaarten

Vanaf v1.3.0 registreert de integratie de kaarten automatisch. Herstart Home Assistant en ververs de browser volledig. Ga daarna naar:

**Dashboard → Bewerken → Kaart toevoegen**

Zoek naar:

- **P2000 Incident Card** — één uitgebreide melding
- **P2000 Monitorenkaart** — compact overzicht van meerdere monitorprofielen

### Handmatige resource fallback

Verschijnen de kaarten niet in de kaartkiezer, voeg dan onder **Instellingen → Dashboards → Resources** deze JavaScript-module toe:

```text
/p2000_companion/p2000-companion-card.js
```

Type: **JavaScript-module**. Ververs daarna de browsercache.

### Incident Card YAML

```yaml
type: custom:p2000-companion-card
entity: sensor.mmt_honselersdijk_laatste_gefilterde_melding
title: MMT Honselersdijk
compact: false
show_link: true
show_raw: false
show_statistics: true
```

### Monitorenkaart YAML

```yaml
type: custom:p2000-companion-monitors-card
title: P2000-monitoren
entities:
  - sensor.westland_ambulance_laatste_gefilterde_melding
  - sensor.brandweer_haaglanden_laatste_gefilterde_melding
  - sensor.mmt_honselersdijk_laatste_gefilterde_melding
show_empty: true
```

De exacte entiteitsnamen hangen af van de namen van je monitorprofielen.

## Events

Algemeen:

```text
p2000_feed_alert
p2000_filtered_alert
```

Per monitorprofiel ontstaat daarnaast een event zoals:

```text
p2000_monitor_mmt_honselersdijk
```

Voor meerdere snel opeenvolgende meldingen wordt in automatiseringen aanbevolen:

```yaml
mode: queued
max: 10
```

## Voorbeeldautomatisering

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

## Licentie

MIT

## Dienstfilters

Vanaf versie 2.0.0 worden diensten gekozen met selectievakjes in de configuratie en opties van ieder monitorprofiel. De getoonde namen zijn Nederlands; intern gebruikt de integratie de stabiele waarden `ambulance`, `fire`, `police`, `mmt` en `lifeboat`.
