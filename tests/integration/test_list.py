"""Integration tests for behave-runner list command."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from behave_runner.cli.app import app

runner = CliRunner()


def test_list_minimal() -> None:
    """Test list shows scenarios in rich table."""
    result = runner.invoke(app, ["list", "tests/fixtures/minimal/features"])
    assert result.exit_code == 0
    assert "Successful login" in result.stdout


def test_list_json() -> None:
    """Test --format json produces valid JSON."""
    result = runner.invoke(app, ["list", "--format", "json", "tests/fixtures/minimal/features"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert len(data) >= 1
    assert data[0]["scenario"] == "Successful login"
    assert data[0]["feature"] == "Login"
    assert "location" in data[0]
    assert "tags" in data[0]


def test_list_tags_filter() -> None:
    """Test --tags filters scenarios."""
    result = runner.invoke(
        app, ["list", "--tags", "@nonexistent", "tests/fixtures/minimal/features"]
    )
    assert result.exit_code == 0


def test_list_priority_tags() -> None:
    """Test listing with tags from priority fixture."""
    result = runner.invoke(app, ["list", "tests/fixtures/priority/features"])
    assert result.exit_code == 0
    assert "Smoke test" in result.stdout
    assert "High priority test" in result.stdout


def test_list_tags_filter_smoke() -> None:
    """Test --tags=@smoke filters to only smoke scenarios."""
    result = runner.invoke(app, ["list", "--tags=@smoke", "tests/fixtures/priority/features"])
    assert result.exit_code == 0
    assert "Smoke test" in result.stdout
    assert "High priority test" not in result.stdout


def test_list_tags_exclude() -> None:
    """Test --tags=~@smoke excludes smoke scenarios."""
    result = runner.invoke(
        app,
        ["list", "--tags=~@smoke", "--format", "json", "tests/fixtures/priority/features"],
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    scenarios = [s["scenario"] for s in data]
    assert "Smoke test" not in scenarios
    assert "High priority test" in scenarios
    assert "Low priority test" in scenarios


def test_list_multiple_tags_and() -> None:
    """Test multiple --tags are ANDed together."""
    result = runner.invoke(
        app,
        [
            "list",
            "--tags=@smoke",
            "--tags=@priority.1",
            "--format",
            "json",
            "tests/fixtures/priority/features",
        ],
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data == []


def test_list_invalid_format() -> None:
    """Test --format with invalid value exits with code 2."""
    result = runner.invoke(app, ["list", "tests/fixtures/minimal/features", "--format", "xml"])
    assert result.exit_code == 2
    assert "Unknown format" in result.output
    assert "xml" in result.output


def test_list_default_features_path() -> None:
    """Test list with no args uses 'features' as default path."""
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0


def test_list_nonexistent_path() -> None:
    """Test list with nonexistent path returns empty gracefully."""
    result = runner.invoke(app, ["list", "nonexistent/path/"])
    assert result.exit_code == 0


def test_list_json_structure() -> None:
    """Test JSON output has correct structure with all required fields."""
    result = runner.invoke(app, ["list", "--format", "json", "tests/fixtures/priority/features"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    for item in data:
        assert "feature" in item
        assert "scenario" in item
        assert "location" in item
        assert "tags" in item
        assert isinstance(item["tags"], list)


def test_list_help() -> None:
    """Test list --help."""
    result = runner.invoke(app, ["list", "--help"])
    assert result.exit_code == 0
    assert "list" in result.stdout.lower()
    assert "--tags" in result.stdout
    assert "--format" in result.stdout
