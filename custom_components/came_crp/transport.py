"""Serialx stream transport for local UARTs, raw TCP bridges and ESPHome proxies."""

from __future__ import annotations

from typing import Any

import serialx


class CRPTransport:
    """Thin connection wrapper; serialx dispatches device URLs by scheme."""

    def __init__(self, url: str, baudrate: int) -> None:
        self.url = url
        self.baudrate = baudrate
        self.reader: Any | None = None
        self.writer: Any | None = None

    async def async_connect(self) -> None:
        self.reader, self.writer = await serialx.open_serial_connection(
            self.url, baudrate=self.baudrate, bytesize=8,
            parity=serialx.Parity.NONE, stopbits=serialx.StopBits.ONE
        )

    async def async_write(self, data: bytes) -> None:
        if self.writer is None:
            raise ConnectionError("CRP transport is not connected")
        self.writer.write(data)
        await self.writer.drain()

    async def async_read(self, size: int = 256) -> bytes:
        if self.reader is None:
            raise ConnectionError("CRP transport is not connected")
        return await self.reader.read(size)

    async def async_close(self) -> None:
        if self.writer is not None:
            self.writer.close()
            try:
                await self.writer.wait_closed()
            except (OSError, AttributeError):
                pass
        self.reader = self.writer = None
