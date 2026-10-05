"""Optional dependency checking with graceful degradation."""

from __future__ import annotations

import importlib
import subprocess  # nosec B404
import sys
from pathlib import Path

from rich.console import Console

console = Console()


def resolve_executable(name: str) -> str:
    """Resolve a console script name to a path next to the current interpreter.

    External behave-* tools are checked for via ``importlib`` but invoked as
    console scripts. When the interpreter's Scripts/bin directory is not on
    ``PATH`` (venv not activated, ``pip install --user``, etc.), the package
    is importable but the script cannot be found by name. Prefer the script
    located next to ``sys.executable``; fall back to the bare name so PATH
    resolution still works.
    """
    exe_dir = Path(sys.executable).parent
    candidates = [
        exe_dir / name,
        exe_dir / f"{name}.exe",
        exe_dir / "Scripts" / name,
        exe_dir / "Scripts" / f"{name}.exe",
        exe_dir / "bin" / name,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return name


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
    resolved = [resolve_executable(cmd[0]), *cmd[1:]]
    try:
        result = subprocess.run(resolved, check=False)  # noqa: S603  # nosec B603
        return result.returncode
    except FileNotFoundError:
        console.print(
            f"[red]Error: {tool_name} not found. Install with: pip install {install_hint}[/red]"
        )
        return 2
    except OSError as e:
        console.print(f"[red]Error running {tool_name}: {e}[/red]")
        return 2
