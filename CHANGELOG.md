# Changelog

## 1.0.2 — 2026-10-27

- Use Home Assistant's recommended `bleak_retry_connector.establish_connection` helper and cached-service client instead of direct `BleakClient.connect()` calls.
- Initialize notifications/status after successful connections without relying on Bleak's deprecated boolean return value.
- Refresh the connectable device route for retries and reconnects; clear the connecting flag on failure or cancellation.
- Retain existing light configuration and device/entity identifiers.

## 1.0.1 — 2026-10-27

- Update repository, support, and code-owner references to `nikolaspadilla`.
- Add a one-click HACS repository link and instructions for existing installs.
- Preserve the `ilink_light` integration domain, configuration, and device/entity identifiers; no runtime code changes.

Updates are currently distributed from the default branch through HACS, rather than GitHub releases.

## 1.0.0

- Update the integration for modern Home Assistant APIs.
- Fix color-temperature and type-hint errors.
- Add availability tracking for failed Bluetooth connections.

