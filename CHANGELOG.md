# Changelog

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
