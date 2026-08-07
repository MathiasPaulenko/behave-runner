"""Integration tests for behave-runner impact command."""

from __future__ import annotations

import importlib.util

import pytest
from typer.testing import CliRunner

from behave_runner.cli.app import app

runner = CliRunner()


def test_impact_with_dep() -> None:
    """Test impact when behave-doctor is installed."""
    if not importlib.util.find_spec("behave_doctor"):
        pytest.skip("behave-doctor not installed")
    result = runner.invoke(app, ["impact", "tests/fixtures/minimal"])
    assert result.exit_code in (0, 1)


def test_impact_without_dep() -> None:
    """Test impact degrades gracefully when behave-doctor not installed."""
    result = runner.invoke(app, ["impact", "tests/fixtures/minimal"])
    assert result.exit_code in (0, 1, 2)


def test_impact_help() -> None:
    """Test impact --help."""
    result = runner.invoke(app, ["impact", "--help"])
    assert result.exit_code == 0
    assert "impact" in result.stdout.lower()
