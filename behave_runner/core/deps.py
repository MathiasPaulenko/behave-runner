"""Optional dependency checking with graceful degradation."""

from __future__ import annotations

import importlib

from rich.console import Console

console = Console()


def is_installed(package: str) -> bool:
    """Silently check if a package is installed."""
    try:
        importlib.import_module(package)
        return True
    except ImportError:
        return False


def check_optional(feature: str, package: str, flag: str) -> bool:
    """Check if an optional package is installed. Print warning if not."""
    if is_installed(package):
        return True
    console.print(
        f"[yellow]Warning: {flag} requires {package}. "
        f"Install with: pip install behave-runner[{feature}][/yellow]"
    )
    return False
