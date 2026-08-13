"""Shared feature file parsing utilities."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import TypedDict

from behave_model import load_feature

logger = logging.getLogger(__name__)


class ScenarioInfo(TypedDict):
    """Information about a single scenario collected from a feature file."""

    feature: str
    scenario: str
    location: str
    tags: list[str]


def collect_scenarios(
    feature_paths: list[Path],
    tags: list[str] | None = None,
    pattern: str | None = None,
    feature_name: str | None = None,
) -> list[ScenarioInfo]:
    """Parse feature files and collect scenarios matching all filters.

    Args:
        feature_paths: Paths to feature files or directories.
        tags: Tag filters. Use ~@tag to exclude.
        pattern: Regex pattern to match scenario names.
        feature_name: Case-insensitive substring to filter feature names.
    """
    include_tags = [t.strip() for t in (tags or []) if not t.startswith("~") and t.strip()]
    exclude_tags = [t[1:].strip() for t in (tags or []) if t.startswith("~") and t[1:].strip()]

    regex = re.compile(pattern) if pattern else None

    scenarios: list[ScenarioInfo] = []
    for fp in feature_paths:
        try:
            if fp.is_dir():
                feature_files = sorted(fp.rglob("*.feature"))
            elif fp.is_file() and fp.suffix == ".feature":
                feature_files = [fp]
            else:
                continue
        except OSError as e:
            logger.warning("Skipping %s: %s", fp, e)
            continue
        for ff in feature_files:
            try:
                feature = load_feature(str(ff))
            except Exception as e:
                logger.warning("Failed to load feature %s: %s", ff, e)
                continue
            if feature_name and (
                not feature.name or feature_name.lower() not in feature.name.lower()
            ):
                continue
            for scenario in feature.scenarios:
                scenario_tags = [t.strip() for t in scenario.tag_names]
                if not matches_tags(scenario_tags, include_tags, exclude_tags):
                    continue
                if regex and (not scenario.name or not regex.search(scenario.name)):
                    continue
                scenarios.append(
                    ScenarioInfo(
                        feature=feature.name or "",
                        scenario=scenario.name or "",
                        location=str(scenario.location),
                        tags=scenario_tags,
                    )
                )
    return scenarios


def matches_tags(
    scenario_tags: list[str],
    include_tags: list[str] | None = None,
    exclude_tags: list[str] | None = None,
) -> bool:
    """Check if scenario matches include tags (AND) and excludes none.

    If no include tags are specified, all scenarios pass the include check.
    If no exclude tags are specified, no scenarios are excluded.
    """
    scenario_tags = [t.strip() for t in (scenario_tags or [])]
    include = [t.strip() for t in (include_tags or []) if t.strip()]
    exclude = [t.strip() for t in (exclude_tags or []) if t.strip()]
    if include and not all(t in scenario_tags for t in include):
        return False
    if exclude:
        return not any(t in scenario_tags for t in exclude)
    return True
