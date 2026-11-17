"""CAME CRP framing helpers based on the ZBX7N firmware and captures.

The E0 / CRC16-A001 variant has worked with the researched ZBX7N, but CAME
devices may use other header variants. State value semantics are not decoded
here because they have not yet been confirmed against physical gate movement.
"""

from __future__ import annotations

from dataclasses import dataclass

START = 0xC2
END = 0xC3
ESC = 0xDB
ESCAPE = {0xC2: b"\xdb\xd2", 0xC3: b"\xdb\xd3", 0xDB: b"\xdb\xdd"}
UNESCAPE = {0xD2: 0xC2, 0xD3: 0xC3, 0xDD: 0xDB}


class CRPError(ValueError):
    """Invalid or incomplete CRP frame."""


@dataclass(frozen=True)
class CRPFrame:
    flags: int
    header_byte: int
    source_type: int
    source_address: int
    target_type: int
    target_address: int
    counter: int
    commands: tuple[bytes, ...]
    wire: bytes


def crc16_a001(data: bytes) -> int:
    """CRC-16/A001 used by the researched ZBX7N firmware (init 0, BE trailer)."""
    value = 0
    for byte in data:
        value ^= byte
        for _ in range(8):
            value = (value >> 1) ^ (0xA001 if value & 1 else 0)
    return value


def _wrap(raw: bytes) -> bytes:
    return bytes((START,)) + b"".join(ESCAPE.get(byte, bytes((byte,))) for byte in raw) + bytes((END,))


def encode_request(
    command: bytes,
    *,
    address: int = 1,
    counter: int = 1,
    source_type: int = 0x13,
    source_address: int = 0x05,
    target_type: int = 0x01,
    flags: int = 0xE0,
) -> bytes:
    """Encode a single-command address request using the validated E0 variant."""
    if not 1 <= address <= 254:
        raise ValueError("CRP address must be in 1..254")
    if not 0 <= counter <= 255:
        raise ValueError("CRP counter must be in 0..255")
    if not command or len(command) > 255:
        raise ValueError("CRP command must contain 1..255 bytes")
    item = bytes((len(command),)) + command
    header = bytes((flags, 0, source_type, source_address, target_type, address, counter))
    raw = header + bytes((-sum(header) & 0xFF, len(item))) + item
    raw += crc16_a001(raw).to_bytes(2, "big")
    return _wrap(raw)


def decode_frame(wire: bytes) -> CRPFrame:
    """Unescape and validate one complete CRP frame."""
    if len(wire) < 2 or wire[0] != START or wire[-1] != END:
        raise CRPError("Missing C2/C3 frame boundaries")
    raw = bytearray()
    escaped = False
    for byte in wire[1:-1]:
        if escaped:
            if byte not in UNESCAPE:
                raise CRPError("Invalid escaped byte")
            raw.append(UNESCAPE[byte])
            escaped = False
        elif byte == ESC:
            escaped = True
        elif byte in (START, END):
            raise CRPError("Unescaped frame delimiter")
        else:
            raw.append(byte)
    if escaped or len(raw) < 11:
        raise CRPError("Truncated frame")
    if sum(raw[:8]) & 0xFF:
        raise CRPError("Invalid header checksum")
    if crc16_a001(raw[:-2]) != int.from_bytes(raw[-2:], "big"):
        raise CRPError("Invalid frame CRC")
    if raw[8] != len(raw) - 11:
        raise CRPError("Invalid payload length")
    commands: list[bytes] = []
    pos, end = 9, len(raw) - 2
    while pos < end:
        size = raw[pos]
        pos += 1
        if size == 0 or pos + size > end:
            raise CRPError("Invalid command item length")
        commands.append(bytes(raw[pos : pos + size]))
        pos += size
    return CRPFrame(
        flags=raw[0], header_byte=raw[1], source_type=raw[2], source_address=raw[3],
        target_type=raw[4], target_address=raw[5], counter=raw[6],
        commands=tuple(commands), wire=wire,
    )


def split_frames(data: bytes, buffer: bytearray) -> list[bytes]:
    """Extract complete C2..C3 frames from an arbitrary stream chunk."""
    frames: list[bytes] = []
    for byte in data:
        if not buffer:
            if byte == START:
                buffer.append(byte)
            continue
        buffer.append(byte)
        if byte == END:
            frames.append(bytes(buffer))
            buffer.clear()
        elif byte == START and len(buffer) > 1:
            buffer[:] = bytes((START,))
        elif len(buffer) > 1024:
            buffer.clear()
    return frames
