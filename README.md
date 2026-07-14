# P2000 Companion

Home Assistant-integratie voor Nederlandse P2000-meldingen via **RSS** en vanaf v2.1.0 ook realtime via **Telegram/Telethon**. Monitorprofielen leveren sensoren, algemene events en een eigen event per monitor.

## Nieuw in 2.1.0: Telegram-provider

Bij het toevoegen van een monitor kies je nu tussen:

- **RSS-feed** — periodiek ophalen van een of meer feeds;
- **Telegram via Telethon** — realtime meelezen met een Telegram-groep of -kanaal waartoe jouw eigen account toegang heeft.

De gebruiker vult tijdens de installatie zelf in:

- Telegram API ID;
- Telegram API hash;
- telefoonnummer inclusief landcode;
- chat-ID, bijvoorbeeld `-1001661223938`, of een openbare gebruikersnaam;
- de eenmalige Telegram-inlogcode;
- eventueel het Telegram 2FA-wachtwoord.

Er staan **geen Telegram API-gegevens hardcoded in de integratie**. De gegenereerde StringSession wordt lokaal opgeslagen in de Home Assistant config-entry. Behandel je Home Assistant-back-ups daarom als vertrouwelijk: de sessie vertegenwoordigt toegang tot je Telegram-account.

## Telegram API-gegevens aanmaken

1. Meld je aan op `my.telegram.org` met je Telegram-account.
2. Open **API development tools**.
3. Maak een applicatie aan.
4. Noteer het API ID en de API hash.
5. Voeg in Home Assistant een nieuwe P2000 Companion-monitor toe en kies **Telegram via Telethon**.

Gebruik Telethon alleen voor groepen/kanalen waartoe je rechtmatig toegang hebt en respecteer de regels van de beheerder.

## Functies

- RSS- en Telegram-provider naast elkaar
- Realtime Telegram `NewMessage`-verwerking
- Zelf aan te maken monitor-/filterprofielen
- Filters op plaats, dienst, prioriteit, tekst en uitsluitwoorden
- Diensten: ambulance, brandweer, politie, MMT/Lifeliner en KNRM
- Prioriteiten: P1, P2, P3, B1 en B2
- Eén event per nieuwe melding
- Persistente deduplicatie
- Eigen event per monitorprofiel
- Optionele RSS-feedmelding-sensor; standaard alleen de gefilterde sensor
- Twee ingebouwde Lovelace-kaarten

## Installatie via HACS

1. Voeg deze repository als aangepaste HACS-repository toe met categorie **Integration**.
2. Installeer P2000 Companion.
3. Herstart Home Assistant.
4. Voeg een monitor toe via **Instellingen → Apparaten & diensten → Integratie toevoegen → P2000 Companion**.
5. Kies **RSS-feed** of **Telegram via Telethon**.

Telethon wordt als vastgepinde Python-dependency automatisch door Home Assistant geïnstalleerd.

## Telegram-monitor aanpassen

Via **Configureren** kun je de chat-ID en filters wijzigen. API-gegevens en de sessie blijven behouden. Wanneer je van Telegram-account of API-applicatie wilt wisselen, verwijder je de monitor en voeg je hem opnieuw toe.

## Sensor en events

Een Telegram-monitor maakt standaard één sensor aan:

```text
sensor.<monitornaam>_laatste_gefilterde_melding
```

Algemene events:

```text
p2000_feed_alert
p2000_filtered_alert
```

Profielspecifiek event, bijvoorbeeld:

```text
p2000_monitor_live_p2000_honselersdijk
```

De eventdata bevatten onder meer `provider: telegram`, `summary`, `raw_text`, `service`, `priority`, `city`, `monitor_name` en `telegram_chat`.

## Voorbeeldautomatisering

```yaml
alias: Telegram P2000 Honselersdijk
triggers:
  - trigger: event
    event_type: p2000_monitor_live_p2000_honselersdijk
actions:
  - action: notify.pushover
    data:
      title: "🚨 P2000 Telegram"
      message: "{{ trigger.event.data.summary }}"
mode: queued
max: 10
```

## Dashboardkaarten

Na installatie en herstart zijn beschikbaar:

- **P2000 Incident Card**
- **P2000 Monitorenkaart**

Handmatige resource-fallback:

```text
/p2000_companion/p2000-companion-card.js
```

Type: **JavaScript-module**.

## Licentie

MIT
