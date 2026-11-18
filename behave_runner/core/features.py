"""Shared feature file parsing utilities."""

from __future__ import annotations

import logging
import re
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypedDict

from behave_model import load_feature

if TYPE_CHECKING:
    from behave_model import Feature

logger = logging.getLogger(__name__)


class ScenarioInfo(TypedDict):
    """Information about a single scenario collected from a feature file."""

    feature: str
    scenario: str
    location: str
    tags: list[str]


def _iter_scenarios(feature: Feature) -> Iterator[tuple[Any, list[str]]]:
    """Yield (scenario, inherited tag names) pairs.

    ``feature.scenarios`` only contains scenarios that are not inside a
    ``Rule:`` block; rule members live under ``feature.rules`` and are
    reachable through ``feature.all_scenarios()``. Iterating structurally
    also gives us each rule's tags so effective tags can be computed.
    """
    feature_tags = list(getattr(feature, "tag_names", None) or [])
    for scenario in feature.scenarios:
        yield scenario, feature_tags
    for rule in getattr(feature, "rules", None) or []:
        rule_tags = [*feature_tags, *(getattr(rule, "tag_names", None) or [])]
        for scenario in rule.scenarios:
            yield scenario, rule_tags


def _effective_tags(inherited: list[str], scenario: Any) -> list[str]:
    """Return inherited + own + Examples tags, matching behave's semantics."""
    tags = [t.strip() for t in inherited]
    tags.extend(t.strip() for t in (getattr(scenario, "tag_names", None) or []))
    for ex in getattr(scenario, "examples", None) or []:
        tags.extend(t.strip() for t in getattr(ex, "tag_names", []))
    return tags


def _norm_tag(tag: str) -> str:
    """Normalize a tag for matching; behave accepts names without '@'."""
    tag = tag.strip()
    return tag if tag.startswith("@") else f"@{tag}"


_TAG_TOKEN_RE = re.compile(r"\s*(and\b|or\b|not\b|\(|\)|[^\s()]+)")


def _eval_tag_expression(expr: str, tags: set[str]) -> bool:
    """Evaluate a behave v2 tag expression like '@a and not (@b or @c)'."""
    tokens = _TAG_TOKEN_RE.findall(expr)
    pos = 0

    def peek() -> str | None:
        return tokens[pos] if pos < len(tokens) else None

    def parse_or() -> bool:
        nonlocal pos
        val = parse_and()
        while peek() == "or":
            pos += 1
            # Evaluate the right side unconditionally so `pos` advances.
            val = parse_and() or val
        return val

    def parse_and() -> bool:
        nonlocal pos
        val = parse_not()
        while peek() == "and":
            pos += 1
            val = parse_not() and val
        return val

    def parse_not() -> bool:
        nonlocal pos
        if peek() == "not":
            pos += 1
            return not parse_not()
        return parse_atom()

    def parse_atom() -> bool:
        nonlocal pos
        tok = peek()
        if tok == "(":
            pos += 1
            val = parse_or()
            if peek() == ")":
                pos += 1
            return val
        pos += 1
        if tok is None or tok == ")":
            return False
        return _norm_tag(tok) in tags

    return parse_or()


_TAG_EXPR_RE = re.compile(r"\b(?:and|or|not)\b|[()]")


def _matches_tag_spec(spec: str, tags: set[str]) -> bool:
    """Match one --tags value with behave semantics.

    Behave accepts either a v2 boolean expression ("@a and not @b") or a
    comma-separated list where items are OR-ed and '~' negates
    ("@a,@b", "~@wip"). Multiple --tags flags are AND-ed by the caller.
    """
    spec = spec.strip()
    if not spec:
        return True
    if _TAG_EXPR_RE.search(spec):
        return _eval_tag_expression(spec, tags)
    parts = [p.strip() for p in spec.split(",") if p.strip()]
    if not parts:
        return True
    for part in parts:
        if part.startswith("~"):
            if _norm_tag(part[1:]) not in tags:
                return True
        elif _norm_tag(part) in tags:
            return True
    return False


_FEATURE_LOCATION_RE = re.compile(r"^(.+\.feature):(\d+)$", re.IGNORECASE)


def _split_location(raw: Path | str) -> tuple[Path, int | None]:
    """Split behave's 'path/file.feature:LINE' syntax into path and line."""
    text = str(raw)
    path = Path(text)
    try:
        if path.is_dir() or path.is_file():
            return path, None
    except OSError:
        pass
    match = _FEATURE_LOCATION_RE.match(text)
    if match:
        return Path(match.group(1)), int(match.group(2))
    return path, None


def collect_scenarios(
    feature_paths: Sequence[Path | str],
    tags: list[str] | None = None,
    pattern: str | None = None,
    feature_name: str | None = None,
) -> list[ScenarioInfo]:
    """Parse feature files and collect scenarios matching all filters.

    Args:
        feature_paths: Paths to feature files or directories. Behave's
            'file.feature:LINE' location syntax is also accepted.
        tags: Tag filters using behave semantics: comma-separated items are
            OR-ed, '~@tag' negates, and v2 expressions ('@a and not @b')
            are supported. Multiple entries are AND-ed.
        pattern: Regex pattern to match scenario names.
        feature_name: Case-insensitive substring to filter feature names.
    """
    tag_specs = [t.strip() for t in (tags or []) if t.strip()]
    regex = re.compile(pattern) if pattern else None

    scenarios: list[ScenarioInfo] = []
    seen_files: set[Path] = set()
    for raw_path in feature_paths:
        fp, line_no = _split_location(raw_path)
        try:
            if fp.is_dir():
                feature_files = sorted(
                    f for f in fp.rglob("*.feature") if f.suffix.lower() == ".feature"
                )
            elif fp.is_file() and fp.suffix.lower() == ".feature":
                feature_files = [fp]
            else:
                logger.warning("Skipping %s: not a .feature file or directory", fp)
                continue
        except OSError as e:
            logger.warning("Skipping %s: %s", fp, e)
            continue
        for ff in feature_files:
            key = ff.resolve()
            if key in seen_files:
                continue
            seen_files.add(key)
            try:
                feature = load_feature(str(ff))
            except Exception as e:
                logger.warning("Failed to load feature %s: %s", ff, e)
                continue
            if feature_name and (
                not feature.name or feature_name.lower() not in feature.name.lower()
            ):
                continue
            for scenario, inherited in _iter_scenarios(feature):
                if line_no is not None and getattr(scenario.location, "line", None) != line_no:
                    continue
                scenario_tags = _effective_tags(inherited, scenario)
                if tag_specs and not all(
                    _matches_tag_spec(spec, set(scenario_tags)) for spec in tag_specs
                ):
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
