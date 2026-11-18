"""Record command for behave-runner CLI."""

from __future__ import annotations

import subprocess  # nosec B404
from pathlib import Path

import typer
from rich.console import Console

from behave_runner.core.deps import check_optional, resolve_executable, run_external

console = Console()
err_console = Console(stderr=True)


def record_command(
    url: str = typer.Argument(
        "about:blank",
        help="URL to record. Use about:blank to navigate manually.",
    ),
    output: Path = typer.Option(
        Path("recordings"),
        "--output",
        help="Directory for recording output.",
        file_okay=False,
        dir_okay=True,
    ),
    name: str = typer.Option(
        "recorded_step",
        "--name",
        help="Name for the generated step.",
    ),
) -> None:
    """Record a browser session with wavexis and generate behave steps."""
    if not name.strip() or Path(name).name != name.strip():
        err_console.print("[red]Error: --name must be a simple file name.[/red]")
        raise typer.Exit(2)

    if not check_optional("record", "wavexis", "record"):
        raise typer.Exit(2)

    try:
        output.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        err_console.print(f"[red]Error: cannot create output directory {output}: {e}[/red]")
        raise typer.Exit(2) from e
    recording_path = output / f"{name}.yaml"

    console.print(f"[cyan]Starting wavexis recording -> {recording_path}[/cyan]")
    cmd = [
        resolve_executable("wavexis"),
        "record",
        url,
        "--output",
        str(recording_path),
        "--interactive",
    ]
    try:
        result = subprocess.run(cmd, check=False)  # noqa: S603  # nosec B603
    except FileNotFoundError:
        # wavexis already passed the import check — the console script
        # itself is missing, i.e. a broken install.
        err_console.print(
            "[red]Error: wavexis console script not found. "
            "Reinstall with: pip install --force-reinstall wavexis[/red]"
        )
        raise typer.Exit(2) from None
    except OSError as e:
        err_console.print(f"[red]Error running wavexis: {e}[/red]")
        raise typer.Exit(2) from None

    if result.returncode != 0:
        err_console.print(f"[red]Recording failed with exit code {result.returncode}[/red]")
        raise typer.Exit(result.returncode)

    console.print(f"[green]Recording saved: {recording_path}[/green]")

    if not check_optional("gen", "behave_gen", "generate"):
        err_console.print(
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
    raise typer.Exit(run_external(gen_cmd, "behave-gen", "behave-gen"))
