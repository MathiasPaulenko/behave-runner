"""Output directory management for reports."""

from __future__ import annotations

from pathlib import Path


def ensure_output_dir(path: Path) -> Path:
    """Create output directory if it doesn't exist. Return the path."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def find_latest_report(output_dir: Path) -> Path | None:
    """Find the most recently modified report file in output_dir."""
    if not output_dir.exists():
        return None
    files = sorted(
        output_dir.iterdir(),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    return files[0] if files else None


def clean_output_dir(path: Path) -> None:
    """Remove all contents of the output directory."""
    if not path.exists():
        return
    for item in path.iterdir():
        if item.is_dir():
            item.rmdir()
        else:
            item.unlink()
