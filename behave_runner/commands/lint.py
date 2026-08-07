"""Lint command for behave-runner CLI."""

from __future__ import annotations

import subprocess

import typer
from rich.console import Console

from behave_runner.core.deps import check_optional

console = Console()


def lint_command(
    args: list[str] = typer.Argument(None, help="Arguments to pass to behave-lint."),
) -> None:
    """Run behave-lint static analysis on features."""
    if not check_optional("lint", "behave_lint", "lint"):
        raise typer.Exit(2)

    cmd = [*args] if args else []
    try:
        result = subprocess.run(["behave-lint", *cmd], check=False)  # noqa: S603
        raise typer.Exit(result.returncode)
    except FileNotFoundError:
        console.print(
            "[red]Error: behave-lint not found. Install with: pip install behave-lint[/red]"
        )
        raise typer.Exit(2) from None
