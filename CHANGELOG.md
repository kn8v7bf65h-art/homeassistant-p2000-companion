# Changelog

## v0.1.4
- Fixed missing `CONF_SCAN_INTERVAL` import in coordinator.
- Normalized service filters to stable internal values: `ambulance`, `fire`, `police`, `mmt`, `lifeboat`.
- Dutch service input such as `brandweer`, `politie`, and `traumaheli` is accepted and converted automatically.

# Changelog

## v0.1.3

- Fixed coordinator feed URL handling when changed from Options.
- Added `alerts_in_feed` attribute to sensors for easier testing.
- Cleaned release package by removing `__pycache__`.
- Improved README with HACS installation steps.

## v0.1.2

- Fixed OptionsFlow crash caused by assigning to read-only `config_entry`.

## v0.1.1

- Config-flow fixes.

## v0.1.0

- Initial UI-based integration version.
