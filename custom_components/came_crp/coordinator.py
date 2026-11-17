"""Polling and diagnostic state for a CAME CRP controller."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    ATTR_INVALID_FRAMES,
    ATTR_LAST_COMMANDS,
    ATTR_LAST_RX,
    ATTR_LAST_TX,
    ATTR_VALID_FRAMES,
    CONF_BAUDRATE,
    CONF_DEVICE_ADDRESS,
    DEFAULT_ADDRESS,
    DOMAIN,
    SCAN_INTERVAL,
)
from .models import PROFILES, detect_profile, information_signature
from .protocol import CRPError, CRPFrame, decode_frame, encode_request, split_frames
from .transport import CRPTransport


class CAMECRPCoordinator(DataUpdateCoordinator[dict[str, object]]):
    """Own the serial stream and issue conservative CRP read-state requests."""

    def __init__(self, hass: HomeAssistant, config: dict[str, object]) -> None:
        super().__init__(
            hass, logger=logging.getLogger(__name__), name=DOMAIN, update_interval=SCAN_INTERVAL
        )
        self.config = config
        self.transport = CRPTransport(str(config["transport_url"]), int(config[CONF_BAUDRATE]))
        self.address = int(config.get(CONF_DEVICE_ADDRESS, DEFAULT_ADDRESS))
        self.model_key = str(config.get("model", "auto"))
        self.model_name = PROFILES.get(self.model_key.lower(), PROFILES["generic"]).name
        if (
            self.model_key.lower() not in {"auto", "generic"}
            and self.model_key.lower() not in PROFILES
        ):
            self.model_name = self.model_key
        self.info_raw: str | None = None
        self.info_signature: str | None = None
        self.counter = 0
        self._buffer = bytearray()
        self._rx_frames: list[CRPFrame] = []
        self._transaction_lock = asyncio.Lock()
        self.valid_frames = 0
        self.invalid_frames = 0
        self.last_tx: str | None = None
        self.last_rx: str | None = None
        self.last_commands: list[str] = []
        self.last_seen: str | None = None

    async def async_connect(self) -> None:
        await self.transport.async_connect()
        if self.model_key == "auto":
            # SetUp Pro uses ReadState/INFORMATION (03 10) during discovery.
            frames = await self._async_request(b"\x03\x10")
            info = b"".join(command for frame in frames for command in frame.commands)
            self.info_raw = info.hex(" ").upper() if info else None
            self.info_signature = information_signature(info)
            detected = detect_profile(info)
            if detected.key != "generic":
                self.model_name = detected.name
            elif self.info_signature:
                self.model_name = f"Unmapped CRP ({self.info_signature})"

    async def async_shutdown(self) -> None:
        await self.transport.async_close()

    def _next_counter(self) -> int:
        value = self.counter
        self.counter = (self.counter + 1) & 0xFF
        return value

    async def _async_receive(self, timeout: float = 1.2) -> None:
        deadline = asyncio.get_running_loop().time() + timeout
        while asyncio.get_running_loop().time() < deadline:
            try:
                chunk = await asyncio.wait_for(self.transport.async_read(), timeout=0.2)
            except asyncio.TimeoutError:
                continue
            if not chunk:
                raise ConnectionError("Serial/TCP stream closed")
            for wire in split_frames(chunk, self._buffer):
                self.last_rx = wire.hex(" ").upper()
                try:
                    frame = decode_frame(wire)
                except CRPError:
                    self.invalid_frames += 1
                    continue
                self.valid_frames += 1
                self.last_seen = datetime.now(timezone.utc).isoformat()
                self.last_commands = [command.hex(" ").upper() for command in frame.commands]
                self._rx_frames.append(frame)

    async def _async_request(self, command: bytes) -> list[CRPFrame]:
        async with self._transaction_lock:
            self._rx_frames.clear()
            wire = encode_request(command, address=self.address, counter=self._next_counter())
            self.last_tx = wire.hex(" ").upper()
            await self.transport.async_write(wire)
            await self._async_receive()
            return list(self._rx_frames)

    async def _async_update_data(self) -> dict[str, object]:
        try:
            # ReadState(01) is an observed read-only operation. State bytes
            # remain raw until the ZBX7N mapping is confirmed against the gate.
            frames = await self._async_request(b"\x03\x01")
        except (OSError, ConnectionError, TimeoutError) as err:
            raise UpdateFailed(f"CRP communication failed: {err}") from err
        state_items = [item.hex(" ").upper() for frame in frames for item in frame.commands]
        return {
            "available": bool(frames),
            "state_raw": state_items[-1] if state_items else None,
            "last_seen": self.last_seen,
            ATTR_LAST_TX: self.last_tx,
            ATTR_LAST_RX: self.last_rx,
            ATTR_LAST_COMMANDS: self.last_commands,
            ATTR_VALID_FRAMES: self.valid_frames,
            ATTR_INVALID_FRAMES: self.invalid_frames,
            "address": self.address,
            "transport": self.config.get("transport_kind"),
            "baudrate": self.config[CONF_BAUDRATE],
            "model": self.model_name,
            "information_raw": self.info_raw,
            "information_signature": self.info_signature,
        }
