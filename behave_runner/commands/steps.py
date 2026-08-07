"""Steps command for behave-runner CLI."""

from __future__ import annotations

import subprocess

import typer
from rich.console import Console

from behave_runner.core.deps import check_optional

console = Console()

steps_app = typer.Typer(
    name="steps",
    help="Manage step libraries using behave-steplib.",
    no_args_is_help=True,
)


def _run_behave_steplib(cmd: list[str]) -> None:
    """Delegate to behave-steplib via subprocess."""
    if not check_optional("steplib", "behave_steplib", "steps"):
        raise typer.Exit(2)

    try:
        result = subprocess.run(cmd, check=False)  # noqa: S603
        raise typer.Exit(result.returncode)
    except FileNotFoundError:
        console.print(
            "[red]Error: behave-steplib not found. Install with: pip install behave-steplib[/red]"
        )
        raise typer.Exit(2) from None


@steps_app.command(name="list")
def steps_list(
    args: list[str] = typer.Argument(None, help="Additional arguments."),
) -> None:
    """List available step libraries."""
    _run_behave_steplib(["behave-steplib", "list", *(args or [])])


@steps_app.command(name="install")
def steps_install(
    name: str = typer.Argument(..., help="Step library name to install."),
    args: list[str] = typer.Argument(None, help="Additional arguments."),
) -> None:
    """Install a step library."""
    _run_behave_steplib(["behave-steplib", "install", name, *(args or [])])


@steps_app.command(name="search")
def steps_search(
    query: str = typer.Argument(..., help="Search query."),
    args: list[str] = typer.Argument(None, help="Additional arguments."),
) -> None:
    """Search for step libraries."""
    _run_behave_steplib(["behave-steplib", "search", query, *(args or [])])
