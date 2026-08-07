"""List command for behave-runner CLI."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from behave_runner.core.features import collect_scenarios

console = Console()


def list_command(
    features: list[Path] = typer.Argument(
        default=None,
        help="Paths to feature files or directories.",
    ),
    tags: list[str] = typer.Option([], "--tags", "-t", help="Filter by tags."),
    fmt: str = typer.Option("text", "--format", help="Output format: text, json."),
) -> None:
    """List scenarios without executing them."""
    valid_formats = {"text", "json"}
    if fmt not in valid_formats:
        console.print(
            f"[red]Unknown format: '{fmt}'. Choose from: {', '.join(sorted(valid_formats))}[/red]"
        )
        raise typer.Exit(2)

    feature_paths = features if features else [Path("features")]
    scenarios = collect_scenarios(feature_paths, tags=tags)

    if fmt == "json":
        print(json.dumps(scenarios, indent=2))
    else:
        table = Table(title="Scenarios")
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
