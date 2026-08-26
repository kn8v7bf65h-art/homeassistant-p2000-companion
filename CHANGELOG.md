# Changelog

## 3.2.0

### API-only Lovelace kaarten

- Nieuwe **P2000 API Incident Card** voor één melding uit uitsluitend de officiële P2000 Haaglanden API-provider.
- Nieuwe **P2000 API Hulpdienstenkaart** met de laatste melding per hulpdienst uit één API-monitor.
- De kaarten accepteren alleen entiteiten met `provider: api`; RSS- en Telegram-entiteiten worden niet aangeboden.
- Het hulpdienstenoverzicht gebruikt alleen de aparte dienstsensoren met `service_filter`, zodat generieke sensors niet dubbel worden weergegeven.
- Ondersteuning voor API-velden zoals `service_icon`, `service_color`, `service_label`, `priority_label`, `location_full` en `time_relative`.
- De incidentkaart kan tonen of een dienst of locatie lokaal is gecorrigeerd door P2000 Companion.
- Optionele weergave van capcodes en een directe link naar de originele melding.
- Nieuwe kaarten zijn beschikbaar via `/p2000_companion/p2000-api-card.js`.
- Bestaande P2000 Incident Card en Monitorenkaart blijven ongewijzigd beschikbaar.

## 3.1.1

### API classificatie- en locatiecorrecties

- MMT-, Lifeliner- en traumahelimeldingen worden lokaal als **MMT** geclassificeerd wanneer de API ze als ambulance aanlevert.
- De oorspronkelijke API-classificatie blijft beschikbaar via `api_service_*` attributen.
- Persistente dienstcache wordt hersteld wanneer een eerder verkeerd geclassificeerde melding opnieuw wordt ingelezen.
- `'s-Gravenhage`, `s-Gravenhage` en `Den Haag` worden consistent genormaliseerd naar **Den Haag**.
- Wanneer de API geen stad uit de melding kan halen, gebruikt P2000 Companion een lokale fallback.
- Straatnamen zoals `Lozerlaan` worden lokaal uit de melding gehaald wanneer de API incidenttekst in `location_street` heeft opgenomen.
- De originele API-locatie blijft ter controle beschikbaar via `api_location_*` attributen.

## 3.1.0

### Officiële P2000 Haaglanden API-provider

- Nieuwe provider **P2000 Haaglanden API** naast RSS en Telegram.
- Eén gezamenlijke API-call voor alle diensten via `/api/v1/meldingen?limit=10`.
- Standaard polling iedere **10 seconden** (8.640 requests per dag).
- API-key wordt als wachtwoordveld in de Home Assistant config-entry opgeslagen en niet als sensorattribuut gepubliceerd.
- Plaats-, dienst-, prioriteit-, tekst- en uitsluitfilters blijven lokaal in Home Assistant werken.
- Deduplicatie gebruikt het officiële numerieke API-ID en verwerkt meerdere nieuwe meldingen tussen twee polls oudste → nieuwste.
- Gestructureerde API-data is beschikbaar in events en sensoren: diensttype, icoon, kleur, label, origineel prioriteitslabel, soort melding, straat, plaats, volledige locatie, raw/formatted/unix/relatieve tijd, capcodes en API generated_at.
- Bestaande genormaliseerde services (`ambulance`, `fire`, `police`, etc.) en prioriteiten (`P0`, `P1`, `P2`, ...) blijven behouden voor achterwaartse compatibiliteit.
- Bestaande events zoals `p2000_new_alert`, `p2000_filtered_alert` en monitor-specifieke events blijven werken.
- Config-entryversie verhoogd naar 5 en bestaande v4-installaties worden automatisch gemigreerd.

## 2.2.0

- Aparte persistente laatste-melding-sensoren per hulpdienst.
- Ambulance, brandweer, politie, MMT en KNRM behouden elk hun eigen laatste melding.
- Ondersteuning voor A0/P0/PRIO 0 als genormaliseerde prioriteit P0.
- Bestaande monitor-events en algemene sensoren blijven ongewijzigd.

## 2.1.0

### Telegram/Telethon-provider

- Nieuwe providerkeuze bij het toevoegen van een monitor: RSS of Telegram via Telethon.
- De gebruiker voert zelf API ID, API hash, telefoonnummer en chat-ID in; niets is hardcoded.
- Meertraps Telegram-aanmelding met inlogcode en optionele 2FA.
- Veilige lokale opslag als Telethon StringSession in de Home Assistant config-entry.
- Realtime verwerking van ieder nieuw Telegram-bericht via `events.NewMessage`.
- Telegram-berichten gebruiken dezelfde parser, filters, sensoren en monitor-events als RSS.
- Persistent onthouden van Telegram message-ID's om dubbele events te voorkomen.
- Telegram-chat en filters kunnen via de opties worden aangepast.
- Bestaande RSS-monitoren worden automatisch naar config-entryversie 4 gemigreerd.
- Telethon 1.44.0 als vastgepinde dependency toegevoegd.

## 2.0.0

### Minder dubbele entiteiten

- De sensor **Laatste feedmelding** is nu optioneel en staat standaard uit.
- Iedere monitor behoudt standaard alleen **Laatste gefilterde melding**.
- Bestaande feed-sensoren worden bij migratie door de integratie uitgeschakeld, tenzij de optie expliciet wordt ingeschakeld.
- Nieuwe optie in de monitorconfiguratie: **Laatste feedmelding-sensor aanmaken**.
- Bestaande monitoren, events en automatiseringen blijven behouden.
- Config-entry migratie bijgewerkt naar versie 3.

### Bestaande functies

- Zelf aan te maken monitorprofielen.
- Meerdere RSS-feeds per monitor.
- Dienst-, plaats-, prioriteit- en tekstfilters.
- Eén event per nieuwe melding.
- Profielspecifieke events.
- Persistente deduplicatie.
- P2000 Incident Card en Monitorenkaart.
