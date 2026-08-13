"""Open command for behave-runner CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import typer
from rich.console import Console

from behave_runner.core.deps import check_optional, run_external
from behave_runner.core.output import open_latest_report

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
        file_okay=False,
        dir_okay=True,
    ),
) -> None:
    """Open the latest report or trace viewer in the browser."""
    if target == "trace":
        _open_trace()
        return

    _open_report(output)


def _open_report(output: Path) -> None:
    """Find and open the latest report in the browser."""
    open_latest_report(output)


def _open_trace() -> None:
    """Open the trace viewer via behave-trace."""
    if not check_optional("trace", "behave_trace", "trace"):
        raise typer.Exit(2)

    # Search for trace.json in common locations
    trace_candidates = [
        Path("reports") / "trace.json",
        Path("trace.json"),
        Path("output") / "trace.json",
    ]
    trace_file = next((p for p in trace_candidates if p.exists()), None)

    cmd = ["behave-trace", "show"]
    if trace_file is not None:
        cmd.append(str(trace_file))
    else:
        console.print(
            "[yellow]Warning: trace.json not found. Run with --trace to generate one.[/yellow]"
        )

    raise typer.Exit(run_external(cmd, "behave-trace", "behave-trace"))
