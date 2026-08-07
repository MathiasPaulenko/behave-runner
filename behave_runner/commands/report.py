"""Report command for behave-runner CLI."""

from __future__ import annotations

import subprocess  # nosec B404
from pathlib import Path
from typing import Literal

import typer
from rich.console import Console

from behave_runner.core.deps import check_optional
from behave_runner.core.output import ensure_output_dir, open_latest_report

console = Console()

report_app = typer.Typer(
    name="report",
    help="Generate and show reports.",
    no_args_is_help=True,
)

FormatType = Literal["console", "html", "md", "json", "sheets", "file"]

_FORMAT_PACKAGES: dict[str, str] = {
    "console": "behave_modern_console_report",
    "html": "behave_modern_html_report",
    "md": "behave_modern_md_report",
    "json": "behave_modern_json_report",
    "sheets": "behave_modern_sheets_report",
    "file": "behave_modern_file_report",
}

_FORMAT_EXTRAS: dict[str, str] = {
    "console": "report-console",
    "html": "report-html",
    "md": "report-md",
    "json": "report-json",
    "sheets": "report-sheets",
    "file": "report-file",
}


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
    """Generate reports from test results using behave-modern-*-report."""
    if fmt not in _FORMAT_PACKAGES:
        console.print(
            f"[red]Unknown format: '{fmt}'. Choose from: {', '.join(_FORMAT_PACKAGES)}[/red]"
        )
        raise typer.Exit(2)

    package = _FORMAT_PACKAGES[fmt]
    extra = _FORMAT_EXTRAS[fmt]
    if not check_optional(extra, package, f"format {fmt}"):
        raise typer.Exit(2)

    if output is not None:
        ensure_output_dir(output)

    cmd = [f"behave-modern-{fmt}-report"]  # nosec B607
    if output is not None:
        cmd.extend(["--output", str(output)])
    feature_paths = [str(f) for f in features] if features else ["features"]
    cmd.extend(feature_paths)

    try:
        result = subprocess.run(cmd, check=False)  # noqa: S603  # nosec B603
        raise typer.Exit(result.returncode)
    except FileNotFoundError:
        console.print(
            f"[red]Error: behave-modern-{fmt}-report not found. "
            f"Install with: pip install {package.replace('_', '-')}[/red]"
        )
        raise typer.Exit(2) from None
    except OSError as e:
        console.print(f"[red]Error running report command: {e}[/red]")
        raise typer.Exit(2) from None


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
