"""Open command for behave-runner CLI."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Literal

import typer
from rich.console import Console

from behave_runner.core.deps import check_optional
from behave_runner.core.output import find_latest_report
from behave_runner.utils import open_in_browser

console = Console()

TargetType = Literal["report", "trace"]


def open_command(
    target: TargetType = typer.Argument(
        "report",
        help="What to open: 'report' (default) or 'trace'.",
    ),
    output: Path = typer.Option(
        Path("reports"),
        "--output",
        help="Directory containing reports.",
    ),
) -> None:
    """Open the latest report or trace viewer in the browser."""
    if target == "trace":
        _open_trace()
        return

    _open_report(output)


def _open_report(output: Path) -> None:
    """Find and open the latest report in the browser."""
    report_file = find_latest_report(output)
    if report_file is None:
        console.print("[yellow]No reports found.[/yellow]")
        return
    console.print(f"[green]Opening: {report_file}[/green]")
    open_in_browser(str(report_file.resolve()))


def _open_trace() -> None:
    """Open the trace viewer via behave-trace."""
    if not check_optional("trace", "behave_trace", "trace"):
        raise typer.Exit(2)

    try:
        result = subprocess.run(
            ["behave-trace", "show"],
            check=False,  # noqa: S603
        )
        raise typer.Exit(result.returncode)
    except FileNotFoundError:
        console.print(
            "[red]Error: behave-trace not found. Install with: pip install behave-trace[/red]"
        )
        raise typer.Exit(2) from None
