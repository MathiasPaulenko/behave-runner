"""Init command for behave-runner CLI."""

from __future__ import annotations

import subprocess

import typer
from rich.console import Console

from behave_runner.core.deps import check_optional

console = Console()


def init_command(
    name: str | None = typer.Option(
        None, "--name", help="Project name for the generated structure."
    ),
    args: list[str] = typer.Argument(None, help="Additional arguments for behave-gen."),
) -> None:
    """Initialize a new behave project structure using behave-gen."""
    if not check_optional("gen", "behave_gen", "init"):
        raise typer.Exit(2)

    cmd = ["behave-gen", "init"]
    if name:
        cmd.extend(["--name", name])
    cmd.extend(args or [])

    try:
        result = subprocess.run(cmd, check=False)  # noqa: S603
        raise typer.Exit(result.returncode)
    except FileNotFoundError:
        console.print(
            "[red]Error: behave-gen not found. Install with: pip install behave-gen[/red]"
        )
        raise typer.Exit(2) from None
