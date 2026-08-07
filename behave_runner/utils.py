"""Utility functions for behave-runner."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def find_project_root(start: Path | None = None) -> Path:
    """Find project root by looking for pyproject.toml."""
    current = start or Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    return Path.cwd()


def open_in_browser(url: str) -> None:
    """Open a URL in the default browser."""
    if sys.platform == "win32":
        subprocess.run(["cmd", "/c", "start", url], check=False)  # noqa: S603, S607
    elif sys.platform == "darwin":
        subprocess.run(["open", url], check=False)  # noqa: S603
    else:
        subprocess.run(["xdg-open", url], check=False)  # noqa: S603
