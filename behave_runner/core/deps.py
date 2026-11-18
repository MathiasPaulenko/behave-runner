"""Optional dependency checking with graceful degradation."""

from __future__ import annotations

import importlib.util
import subprocess  # nosec B404
import sys
import sysconfig
from pathlib import Path

from rich.console import Console

console = Console(stderr=True)


def _user_scripts_dir() -> Path | None:
    """Return the per-user scripts directory for the running interpreter.

    ``pip install --user`` places console scripts in
    ``%APPDATA%\\Python\\PythonXY\\Scripts`` (Windows) or ``~/.local/bin``
    (POSIX), which is not next to ``sys.executable`` and often not on PATH.
    """
    scheme = "nt_user" if sys.platform == "win32" else "posix_user"
    try:
        scripts = sysconfig.get_path("scripts", scheme)
    except (KeyError, AttributeError, TypeError):
        return None
    return Path(scripts) if scripts else None


def resolve_executable(name: str) -> str:
    """Resolve a console script name to a path next to the current interpreter.

    External behave-* tools are checked for via ``importlib`` but invoked as
    console scripts. When the interpreter's Scripts/bin directory is not on
    ``PATH`` (venv not activated, ``pip install --user``, etc.), the package
    is importable but the script cannot be found by name. Prefer the script
    located next to ``sys.executable``, then the per-user scripts directory;
    fall back to the bare name so PATH resolution still works.
    """
    exe_dir = Path(sys.executable).parent
    candidates = [
        exe_dir / name,
        exe_dir / f"{name}.exe",
        exe_dir / "Scripts" / name,
        exe_dir / "Scripts" / f"{name}.exe",
        exe_dir / "bin" / name,
    ]
    user_scripts = _user_scripts_dir()
    if user_scripts is not None:
        candidates.extend(
            [
                user_scripts / name,
                user_scripts / f"{name}.exe",
            ]
        )
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return name


def is_installed(package: str) -> bool:
    """Silently check if a package is installed.

    Uses ``importlib.util.find_spec`` so the check does not execute module
    code: importing an optional package may pull in heavy transitive
    dependencies or trigger side effects just to answer "is it installed?".
    """
    try:
        return importlib.util.find_spec(package) is not None
    except (ImportError, ValueError, AttributeError, TypeError):
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
    if not cmd:
        console.print(f"[red]Error: no command provided for {tool_name}.[/red]")
        return 2
    resolved = [resolve_executable(cmd[0]), *cmd[1:]]
    try:
        result = subprocess.run(resolved, check=False)  # noqa: S603  # nosec B603
        return result.returncode
    except FileNotFoundError:
        if is_installed(install_hint.replace("-", "_")):
            # Package is importable but its console script is missing from
            # every known Scripts/bin dir and PATH — broken install, not
            # a missing dependency.
            console.print(
                f"[red]Error: {tool_name} console script not found. "
                f"Reinstall with: pip install --force-reinstall {install_hint}[/red]"
            )
        else:
            console.print(
                f"[red]Error: {tool_name} not found. Install with: pip install {install_hint}[/red]"
            )
        return 2
    except OSError as e:
        console.print(f"[red]Error running {tool_name}: {e}[/red]")
        return 2
