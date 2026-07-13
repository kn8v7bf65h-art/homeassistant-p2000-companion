# Changelog

## v1.0.0 — Eerste stabiele release

P2000 Companion is nu klaar als eerste stabiele publieke release voor Home Assistant en HACS.

### Functionaliteit

- Ondersteuning voor meerdere P2000 RSS-feeds binnen één integratie.
- Eén `p2000_feed_alert`-event per nieuwe feedmelding.
- Eén `p2000_filtered_alert`-event per melding die aan de ingestelde filters voldoet.
- Legacy-event `p2000_new_alert` blijft beschikbaar voor bestaande automatiseringen.
- Sensoren voor de laatste feedmelding en de laatste gefilterde melding.
- Filtering op plaats, dienst, prioriteit en tekstinhoud.
- Genormaliseerde diensten: `ambulance`, `fire`, `police`, `mmt` en `lifeboat`.
- Genormaliseerde prioriteiten, waaronder `A1`, `A2`, `P 1`, `P 2`, `PRIO 1`, `PRIO 2`, `B1` en `B2`.
- Persistente deduplicatie om herhaalde events na feedupdates of herstarts te voorkomen.
- Configuratie en opties via Home Assistant **Apparaten & diensten**.
- HACS-ondersteuning, branding en GitHub-validatie via HACS en Hassfest.

## v0.3.3

- Branding toegevoegd voor Home Assistant en HACS.
- GitHub Actions toegevoegd voor HACS- en Hassfest-validatie.
- Manifestversie gelijkgetrokken met de release.
- CONTRIBUTING- en MIT-licentiebestanden toegevoegd.

## v0.3.2

- Verbeterde deduplicatie op basis van de stabiele detailpagina-link.
- Trackingparameters en gewijzigde publicatietijden veroorzaken geen dubbele events meer.

## v0.3.1

- Deduplicatie verbeterd voor dezelfde melding in meerdere feeds.
