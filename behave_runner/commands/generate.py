"""Generate command for behave-runner CLI."""

from __future__ import annotations

import subprocess

import typer
from rich.console import Console

from behave_runner.core.deps import check_optional

console = Console()

generate_app = typer.Typer(
    name="generate",
    help="Generate step definitions and feature files using behave-gen.",
    no_args_is_help=True,
)


def _run_behave_gen(cmd: list[str]) -> None:
    """Delegate to behave-gen via subprocess."""
    if not check_optional("gen", "behave_gen", "generate"):
        raise typer.Exit(2)

    try:
        result = subprocess.run(cmd, check=False)  # noqa: S603
        raise typer.Exit(result.returncode)
    except FileNotFoundError:
        console.print(
            "[red]Error: behave-gen not found. Install with: pip install behave-gen[/red]"
        )
        raise typer.Exit(2) from None


@generate_app.command(name="step")
def generate_step(
    lib: str = typer.Option(..., "--lib", help="Step library name (e.g. http, auth)."),
) -> None:
    """Generate step definitions from a step library."""
    _run_behave_gen(["behave-gen", "add", "steps", "--lib", lib])


@generate_app.command(name="feature")
def generate_feature(
    name: str = typer.Argument(..., help="Feature name (without extension)."),
    tags: str | None = typer.Option(None, "--tags", help="Comma or space separated tags."),
) -> None:
    """Generate a feature file skeleton."""
    cmd = ["behave-gen", "add", "feature", name]
    if tags:
        cmd.extend(["--tags", tags])
    _run_behave_gen(cmd)
