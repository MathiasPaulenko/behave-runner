"""Output directory management for reports."""

from __future__ import annotations

import shutil
from pathlib import Path

from rich.console import Console

from behave_runner.utils import open_in_browser

console = Console()
err_console = Console(stderr=True)


def ensure_output_dir(path: Path) -> Path:
    """Create output directory if it doesn't exist. Return the path.

    Raises FileExistsError if the path exists but is not a directory.
    """
    if path.exists() and not path.is_dir():
        raise FileExistsError(f"Path {path} exists but is not a directory")
    path.mkdir(parents=True, exist_ok=True)
    return path


def find_latest_report(output_dir: Path) -> Path | None:
    """Find the most recently modified report file in output_dir."""
    if not output_dir.is_dir():
        return None
    try:
        entries = list(output_dir.iterdir())
    except OSError:
        return None
    candidates: list[tuple[float, Path]] = []
    for f in entries:
        try:
            if f.is_file():
                candidates.append((f.stat().st_mtime, f))
        except OSError:
            continue
    if not candidates:
        return None
    candidates.sort(key=lambda pair: pair[0], reverse=True)
    return candidates[0][1]


def clean_output_dir(path: Path) -> None:
    """Remove all contents of the output directory.

    Symlinks are unlinked rather than followed to prevent deleting files
    outside the output directory.
    """
    if not path.exists():
        return
    try:
        items = list(path.iterdir())
    except OSError:
        return
    for item in items:
        try:
            if item.is_symlink():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        except OSError:
            continue


def open_latest_report(output_dir: Path) -> bool:
    """Find and open the latest report in the browser.

    Returns True when a report was found and opened; False otherwise so
    callers can exit non-zero — "nothing to open" must not look like success.
    """
    report_file = find_latest_report(output_dir)
    if report_file is None:
        err_console.print("[yellow]No reports found.[/yellow]")
        return False
    console.print(f"[green]Opening: {report_file}[/green]")
    open_in_browser(report_file.resolve().as_uri())
    return True
