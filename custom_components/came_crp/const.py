"""Constants for CAME CRP."""

from datetime import timedelta

DOMAIN = "came_crp"
PLATFORMS = ["sensor"]
SCAN_INTERVAL = timedelta(seconds=10)

CONF_DEVICE_ADDRESS = "device_address"
CONF_BAUDRATE = "baudrate"

DEFAULT_BAUDRATE = 38400
DEFAULT_ADDRESS = 1
DEFAULT_SOURCE_TYPE = 0x13
DEFAULT_SOURCE_ADDRESS = 0x05

ATTR_LAST_TX = "last_transmitted_frame"
ATTR_LAST_RX = "last_received_frame"
ATTR_VALID_FRAMES = "valid_frames"
ATTR_INVALID_FRAMES = "invalid_frames"
ATTR_LAST_COMMANDS = "last_commands"
