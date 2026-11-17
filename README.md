# CAME CRP Home Assistant integration

Custom Home Assistant integration for CAME gate controllers that communicate
over the CAME Remote Protocol (CRP).

## Development status

The current `development` branch starts with a transport and diagnostics
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
