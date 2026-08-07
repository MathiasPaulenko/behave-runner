"""Record command for behave-runner CLI."""

from __future__ import annotations

import subprocess
from pathlib import Path

import typer
from rich.console import Console

from behave_runner.core.deps import check_optional

console = Console()


def record_command(
    url: str = typer.Argument(
        "about:blank",
        help="URL to record. Use about:blank to navigate manually.",
    ),
    output: Path = typer.Option(
        Path("recordings"),
        "--output",
        help="Directory for recording output.",
    ),
    name: str = typer.Option(
        "recorded_step",
        "--name",
        help="Name for the generated step.",
    ),
) -> None:
    """Record a browser session with wavexis and generate behave steps."""
    if not check_optional("record", "wavexis", "record"):
        raise typer.Exit(2)

    output.mkdir(parents=True, exist_ok=True)
    recording_path = output / f"{name}.yaml"

    console.print(f"[cyan]Starting wavexis recording → {recording_path}[/cyan]")
    cmd = [
        "wavexis",
        "record",
        url,
        "--output",
        str(recording_path),
        "--interactive",
    ]
    try:
        result = subprocess.run(cmd, check=False)  # noqa: S603
    except FileNotFoundError:
        console.print(
            "[red]Error: wavexis not found. Install with: pip install behave-runner[record][/red]"
        )
        raise typer.Exit(2) from None

    if result.returncode != 0:
        console.print(f"[red]Recording failed with exit code {result.returncode}[/red]")
        raise typer.Exit(result.returncode)

    console.print(f"[green]Recording saved: {recording_path}[/green]")

    if not check_optional("gen", "behave_gen", "generate"):
        console.print(
            "[yellow]Warning: behave-gen not installed. Skipping step generation.[/yellow]"
        )
        raise typer.Exit(0)

    gen_cmd = [
        "behave-gen",
        "add",
        "steps",
        "--from-recording",
        str(recording_path),
    ]
    try:
        gen_result = subprocess.run(gen_cmd, check=False)  # noqa: S603
    except FileNotFoundError:
        console.print(
            "[red]Error: behave-gen not found. Install with: pip install behave-gen[/red]"
        )
        raise typer.Exit(2) from None

    raise typer.Exit(gen_result.returncode)
