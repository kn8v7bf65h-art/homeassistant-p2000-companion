# Changelog

## v0.2.0

- Verwerkt nu alle nieuwe RSS-items per update, niet alleen de meest recente.
- Vuurt één `p2000_feed_alert` event af per nieuwe feedmelding.
- Vuurt één `p2000_filtered_alert` event af per nieuwe melding die aan de filters voldoet.
- Houdt een persistente cache met bekende meldingen bij in Home Assistant storage.
- Voorkomt daardoor dubbele events na een herstart.
- Sensorattributen toegevoegd:
  - `new_alerts_last_update`
  - `filtered_alerts_last_update`

## v0.1.5

- `B1` en `B2` prioriteiten toegevoegd.
- `sensor.p2000_last_feed_alert` en `sensor.p2000_last_filtered_alert` toegevoegd.
- Nieuw event: `p2000_filtered_alert`.
- Oude event `p2000_new_alert` blijft werken voor backwards compatibility.

## v0.1.4

- Fix voor `CONF_SCAN_INTERVAL is not defined`.
- Diensten genormaliseerd naar vaste interne waarden: `ambulance`, `fire`, `police`, `mmt`, `lifeboat`.

## v0.1.3

- Config-flow/options bugfixes.
- Feed URL aanpassen via opties.
- `alerts_in_feed` attribuut toegevoegd.
