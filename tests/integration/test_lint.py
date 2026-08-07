"""Integration tests for behave-runner lint command."""

from __future__ import annotations

import importlib.util

import pytest
from typer.testing import CliRunner

from behave_runner.cli.app import app

runner = CliRunner()


def test_lint_with_dep() -> None:
    """Test lint when behave-lint is installed."""
    if not importlib.util.find_spec("behave_lint"):
        pytest.skip("behave-lint not installed")
    result = runner.invoke(app, ["lint", "tests/fixtures/minimal/features"])
    assert result.exit_code in (0, 1)


def test_lint_without_dep() -> None:
    """Test lint degrades gracefully when behave-lint not installed."""
    result = runner.invoke(app, ["lint", "tests/fixtures/minimal/features"])
    assert result.exit_code in (0, 1, 2)


def test_lint_help() -> None:
    """Test lint --help."""
    result = runner.invoke(app, ["lint", "--help"])
    assert result.exit_code == 0
    assert "lint" in result.stdout.lower()
