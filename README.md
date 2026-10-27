# iLink Light - Home Assistant Custom Component

> **This is a maintained fork of [donandren/ilink_light](https://github.com/donandren/ilink_light) with bug fixes for recent Home Assistant versions. Use this repository's URL when installing via HACS.**

A custom component for Home Assistant that replaces the iLink app, letting you control and automate iLink-compatible lights (commonly found on AliExpress) through Home Assistant.

![lamp](https://github.com/donandren/ilink_light/assets/13854631/ea0759da-33e3-4f00-8370-2b39f340b4d1)

## Features

- Bluetooth auto-discovery of nearby iLink lights
- Manual addition by MAC address
- Full light control: on/off, RGB color, brightness, color temperature

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=nikolaspadilla&repository=ilink_light&category=integration)

## Installation

1. Open HACS → Integrations → **+ Explore & Add Repositories**
2. Paste `https://github.com/nikolaspadilla/ilink_light` and click **Add**
3. Find **iLink Light**, install it, and restart Home Assistant

## Updating an existing installation

If you already installed this fork, use the normal **Update** action in HACS when a new version is offered, then restart Home Assistant. This repository currently publishes updates from its default branch; HACS may display a commit hash as the downloaded version.

The GitHub username changed, but this is the same repository. Earlier repository URLs currently redirect here. Use the current URL above for new installations and bookmarks. Do not uninstall the Home Assistant integration, delete its configuration, or re-add your lights just because the repository URL changed: the integration domain remains `ilink_light`, and this maintenance update changes no runtime code or device/entity identifiers.

If HACS has not offered the update yet, refresh the repository information and check again. For a manual installation, back up your configuration, replace only `custom_components/ilink_light` with the updated folder, and restart Home Assistant.

Installations tracking the original `donandren/ilink_light` repository do not automatically switch to this fork. The HACS button above selects this fork; it is not a mechanism to redirect another author's users.

See [CHANGELOG.md](CHANGELOG.md) for changes.

## Support

Found a bug? [Open an issue](https://github.com/nikolaspadilla/ilink_light/issues).

## Credits

Original integration by [donandren](https://github.com/donandren/ilink_light).

## Disclaimer

Not affiliated with or endorsed by the creators of the iLink app or Home Assistant. Use at your own risk.

## License

MIT — see [LICENSE](LICENSE) for details.
