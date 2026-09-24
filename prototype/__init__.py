"""Prototype package for Neron."""

from pathlib import Path

_GOLDEN_NAME = "golden_01"


def run() -> str:
    """Return the golden output label and persist it to outputs/."""
    output = _GOLDEN_NAME
    output_dir = Path("outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "latest.txt").write_text(f"{output}\n", encoding="utf-8")
    return output
