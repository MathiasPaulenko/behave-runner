"""Steps command for behave-runner CLI."""

from __future__ import annotations

import subprocess  # nosec B404

import typer
from rich.console import Console

from behave_runner.core.deps import check_optional

console = Console()

steps_app = typer.Typer(
    name="steps",
    help="Manage step libraries using behave-steplib.",
    no_args_is_help=True,
)


def _run_steplib(cmd: list[str]) -> None:
    """Delegate to steplib via subprocess."""
    if not check_optional("steplib", "behave_steplib", "steps"):
        raise typer.Exit(2)

    try:
        result = subprocess.run(cmd, check=False)  # noqa: S603  # nosec B603
        raise typer.Exit(result.returncode)
    except FileNotFoundError:
        console.print(
            "[red]Error: steplib not found. Install with: pip install behave-steplib[/red]"
        )
        raise typer.Exit(2) from None
    except OSError as e:
        console.print(f"[red]Error running steplib: {e}[/red]")
        raise typer.Exit(2) from None


@steps_app.command(name="list")
def steps_list(
    args: list[str] = typer.Argument(None, help="Additional arguments."),
) -> None:
    """List available step libraries."""
    _run_steplib(["steplib", "list", *(args or [])])


@steps_app.command(name="show")
def steps_show(
    pattern: str = typer.Argument(..., help="Step pattern to show."),
    args: list[str] = typer.Argument(None, help="Additional arguments."),
) -> None:
    """Show details for a specific step pattern."""
    _run_steplib(["steplib", "show", pattern, *(args or [])])


@steps_app.command(name="search")
def steps_search(
    query: str = typer.Argument(..., help="Search query."),
    args: list[str] = typer.Argument(None, help="Additional arguments."),
) -> None:
    """Search for step libraries by partial pattern."""
    _run_steplib(["steplib", "search", query, *(args or [])])


@steps_app.command(name="validate")
def steps_validate(
    args: list[str] = typer.Argument(None, help="Additional arguments."),
) -> None:
    """Validate step contracts."""
    _run_steplib(["steplib", "validate", *(args or [])])


@steps_app.command(name="init")
def steps_init(
    args: list[str] = typer.Argument(None, help="Additional arguments."),
) -> None:
    """Generate features/environment.py with autoload wiring."""
    _run_steplib(["steplib", "init", *(args or [])])


@steps_app.command(name="install")
def steps_install(
    name: str = typer.Argument(..., help="Step library extra to install (e.g. api, web, db)."),
    args: list[str] = typer.Argument(None, help="Additional arguments."),
) -> None:
    """Show pip install command for a step library extra."""
    _run_steplib(["steplib", "install", name, *(args or [])])
