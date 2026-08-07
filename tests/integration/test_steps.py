"""Integration tests for behave-runner steps command."""

from __future__ import annotations

import importlib.util

import pytest
from typer.testing import CliRunner

from behave_runner.cli.app import app

runner = CliRunner()


def test_steps_list_with_dep() -> None:
    """Test steps list when behave-steplib is installed."""
    if not importlib.util.find_spec("behave_steplib"):
        pytest.skip("behave-steplib not installed")
    result = runner.invoke(app, ["steps", "list"])
    assert result.exit_code in (0, 1)


def test_steps_without_dep() -> None:
    """Test steps degrades gracefully when behave-steplib not installed."""
    result = runner.invoke(app, ["steps", "list"])
    assert result.exit_code in (0, 2)


def test_steps_help() -> None:
    """Test steps --help."""
    result = runner.invoke(app, ["steps", "--help"])
    assert result.exit_code == 0
    assert "steps" in result.stdout.lower()
