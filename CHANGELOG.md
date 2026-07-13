# Changelog

## v1.1.0 — Zelf te beheren monitorprofielen

- Gebruikers kunnen onbeperkt eigen monitor-/filterprofielen aanmaken door P2000 Companion meerdere keren toe te voegen.
- Elk profiel heeft een eigen naam, RSS-feed(s), plaatsen, diensten, prioriteiten, tekstfilter en uitsluitwoorden.
- Elk profiel verschijnt als een eigen Home Assistant-apparaat met twee sensoren:
  - `Laatste feedmelding`
  - `Laatste gefilterde melding`
- Iedere passende melding vuurt naast de algemene events een profielspecifiek event af:
  - `p2000_monitor_<profielnaam>`
- Algemene events bevatten nu ook `monitor_name`, `monitor_id` en `monitor_event`.
- Profielen kunnen via **Apparaten & diensten → Configureren** worden hernoemd en aangepast.
- Meerdere profielen mogen bewust dezelfde RSS-feed gebruiken.
- Bestaande v1.0-configuraties blijven werken; ontbrekende profielnamen vallen terug op de bestaande configuratietitel.

## v1.0.0 — Eerste stabiele release

- Meerdere RSS-feeds, events per nieuwe melding, filters, sensoren, persistente deduplicatie, HACS, branding en GitHub-validatie.
