# 2.2.0

- Aparte persistente laatste-melding-sensoren per hulpdienst.
- Ambulance, brandweer, politie, MMT en KNRM behouden elk hun eigen laatste melding.
- Ondersteuning voor A0/P0/PRIO 0 als genormaliseerde prioriteit P0.
- Bestaande monitor-events en algemene sensoren blijven ongewijzigd.

# Changelog

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
