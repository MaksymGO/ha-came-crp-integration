"""Build a release archive containing only the installable integration."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "came_crp"


def build() -> Path:
    """Create a deterministic archive with the custom_components folder layout."""
    target = ROOT / "dist" / "came_crp.zip"
    target.parent.mkdir(exist_ok=True)
    with ZipFile(target, "w", ZIP_DEFLATED) as archive:
        for source in sorted(COMPONENT.rglob("*")):
            if source.is_file() and source.suffix in {".py", ".json", ".png", ".svg"}:
                archive.write(source, source.relative_to(ROOT))
    return target


if __name__ == "__main__":
    print(build())
