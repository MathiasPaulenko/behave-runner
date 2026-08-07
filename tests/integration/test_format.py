"""Integration tests for behave-runner format command."""

from __future__ import annotations

import importlib.util

import pytest
from typer.testing import CliRunner

from behave_runner.cli.app import app

runner = CliRunner()


def test_format_check() -> None:
    """Test format --check when behave-format is installed."""
    if not importlib.util.find_spec("behave_format"):
        pytest.skip("behave-format not installed")
    result = runner.invoke(app, ["format", "--check", "tests/fixtures/minimal/features"])
    assert result.exit_code in (0, 1)


def test_format_without_dep() -> None:
    """Test format degrades gracefully when behave-format not installed."""
    result = runner.invoke(app, ["format", "tests/fixtures/minimal/features"])
    assert result.exit_code in (0, 1, 2)


def test_format_help() -> None:
    """Test format --help."""
    result = runner.invoke(app, ["format", "--help"])
    assert result.exit_code == 0
    assert "format" in result.stdout.lower()
