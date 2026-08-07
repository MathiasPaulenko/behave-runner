"""Report command for behave-runner CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import typer
from rich.console import Console

from behave_runner.core.orchestrator import RunConfig, run
from behave_runner.core.output import ensure_output_dir, open_latest_report

console = Console()

report_app = typer.Typer(
    name="report",
    help="Generate and show reports.",
    no_args_is_help=True,
)

FormatType = Literal["console", "html", "md", "json", "sheets", "file"]


@report_app.command(name="generate")
def report_command(
    features: list[Path] = typer.Argument(
        default=None,
        help="Paths to feature files or directories.",
    ),
    fmt: str = typer.Option(
        "console",
        "--format",
        help="Report format: console, html, md, json, sheets, file.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        help="Output directory for reports.",
        file_okay=False,
        dir_okay=True,
    ),
) -> None:
    """Generate reports from test results using behave-modern-*-report.

    This runs behave with the appropriate --format flag for the chosen
    report format. The report is written to the output directory if
    specified, otherwise to the current directory.
    """
    valid_formats = {"console", "html", "md", "json", "sheets", "file"}
    if fmt not in valid_formats:
        console.print(
            f"[red]Unknown format: '{fmt}'. Choose from: {', '.join(sorted(valid_formats))}[/red]"
        )
        raise typer.Exit(2)

    if output is not None:
        ensure_output_dir(output)

    # Build the output file path from the output directory and format
    outfile = None
    if output is not None:
        extensions = {
            "json": "report.json",
            "html": "report.html",
            "md": "report.md",
            "sheets": "report.xlsx",
            "file": "report.txt",
            "console": "report.txt",
        }
        outfile = str(output / extensions.get(fmt, "report.txt"))

    feature_paths = [str(f) for f in features] if features else ["features"]
    config = RunConfig(
        features=feature_paths,
        fmt=fmt,
        outfile=outfile,
    )
    exit_code = run(config)
    raise typer.Exit(exit_code)


@report_app.command(name="show")
def report_show(
    output: Path = typer.Option(
        Path("reports"),
        "--output",
        help="Directory containing reports.",
        file_okay=False,
        dir_okay=True,
    ),
) -> None:
    """Open the latest report in the browser."""
    open_latest_report(output)
