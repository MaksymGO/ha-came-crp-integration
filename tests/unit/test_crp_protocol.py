"""Offline unit tests for CRP framing and model identification."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load_module(name: str, path: Path):
    """Load an integration helper without importing Home Assistant runtime code."""
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


protocol = _load_module(
    "came_crp_protocol_under_test", ROOT / "custom_components/came_crp/protocol.py"
)
models = _load_module("came_crp_models_under_test", ROOT / "custom_components/came_crp/models.py")


def test_crc16_a001_known_vector() -> None:
    assert protocol.crc16_a001(b"123456789") == 0xBB3D


def test_encode_decode_request_round_trip() -> None:
    wire = protocol.encode_request(b"\x03\x10", address=1, counter=0)

    frame = protocol.decode_frame(wire)

    assert frame.flags == 0xE0
    assert frame.source_type == 0x13
    assert frame.source_address == 0x05
    assert frame.target_type == 0x01
    assert frame.target_address == 1
    assert frame.counter == 0
    assert frame.commands == (b"\x03\x10",)


def test_reserved_bytes_are_escaped_and_restored() -> None:
    command = bytes((0x10, 0xC2, 0xC3, 0xDB))

    wire = protocol.encode_request(command)
    frame = protocol.decode_frame(wire)

    assert b"\xdb\xd2" in wire
    assert b"\xdb\xd3" in wire
    assert b"\xdb\xdd" in wire
    assert frame.commands == (command,)


def test_stream_splitter_handles_noise_and_partial_frames() -> None:
    first = protocol.encode_request(b"\x00", counter=1)
    second = protocol.encode_request(b"\x03\x01", counter=2)
    buffer = bytearray()

    assert protocol.split_frames(b"noise" + first[:4], buffer) == []
    assert protocol.split_frames(first[4:] + second, buffer) == [first, second]
    assert not buffer


def test_invalid_header_checksum_is_rejected() -> None:
    wire = bytearray(protocol.encode_request(b"\x00"))
    wire[2] ^= 0x01

    try:
        protocol.decode_frame(bytes(wire))
    except protocol.CRPError as err:
        assert "header checksum" in str(err)
    else:
        raise AssertionError("Corrupted header was accepted")


def test_information_signature_recognizes_zbx7n_candidate() -> None:
    info = bytes.fromhex("03 00 10 01 04 00 00")

    assert models.information_signature(info) == "class_01_board_04"
    assert models.detect_profile(info).key == "zbx7n"


def test_unknown_information_keeps_generic_profile() -> None:
    info = bytes.fromhex("03 00 10 7F 55")

    assert models.information_signature(info) == "class_7F_board_55"
    assert models.detect_profile(info).key == "generic"


def test_home_assistant_brand_assets_have_supported_dimensions() -> None:
    brand = ROOT / "custom_components/came_crp/brand"
    for filename, expected in {
        "icon.png": (256, 256),
        "icon@2x.png": (512, 512),
        "logo.png": (820, 214),
        "logo@2x.png": (1640, 428),
    }.items():
        png = (brand / filename).read_bytes()
        assert png[:8] == b"\x89PNG\r\n\x1a\n"
        assert int.from_bytes(png[16:20], "big") == expected[0]
        assert int.from_bytes(png[20:24], "big") == expected[1]
