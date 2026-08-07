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
    """Test --tags @smoke filters to only smoke scenarios."""
    result = runner.invoke(app, ["list", "--tags", "@smoke", "tests/fixtures/priority/features"])
    assert result.exit_code == 0
    assert "Smoke test" in result.stdout
    assert "High priority test" not in result.stdout


def test_list_help() -> None:
    """Test list --help."""
    result = runner.invoke(app, ["list", "--help"])
    assert result.exit_code == 0
    assert "list" in result.stdout.lower()
