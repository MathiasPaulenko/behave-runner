"""Select command for behave-runner CLI."""

from __future__ import annotations

import json
import re
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from behave_runner.core.features import collect_scenarios

console = Console()


def select_command(
    features: list[Path] = typer.Argument(
        default=None,
        help="Paths to feature files or directories.",
    ),
    pattern: str | None = typer.Option(
        None, "--pattern", help="Regex pattern to match scenario names."
    ),
    tags: list[str] = typer.Option(
        [], "--tags", "-t", help="Filter by tags. Use ~@tag to exclude."
    ),
    feature_name: str | None = typer.Option(
        None, "--feature", help="Filter by feature name (case-insensitive substring)."
    ),
    fmt: str = typer.Option("text", "--format", help="Output format: text, names, json."),
) -> None:
    """Select scenarios with advanced filtering."""
    valid_formats = {"text", "names", "json"}
    if fmt not in valid_formats:
        console.print(
            f"[red]Unknown format: '{fmt}'. Choose from: {', '.join(sorted(valid_formats))}[/red]"
        )
        raise typer.Exit(2)

    feature_paths = features if features else [Path("features")]

    if pattern is not None:
        try:
            re.compile(pattern)
        except re.error as e:
            console.print(f"[red]Invalid regex pattern: {e}[/red]")
            raise typer.Exit(2) from e

    scenarios = collect_scenarios(
        feature_paths, tags=tags, pattern=pattern, feature_name=feature_name
    )

    if fmt == "json":
        print(json.dumps(scenarios, indent=2))
    elif fmt == "names":
        for s in scenarios:
            print(s["scenario"])
    else:
        table = Table(title="Selected Scenarios")
        table.add_column("Feature")
        table.add_column("Scenario")
        table.add_column("Location")
        table.add_column("Tags")
        for s in scenarios:
            table.add_row(
                s["feature"],
                s["scenario"],
                s["location"],
                ", ".join(s["tags"]),
            )
        console.print(table)
