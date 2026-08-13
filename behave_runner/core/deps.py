"""Optional dependency checking with graceful degradation."""

from __future__ import annotations

import importlib
import subprocess  # nosec B404

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


def run_external(cmd: list[str], tool_name: str, install_hint: str) -> int:
    """Run an external CLI tool via subprocess, handling common errors.

    Args:
        cmd: Command list to execute (passed to subprocess.run with shell=False).
        tool_name: Human-readable tool name for error messages.
        install_hint: Package name for the install instruction in error messages.

    Returns:
        The tool's exit code, or 2 if the tool is not found or raises OSError.
    """
    try:
        result = subprocess.run(cmd, check=False)  # noqa: S603  # nosec B603
        return result.returncode
    except FileNotFoundError:
        console.print(
            f"[red]Error: {tool_name} not found. Install with: pip install {install_hint}[/red]"
        )
        return 2
    except OSError as e:
        console.print(f"[red]Error running {tool_name}: {e}[/red]")
        return 2
