"""Lint command for behave-runner CLI."""

from __future__ import annotations

import subprocess  # nosec B404

import typer
from rich.console import Console

from behave_runner.core.deps import check_optional

console = Console()


def lint_command(
    ctx: typer.Context,
    args: list[str] = typer.Argument(None, help="Arguments to pass to behave-lint."),
) -> None:
    """Run behave-lint static analysis on features."""
    if not check_optional("lint", "behave_lint", "lint"):
        raise typer.Exit(2)

    cmd = [*args] if args else []
    cmd.extend(ctx.args)
    try:
        result = subprocess.run(["behave-lint", *cmd], check=False)  # noqa: S603  # nosec
        raise typer.Exit(result.returncode)
    except FileNotFoundError:
        console.print(
            "[red]Error: behave-lint not found. Install with: pip install behave-lint[/red]"
        )
        raise typer.Exit(2) from None
    except OSError as e:
        console.print(f"[red]Error running behave-lint: {e}[/red]")
        raise typer.Exit(2) from None
