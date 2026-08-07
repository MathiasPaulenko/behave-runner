"""Utility functions for behave-runner."""

from __future__ import annotations

import os
import webbrowser
from pathlib import Path


def find_project_root(start: Path | None = None) -> Path:
    """Find project root by looking for pyproject.toml."""
    current = start or Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    return Path.cwd()


def open_in_browser(url: str) -> None:
    """Open a URL in the default browser.

    Set `BEHAVE_RUNNER_NO_BROWSER=1` to skip opening the browser.
    """
    if os.environ.get("BEHAVE_RUNNER_NO_BROWSER", "").lower() in ("1", "true", "yes"):
        return
    webbrowser.open(url)
