"""Doctor command for behave-runner CLI."""

from __future__ import annotations

import subprocess

import typer
from rich.console import Console

from behave_runner.core.deps import check_optional

console = Console()


def doctor_command(
    args: list[str] = typer.Argument(None, help="Arguments to pass to behave-doctor."),
) -> None:
    """Run behave-doctor to diagnose and fix common issues."""
    if not check_optional("doctor", "behave_doctor", "doctor"):
        raise typer.Exit(2)

    cmd = ["behave-doctor", *(args or [])]
    try:
        result = subprocess.run(cmd, check=False)  # noqa: S603
        raise typer.Exit(result.returncode)
    except FileNotFoundError:
        console.print(
            "[red]Error: behave-doctor not found. Install with: pip install behave-doctor[/red]"
        )
        raise typer.Exit(2) from None
