"""UI configuration for serial, TCP and ESPHome serial proxy transports."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME

from .const import CONF_BAUDRATE, CONF_DEVICE_ADDRESS, DEFAULT_ADDRESS, DEFAULT_BAUDRATE, DOMAIN


class CAMECRPConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure one CAME CRP bus connection."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            url = user_input["transport_url"].strip()
            if not url:
                errors["transport_url"] = "required"
            else:
                await self.async_set_unique_id(f"{url}|{user_input[CONF_DEVICE_ADDRESS]}")
                self._abort_if_unique_id_configured()
                title = user_input.get(CONF_NAME) or "CAME CRP Gate"
                return self.async_create_entry(title=title, data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default="CAME CRP Gate"): str,
                vol.Required("transport_url", default="socket://10.21.30.50:6638"): str,
                vol.Required("transport_kind", default="tcp"): vol.In(
                    {
                        "serial": "Local serial port",
                        "tcp": "Raw TCP bridge (EW11 / uart_tcp)",
                        "esphome": "ESPHome serial_proxy URI",
                    }
                ),
                vol.Required("model", default="auto"): str,
                vol.Required(CONF_DEVICE_ADDRESS, default=DEFAULT_ADDRESS): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=254)
                ),
                vol.Required(CONF_BAUDRATE, default=DEFAULT_BAUDRATE): vol.In(
                    {9600: "9600", 19200: "19200", 38400: "38400", 57600: "57600", 115200: "115200"}
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
