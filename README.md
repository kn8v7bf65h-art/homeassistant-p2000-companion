# 🚨 P2000 Companion

Een Home Assistant-integratie voor Nederlandse P2000-meldingen via RSS-feeds.

## Mogelijkheden

- Meerdere RSS-feeds tegelijk uitlezen.
- Eén event per nieuwe melding, ook wanneer meerdere meldingen in één feed-update verschijnen.
- Filteren op plaats, dienst, prioriteit en vrije tekst.
- Persistente deduplicatie van opnieuw gepubliceerde meldingen.
- Configureren via **Instellingen → Apparaten & diensten**.
- Installeren en bijwerken via HACS.

Ondersteunde genormaliseerde diensten:

- `ambulance`
- `fire`
- `police`
- `mmt`
- `lifeboat`

Ondersteunde prioriteitsnotaties omvatten onder meer `A1`, `A2`, `P1`, `P 1`, `PRIO 1`, `P2`, `P 2`, `PRIO 2`, `B1` en `B2`.

## Installeren via HACS

1. Open **HACS → Integraties**.
2. Open rechtsboven het menu en kies **Aangepaste repositories**.
3. Voeg toe:

   ```text
   https://github.com/kn8v7bf65h-art/homeassistant-p2000-companion
   ```

4. Kies categorie **Integration**.
5. Installeer **P2000 Companion**.
6. Herstart Home Assistant.
7. Voeg de integratie toe via **Instellingen → Apparaten & diensten → Integratie toevoegen**.

## Voorbeeldfeeds

Haaglanden:

```text
https://alarmeringen.nl/feeds/region/haaglanden.rss
```

Landelijk:

```text
https://alarmeringen.nl/feeds/all.rss
```

Meerdere feeds kunnen kommagescheiden worden ingevoerd:

```text
https://alarmeringen.nl/feeds/region/haaglanden.rss, https://alarmeringen.nl/feeds/all.rss
```

## Events

Voor iedere nieuwe melding uit de feed:

```text
p2000_feed_alert
```

Voor iedere melding die aan de ingestelde filters voldoet:

```text
p2000_filtered_alert
```

Het oudere event `p2000_new_alert` blijft als compatibiliteitsalias beschikbaar.

### Voorbeeldautomatisering

```yaml
alias: Ambulance P2000-melding
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
mode: queued
max: 10
```

`mode: queued` voorkomt dat gelijktijdig binnenkomende meldingen worden overgeslagen.

## Sensoren

De integratie maakt onder meer deze sensoren aan:

```text
sensor.p2000_last_feed_alert
sensor.p2000_last_filtered_alert
```

## Ontwikkeling en validatie

Bij iedere push of pull request draaien automatisch:

- HACS-validatie
- Home Assistant Hassfest-validatie

Zie [CHANGELOG.md](CHANGELOG.md) voor release-informatie en [CONTRIBUTING.md](CONTRIBUTING.md) voor bijdragen.
