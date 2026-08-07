"""Select command for behave-runner CLI."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import typer
from behave_model import load_feature
from rich.console import Console
from rich.table import Table

console = Console()


def _collect_scenarios(
    feature_paths: list[Path],
    pattern: str | None,
    tags: list[str],
    feature_name: str | None,
) -> list[dict[str, Any]]:
    """Parse feature files and collect scenarios matching all filters."""
    include_tags = [t for t in tags if not t.startswith("~")]
    exclude_tags = [t[1:] for t in tags if t.startswith("~")]

    regex = re.compile(pattern) if pattern else None

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
            if feature_name and feature_name.lower() not in feature.name.lower():
                continue
            for scenario in feature.scenarios:
                scenario_tags = list(scenario.tag_names)
                if not _matches_tags(scenario_tags, include_tags, exclude_tags):
                    continue
                if regex and not regex.search(scenario.name):
                    continue
                scenarios.append(
                    {
                        "feature": feature.name,
                        "scenario": scenario.name,
                        "location": str(scenario.location),
                        "tags": scenario_tags,
                    }
                )
    return scenarios


def _matches_tags(
    scenario_tags: list[str],
    include_tags: list[str],
    exclude_tags: list[str],
) -> bool:
    """Check if scenario matches include tags (AND) and excludes none."""
    if include_tags and not all(t in scenario_tags for t in include_tags):
        return False
    if exclude_tags:
        return not any(t in scenario_tags for t in exclude_tags)
    return True


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
    feature_paths = features if features else [Path("features")]
    scenarios = _collect_scenarios(feature_paths, pattern, tags, feature_name)

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
