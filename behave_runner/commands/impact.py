"""Impact command for behave-runner CLI."""

from __future__ import annotations

import json
import re
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

    # When --run is used, always request JSON internally for reliable parsing
    internal_fmt = "json" if run_affected else fmt
    cmd = ["behave-doctor", "scan", "--format", internal_fmt, path]

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
        names = _extract_scenario_names(result.stdout)
        if names:
            console.print(f"[cyan]Running {len(names)} affected scenarios...[/cyan]")
            worst_exit = 0
            for name in names:
                escaped_name = re.escape(name)
                config = RunConfig(features=[path], name=[escaped_name])
                exit_code = run(config)
                if exit_code != 0:
                    worst_exit = exit_code
            raise typer.Exit(worst_exit)
        console.print("[yellow]No affected scenarios to run.[/yellow]")
        raise typer.Exit(result.returncode)

    raise typer.Exit(result.returncode)


def _extract_scenario_names(stdout: str) -> list[str]:
    """Extract scenario names from behave-doctor JSON output.

    The JSON structure from behave-doctor contains a ``diagnostics`` list,
    where each entry may have a ``metadata.scenario`` field. Falls back
    to empty list if parsing fails.
    """
    if not stdout.strip():
        return []
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        return []

    names: list[str] = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.get("diagnostics") or data.get("findings") or data.get("scenarios") or []
    else:
        return []

    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            name = item.get("scenario") or item.get("name")
            if not name:
                meta = item.get("metadata", {})
                if isinstance(meta, dict):
                    name = meta.get("scenario")
            if isinstance(name, str) and name:
                names.append(name)
    return names
