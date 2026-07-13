# Changelog

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
