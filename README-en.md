<p align="center">
  <img src="docs/bilder/logo.png" alt="RackView" width="220">
</p>

# RackView

[Deutsch](README.md) | English

Self-hosted documentation for server racks and home networks, packaged in one container.

## About this fork and its languages

This is the [jbrockmancas/rackview](https://github.com/jbrockmancas/rackview) fork of [Alexander Schubert's RackView](https://github.com/alexanderschubert/rackview). English/German interface support is being developed on the `eng-trans` branch. Translation coverage is incomplete, and the recent translation changes have not yet been build- or browser-tested. Some screens and server-generated messages still appear in German.

The language selector is available on the authentication screens. The translation structure supports additional languages through locale files in `frontend/src/i18n/locales/`. Internal identifiers, API/database fields and stored values are not translated; only their displayed labels are localized. User-entered content is preserved.

The published upstream image and Unraid App Catalog entry below belong to the original project. They do not contain this fork's unmerged translation work.

![RackView](docs/bilder/app-hell.png)

## Features

- Racks with front/rear views, configurable height, and devices mounted at the front, rear or full depth.
- Device faceplates with RJ45/SFP ports, colored connection states and power outlets.
- Locations for devices outside racks, such as access points, modems and cameras.
- Ports and cable connections, including cable type/length and per-port PoE.
- A network diagram generated from documented connections.
- IP-address and VLAN overviews.
- Power-outlet assignments on PDUs and UPS units.
- Purchase dates and warranty-expiration warnings.
- QR labels for A4 sheets or label printers; scanning opens the device in RackView.
- CSV, PDF and JSON exports, with JSON backup restoration.
- Accounts with separate workspaces, two-factor authentication and optional OIDC sign-in.
- Light/dark themes and scheduled database backups.

<table>
  <tr>
    <td><img src="docs/bilder/rack.png" alt="Rack front and rear views"></td>
    <td><img src="docs/bilder/geraete.png" alt="Device inventory"></td>
  </tr>
  <tr>
    <td><img src="docs/bilder/ports.png" alt="RJ45 and SFP+ port overview"></td>
    <td><img src="docs/bilder/netzplan.png" alt="Network diagram"></td>
  </tr>
  <tr>
    <td><img src="docs/bilder/steckplaetze.png" alt="Power-outlet assignments"></td>
    <td><img src="docs/bilder/etiketten.png" alt="QR labels"></td>
  </tr>
</table>

Screenshots are from the original documentation and may show the German interface.

## Installation

The application image includes the frontend, API and PostgreSQL. Persistent data is stored under `/config`.

### Published upstream release with Docker Compose

```yaml
services:
  rackview:
    image: ghcr.io/alexanderschubert/rackview:latest
    restart: unless-stopped
    ports:
      - "8080:80"
    volumes:
      - ./rackview:/config
    environment:
      TZ: Europe/Berlin
```

This runs the upstream release, not the translation branch.

### Translation-branch test deployment with Portainer/Compose

The following builds this fork's `eng-trans` branch. It uses port 8088 and the existing `rackview-test-data` volume.

```yaml
services:
  rackview:
    build:
      context: https://github.com/jbrockmancas/rackview.git#eng-trans
      dockerfile: docker/app/Dockerfile
    restart: unless-stopped
    ports:
      - "8088:80"
    volumes:
      - rackview-test-data:/config
    environment:
      TZ: America/Phoenix

volumes:
  rackview-test-data:
    external: true
    name: rackview-test-data
```

This example requires the named volume to exist already. Keep your existing Portainer stack and service identity when updating a test deployment, and retain its actual volume mapping. Do not delete or replace the data volume. Rebuild the image from the branch when testing newer source commits; restarting an existing container alone does not incorporate source changes.

### Unraid

For the published upstream release, open Apps, search for RackView, choose Install, review the port/data path, then Apply. The detailed [Unraid guide](unraid/README.md) is currently in German and also covers OIDC, external databases and troubleshooting. Its template and image references point to upstream, not this translation branch.

### First start

The first start takes longer while the database is initialized. Open `http://<server>:8080` for the upstream example, or `http://<server>:8088` for the translation test example, and create an account. The first account becomes administrator.

After creating the initial account, disable self-registration with `RACKVIEW_REGISTRATION=false` if appropriate, especially for an internet-accessible installation. Administrators can create further accounts in Settings.

## Persistent data

```text
/config/db              PostgreSQL database
/config/uploads         Uploaded device images
/config/backups         Scheduled database backups
/config/app.key         Application key
/config/db-passwort     Built-in database password
```

Keep `app.key` safe: it encrypts the two-factor secrets. Include it, the database and uploads in your data-path backups. Scheduled database dumps do not by themselves include device-image files.

## Updates

For a published-image Compose deployment, pull the newer image and redeploy using the same data mapping. In Unraid, use Check for Updates. Pin an upstream version tag instead of `latest` if required; see the upstream [container packages](https://github.com/alexanderschubert/rackview/pkgs/container/rackview).

For `eng-trans`, rebuild from this fork's branch and redeploy the existing stack. Database migrations run at startup by default. Back up persistent data before updates, and preserve the existing data path or named volume.

## Configuration

Settings are optional environment variables. Common options:

| Variable | Default | Purpose |
| --- | --- | --- |
| `TZ` | `Europe/Berlin` | Timezone for logs and backups |
| `RACKVIEW_REGISTRATION` | `true` | Self-registration on the sign-in page |
| `APP_URL` | Unset | Public URL when needed behind a reverse proxy |
| `BACKUP_SCHEDULE` | `0 3 * * *` | Backup schedule in cron format; empty disables it |
| `RETENTION_DAYS` | `14` | Backup retention in days |
| `DB_HOST` | Unset | Unset uses the built-in database; set uses external PostgreSQL |
| `OIDC_ENABLED` | `false` | Enable OIDC sign-in |

The full configuration table and OIDC/external-database instructions are in the German [Unraid guide](unraid/README.md#anhang-alle-einstellungen). These environment settings also apply to other Docker deployments.

## Development and support

- Translation-fork issues: [jbrockmancas/rackview/issues](https://github.com/jbrockmancas/rackview/issues).
- Original project: [alexanderschubert/rackview](https://github.com/alexanderschubert/rackview).
- Building and development: [ENTWICKLUNG.md](ENTWICKLUNG.md) (German).
- Translation notes: [frontend/TRANSLATIONS.md](frontend/TRANSLATIONS.md).
- Report security vulnerabilities privately rather than in a public issue; the upstream project links to [Security → Report a vulnerability](https://github.com/alexanderschubert/rackview/security/advisories/new).

Built with Laravel, Vue 3 and PostgreSQL.

## Project credits

The original RackView was created by Alexander Schubert for his homelab and tested in his own rack on Unraid. In the original project documentation, he credits Claude, Anthropic's AI assistant, for assistance writing much of the code and notes Claude's co-author attribution in commits. This fork adds ongoing multilingual-interface work.

## License

[MIT](LICENSE)
