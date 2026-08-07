"""Format command for behave-runner CLI."""

from __future__ import annotations

import subprocess  # nosec B404

import typer
from rich.console import Console

from behave_runner.core.deps import check_optional

console = Console()


def format_command(
    args: list[str] = typer.Argument(None, help="Arguments to pass to behave-format."),
    check: bool = typer.Option(False, "--check", help="Check only, don't modify files."),
    diff: bool = typer.Option(False, "--diff", help="Show diff of changes."),
    in_place: bool = typer.Option(False, "--in-place", help="Modify files in place."),
) -> None:
    """Run behave-format to format feature files."""
    if not check_optional("format", "behave_format", "format"):
        raise typer.Exit(2)

    cmd = ["behave-format"]
    if check:
        cmd.append("--check")
    if diff:
        cmd.append("--diff")
    if in_place:
        cmd.append("--in-place")
    cmd.extend(args or [])

    try:
        result = subprocess.run(cmd, check=False)  # noqa: S603  # nosec B603
        raise typer.Exit(result.returncode)
    except FileNotFoundError:
        console.print(
            "[red]Error: behave-format not found. Install with: pip install behave-format[/red]"
        )
        raise typer.Exit(2) from None
    except OSError as e:
        console.print(f"[red]Error running behave-format: {e}[/red]")
        raise typer.Exit(2) from None
