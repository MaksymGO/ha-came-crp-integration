"""Model profiles kept separate from the shared CRP transport and framing."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelProfile:
    key: str
    name: str
    board_id: int | None = None
    # Register meanings are model-specific. Empty means we have no validated map.
    registers: dict[int, str] | None = None
    # Motion opcodes are deliberately absent until physically verified per model.
    motion_commands: dict[str, bytes] | None = None
    detection_tokens: tuple[bytes, ...] = ()


PROFILES: dict[str, ModelProfile] = {
    "generic": ModelProfile("generic", "Generic / auto-detect", detection_tokens=()),
    "zbx7n": ModelProfile(
        "zbx7n", "ZBX7N", board_id=4,
        registers={
            1: "enablestop", 2: "fotocx", 3: "fotocy", 5: "servicestest",
            6: "manpresent", 7: "commandmode27", 8: "commandmode23p",
            9: "french", 11: "encoder", 14: "typedevice", 18: "lamp",
            19: "tca", 20: "tca_ped", 21: "preflash", 30: "ralvelocity",
            34: "sensibility", 35: "sensibilityral", 36: "pedestriancourse",
            37: "openral", 38: "closeral", 48: "cue", 54: "direction",
            65: "rioout1", 66: "rioout2", 67: "rioout3", 68: "rioout4",
            71: "partialopen_time", 76: "decodetype", 77: "motortype",
        },
        detection_tokens=(b"ZBX7N", b"ZBX7"),
    ),
}


def detect_profile(data: bytes) -> ModelProfile:
    """Match known INFORMATION replies; otherwise preserve the generic profile.

    The first observed INFORMATION payload is `03 00 10 <class> <board>`.
    The (01, 04) ZBX7N association comes from the offline firmware emulator and
    is a candidate signature until confirmed on additional physical models.
    """
    upper = data.upper()
    for profile in PROFILES.values():
        if any(token in upper for token in profile.detection_tokens):
            return profile
    if len(data) >= 5 and data[:3] == b"\x03\x00\x10" and data[3:5] == b"\x01\x04":
        return PROFILES["zbx7n"]
    return PROFILES["generic"]


def information_signature(data: bytes) -> str | None:
    """Return the decoded class/board signature from an INFORMATION reply."""
    if len(data) >= 5 and data[:3] == b"\x03\x00\x10":
        return f"class_{data[3]:02X}_board_{data[4]:02X}"
    return None
