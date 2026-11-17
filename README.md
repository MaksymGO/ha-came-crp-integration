# CAME CRP Home Assistant integration

Custom Home Assistant integration for CAME gate controllers that communicate
over the CAME Remote Protocol (CRP).

![CAME+ CRP integration logo](custom_components/came_crp/brand/logo.png)

## Development status

The current `develop` branch starts with a transport and diagnostics
prototype. It supports local serial URLs, raw TCP serial bridges, and ESPHome
`serial_proxy` URLs through `serialx`. The first device profile is ZBX7N; unknown
controllers use the generic CRP path and expose raw identification/status data.

Gate movement and register writes are not implemented yet. The ZBX7N action
mapping still needs reliable validation on the physical controller. See
[`custom_components/came_crp/README.md`](custom_components/came_crp/README.md)
for installation, transport examples, and protocol limitations.

## Local installation

Copy `custom_components/came_crp` into the Home Assistant configuration's
`custom_components` directory, restart Home Assistant, then add **CAME CRP
Gate** from Settings → Devices & services.

## Release policy

Development happens on `develop`. Changes are merged into `main` through pull
requests. Use Conventional Commits for squash merge titles:

- `fix: ...` creates a patch release.
- `feat: ...` creates a minor release.
- `feat!: ...` or a `BREAKING CHANGE:` footer marks a breaking change.

Release Please opens a release pull request against `main`, updating
`CHANGELOG.md`, `version.txt`, `.release-please-manifest.json`, and the version
in the integration manifest. Merging that release PR is the release approval
step; it creates a `vX.Y.Z` tag and GitHub Release with a ZIP containing the
installable integration. The starting version is `0.1.0`. Changes pushed to
`develop` do not release automatically.

Use the `develop` branch for manual installation during development. Use a
GitHub Release or HACS after the first release from `main`.

The integration artwork lives in `custom_components/came_crp/brand/` and is
served locally by Home Assistant 2026.3 and newer.
