"""Impact command for behave-runner CLI."""

from __future__ import annotations

import subprocess  # nosec B404

import typer
from rich.console import Console

from behave_runner.core.deps import check_optional
from behave_runner.core.orchestrator import RunConfig, run

console = Console()


VALID_FORMATS = {"text", "json", "sarif"}


def impact_command(
    path: str = typer.Argument(".", help="Project root directory to analyze."),
    fmt: str = typer.Option("text", "--format", help="Output format: text, json, sarif."),
    run_affected: bool = typer.Option(
        False, "--run", help="Run affected scenarios after detecting them."
    ),
) -> None:
    """Detect scenarios affected by code changes using behave-doctor."""
    if fmt not in VALID_FORMATS:
        console.print(
            f"[red]Unknown format: '{fmt}'. Choose from: {', '.join(sorted(VALID_FORMATS))}[/red]"
        )
        raise typer.Exit(2)

    if not check_optional("doctor", "behave_doctor", "impact"):
        raise typer.Exit(2)

    cmd = ["behave-doctor", "scan", "--format", fmt, path]

    try:
        result = subprocess.run(  # noqa: S603  # nosec B603
            cmd, check=False, capture_output=run_affected, text=True
        )
    except FileNotFoundError:
        console.print(
            "[red]Error: behave-doctor not found. Install with: pip install behave-doctor[/red]"
        )
        raise typer.Exit(2) from None
    except OSError as e:
        console.print(f"[red]Error running behave-doctor: {e}[/red]")
        raise typer.Exit(2) from None

    if run_affected:
        if result.returncode != 0:
            raise typer.Exit(result.returncode)
        if result.stdout:
            names = [line.strip() for line in result.stdout.strip().splitlines() if line.strip()]
            if names:
                console.print(f"[cyan]Running {len(names)} affected scenarios...[/cyan]")
                worst_exit = 0
                for name in names:
                    config = RunConfig(features=[path], name=[name])
                    exit_code = run(config)
                    if exit_code != 0:
                        worst_exit = exit_code
                raise typer.Exit(worst_exit)
            console.print("[yellow]No affected scenarios to run.[/yellow]")
            raise typer.Exit(result.returncode)

    raise typer.Exit(result.returncode)
