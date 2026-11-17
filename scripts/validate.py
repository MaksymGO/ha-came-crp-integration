"""Validate release version metadata and translation key parity."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "came_crp"


def _keys(value: dict, prefix: str = "") -> set[str]:
    """Flatten nested translation paths for parity comparison."""
    return {
        item
        for key, child in value.items()
        for item in (
            _keys(child, f"{prefix}{key}.") if isinstance(child, dict) else {f"{prefix}{key}"}
        )
    }


def main() -> None:
    """Check that all release metadata reports the same version."""
    version = json.loads((COMPONENT / "manifest.json").read_text(encoding="utf-8"))["version"]
    manifest_version = json.loads(
        (ROOT / ".release-please-manifest.json").read_text(encoding="utf-8")
    )["."]
    if version != (ROOT / "version.txt").read_text(encoding="utf-8").strip():
        raise ValueError("version.txt and integration manifest versions differ")
    if version != manifest_version:
        raise ValueError("Release Please manifest and integration manifest versions differ")

    strings = json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8"))
    expected_keys = _keys(strings)
    for path in (COMPONENT / "translations").glob("*.json"):
        translation_keys = _keys(json.loads(path.read_text(encoding="utf-8")))
        if translation_keys != expected_keys:
            raise ValueError(f"Translation keys differ in {path.name}")
    print(f"Release metadata and translations valid ({version})")


if __name__ == "__main__":
    main()
