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
