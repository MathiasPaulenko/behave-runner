"""Utility functions for behave-runner."""

from __future__ import annotations

import contextlib
import logging
import os
import webbrowser
from pathlib import Path

logger = logging.getLogger(__name__)


def find_project_root(start: Path | None = None) -> Path:
    """Find project root by looking for pyproject.toml or behave.ini."""
    current = start if start is not None else Path.cwd()
    # A relative `start` would only walk its textual ancestors — resolve it
    # against cwd first. Absolute paths are left untouched.
    if not current.is_absolute():
        current = current.resolve()
    if current.is_file():
        current = current.parent
    for parent in [current, *current.parents]:
        if (parent / "pyproject.toml").exists() or (parent / "behave.ini").exists():
            return parent
    return Path.cwd()


def make_stdout_safe() -> None:
    """Reconfigure stdout to replace unencodable chars instead of crashing.

    Scenario names with emoji/CJK raise UnicodeEncodeError on legacy
    Windows consoles (cp1252) when printed directly.
    """
    import sys

    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:
        with contextlib.suppress(OSError, ValueError):
            reconfigure(errors="replace")


def open_in_browser(url: str) -> None:
    """Open a URL in the default browser.

    Set `BEHAVE_RUNNER_NO_BROWSER=1` to skip opening the browser.
    Browser launch failures (e.g. headless Linux) are logged, not raised.
    """
    if os.environ.get("BEHAVE_RUNNER_NO_BROWSER", "").lower() in ("1", "true", "yes"):
        return
    try:
        opened = webbrowser.open(url)
    except webbrowser.Error:
        opened = False
    if not opened:
        logger.warning("Could not open a browser for %s", url)
