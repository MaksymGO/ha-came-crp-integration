# CAME CRP for Home Assistant — prototype

The CAME logo and icon assets are in `brand/`. Home Assistant 2026.3 and newer
loads custom integration artwork from this folder.

This is the first integration scaffold, intended to live in the GitHub project
`MaksymGO/ha-came-crp-integration`. The linked GitHub repository was not
available to this workspace, so the files currently live under this research
workspace's `custom_components/came_crp/` directory.

## Current scope

- Shared CRP frame encoder/decoder for the researched `E0` / CRC-16/A001 frame
  variant, including C2/C3 escaping and streaming frame extraction.
- `serialx` stream transport: local serial device, raw TCP bridge (including
  EW11 or ESPHome `uart_tcp`), and ESPHome `serial_proxy` (`esphome://`).
- Address and baud-rate configuration, with 8 data bits, no parity and one stop
  bit as the current baseline.
- Startup INFORMATION query (`03 10`) when model auto-detection is selected,
  followed by read-only ReadState (`03 01`) polling.
- Diagnostic sensors expose raw replies and valid/invalid frame counts.
- ZBX7N is the first model profile. Other controllers can use the generic CRP
  transport while their information response, state enums, registers and
  actions are researched and added as model profiles.

Model detection uses the INFORMATION reply. An offline ZBX7N emulator returned
`03 00 10 01 04 ...`, so that class/board signature is recognized as a
**provisional ZBX7N candidate**. It has not yet been confirmed on multiple
physical controller models. Unknown signatures stay Generic CRP and are exposed
as raw bytes so model profiles can be added without changing the shared
transport or framing layer.

## Safety and limits

Gate motion commands are not implemented yet. The ZBX7N action command mapping
is known from the app serializer, but the action's effect has not been verified
reliably on the physical controller. This prototype does not write registers.

The ZBX7N state values in the XML are not yet mapped to the ReadState response
bytes, so the prototype deliberately presents state data as raw bytes instead
of claiming Open/Closed. CRP models may use different framing variants; the
current E0/CRC setting is not assumed universal.

## Transport URL examples

```text
/dev/serial/by-id/usb-...                       local serial
socket://192.168.1.10:4001                       raw TCP serial bridge
esphome://192.168.1.42:6053/?port_name=RS-485    ESPHome serial_proxy
```

For an ESPHome proxy, use `serialx[esphome]`, include the proxy port name in the
URL, and provide authentication in the URL query as supported by serialx. Raw
TCP transports do not change UART settings remotely; configure baud/framing on
the bridge or ESPHome YAML to match the controller.

`uart_tcp` and `tcp_uart` are different ESPHome components. The former exposes
a physical UART over TCP; the latter maps a TCP connection to a virtual UART.
Both can be used as raw TCP endpoints if their server/client roles are set up
accordingly.

## Installation for development

Copy `custom_components/came_crp` into the Home Assistant configuration's
`custom_components` directory, restart Home Assistant, then add **CAME CRP
Gate** from Settings → Devices & services.
