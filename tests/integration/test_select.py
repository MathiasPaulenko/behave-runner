"""Integration tests for behave-runner select command."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from behave_runner.cli.app import app

runner = CliRunner()


def test_select_pattern() -> None:
    """Test --pattern filters by regex on scenario name."""
    result = runner.invoke(
        app, ["select", "--pattern", ".*login.*", "tests/fixtures/minimal/features"]
    )
    assert result.exit_code == 0
    assert "Successful login" in result.stdout


def test_select_names_format() -> None:
    """Test --format names outputs one name per line."""
    result = runner.invoke(app, ["select", "--format", "names", "tests/fixtures/minimal/features"])
    assert result.exit_code == 0
    lines = [line for line in result.stdout.strip().split("\n") if line]
    assert len(lines) >= 1
    assert "Successful login" in lines


def test_select_tags() -> None:
    """Test --tags with nonexistent tag returns no matches."""
    result = runner.invoke(
        app, ["select", "--tags", "@nonexistent", "tests/fixtures/minimal/features"]
    )
    assert result.exit_code == 0


def test_select_json() -> None:
    """Test --format json produces valid JSON."""
    result = runner.invoke(app, ["select", "--format", "json", "tests/fixtures/minimal/features"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert len(data) >= 1


def test_select_tags_smoke() -> None:
    """Test --tags @smoke filters to only smoke scenarios."""
    result = runner.invoke(app, ["select", "--tags", "@smoke", "tests/fixtures/priority/features"])
    assert result.exit_code == 0
    assert "Smoke test" in result.stdout
    assert "High priority test" not in result.stdout


def test_select_tags_exclude() -> None:
    """Test ~@tag excludes scenarios with that tag."""
    result = runner.invoke(app, ["select", "--tags", "~@smoke", "tests/fixtures/priority/features"])
    assert result.exit_code == 0
    assert "Smoke test" not in result.stdout
    assert "High priority test" in result.stdout


def test_select_feature_name() -> None:
    """Test --feature filters by feature name."""
    result = runner.invoke(app, ["select", "--feature", "Login", "tests/fixtures/minimal/features"])
    assert result.exit_code == 0
    assert "Successful login" in result.stdout


def test_select_feature_name_no_match() -> None:
    """Test --feature with no matching feature name."""
    result = runner.invoke(
        app, ["select", "--feature", "Nonexistent", "tests/fixtures/minimal/features"]
    )
    assert result.exit_code == 0


def test_select_help() -> None:
    """Test select --help."""
    result = runner.invoke(app, ["select", "--help"])
    assert result.exit_code == 0
    assert "select" in result.stdout.lower()


# --- Tests with full fixture ---


def test_select_full_all_scenarios() -> None:
    """Test select on full fixture returns all 10 scenarios."""
    result = runner.invoke(app, ["select", "--format", "json", "tests/fixtures/full/features"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert len(data) == 10


def test_select_full_tags_smoke_and_fast() -> None:
    """Test --tags @smoke --tags @fast (AND) on full fixture."""
    result = runner.invoke(
        app,
        [
            "select",
            "--tags",
            "@smoke",
            "--tags",
            "@fast",
            "--format",
            "json",
            "tests/fixtures/full/features",
        ],
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert len(data) == 2
    for s in data:
        assert "@smoke" in s["tags"]
        assert "@fast" in s["tags"]


def test_select_full_tags_exclude_smoke() -> None:
    """Test ~@smoke excludes all smoke scenarios."""
    result = runner.invoke(
        app, ["select", "--tags", "~@smoke", "--format", "names", "tests/fixtures/full/features"]
    )
    assert result.exit_code == 0
    lines = [line for line in result.stdout.strip().split("\n") if line]
    assert len(lines) == 5
    for line in lines:
        assert "login" not in line.lower() or "lockout" in line.lower()


def test_select_full_feature_name_case_insensitive() -> None:
    """Test --feature is case-insensitive."""
    result = runner.invoke(
        app,
        ["select", "--feature", "shopping", "--format", "names", "tests/fixtures/full/features"],
    )
    assert result.exit_code == 0
    lines = [line for line in result.stdout.strip().split("\n") if line]
    assert len(lines) == 4


def test_select_full_pattern_and_tags_combined() -> None:
    """Test --pattern and --tags combined."""
    result = runner.invoke(
        app,
        [
            "select",
            "--pattern",
            "cart.*",
            "--tags",
            "@smoke",
            "--format",
            "json",
            "tests/fixtures/full/features",
        ],
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert len(data) == 2
    for s in data:
        assert "cart" in s["scenario"].lower()
        assert "@smoke" in s["tags"]


def test_select_full_json_structure() -> None:
    """Test JSON output has correct structure."""
    result = runner.invoke(app, ["select", "--format", "json", "tests/fixtures/full/features"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    for s in data:
        assert "feature" in s
        assert "scenario" in s
        assert "location" in s
        assert "tags" in s
        assert isinstance(s["tags"], list)


def test_select_full_names_format() -> None:
    """Test --format names on full fixture."""
    result = runner.invoke(app, ["select", "--format", "names", "tests/fixtures/full/features"])
    assert result.exit_code == 0
    lines = [line for line in result.stdout.strip().split("\n") if line]
    assert len(lines) == 10


def test_select_full_text_format() -> None:
    """Test default text format on full fixture."""
    result = runner.invoke(app, ["select", "tests/fixtures/full/features"])
    assert result.exit_code == 0
    assert "Selected Scenarios" in result.stdout
    assert "Authentication" in result.stdout
    assert "Shopping cart" in result.stdout


def test_select_full_no_matches() -> None:
    """Test --feature with nonexistent name returns empty."""
    result = runner.invoke(
        app,
        ["select", "--feature", "Nonexistent", "--format", "json", "tests/fixtures/full/features"],
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert len(data) == 0


def test_select_full_invalid_format() -> None:
    """Test invalid format exits with code 2."""
    result = runner.invoke(app, ["select", "--format", "invalid", "tests/fixtures/full/features"])
    assert result.exit_code == 2


def test_select_full_invalid_regex() -> None:
    """Test invalid regex pattern exits with code 2."""
    result = runner.invoke(app, ["select", "--pattern", "[invalid", "tests/fixtures/full/features"])
    assert result.exit_code == 2
