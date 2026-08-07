"""List command for behave-runner CLI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from behave_model import load_feature
from rich.console import Console
from rich.table import Table

console = Console()


def _collect_scenarios(feature_paths: list[Path], tags: list[str]) -> list[dict[str, Any]]:
    """Parse feature files and collect matching scenarios."""
    scenarios: list[dict[str, Any]] = []
    for fp in feature_paths:
        if fp.is_dir():
            feature_files = sorted(fp.rglob("*.feature"))
        elif fp.is_file() and fp.suffix == ".feature":
            feature_files = [fp]
        else:
            continue
        for ff in feature_files:
            feature = load_feature(str(ff))
            for scenario in feature.scenarios:
                if _matches_tags(scenario.tag_names, tags):
                    scenarios.append(
                        {
                            "feature": feature.name,
                            "scenario": scenario.name,
                            "location": str(scenario.location),
                            "tags": list(scenario.tag_names),
                        }
                    )
    return scenarios


def _matches_tags(scenario_tags: list[str], filter_tags: list[str]) -> bool:
    """Check if scenario matches all filter tags."""
    if not filter_tags:
        return True
    return all(tag in scenario_tags for tag in filter_tags)


def list_command(
    features: list[Path] = typer.Argument(
        default=None,
        help="Paths to feature files or directories.",
    ),
    tags: list[str] = typer.Option([], "--tags", "-t", help="Filter by tags."),
    fmt: str = typer.Option("text", "--format", help="Output format: text, json."),
) -> None:
    """List scenarios without executing them."""
    feature_paths = features if features else [Path("features")]
    scenarios = _collect_scenarios(feature_paths, tags)

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
