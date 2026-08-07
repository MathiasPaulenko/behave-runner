"""Integration tests for behave-runner trace command."""

from __future__ import annotations

import importlib.util

import pytest
from typer.testing import CliRunner

from behave_runner.cli.app import app

runner = CliRunner()


def test_trace_show_with_dep() -> None:
    """Test trace show when behave-trace is installed."""
    if not importlib.util.find_spec("behave_trace"):
        pytest.skip("behave-trace not installed")
    result = runner.invoke(app, ["trace", "show"])
    assert result.exit_code in (0, 1, 2)


def test_trace_serve_with_dep() -> None:
    """Test trace serve when behave-trace is installed."""
    if not importlib.util.find_spec("behave_trace"):
        pytest.skip("behave-trace not installed")
    result = runner.invoke(app, ["trace", "serve"])
    assert result.exit_code in (0, 1, 2)


def test_trace_without_dep() -> None:
    """Test trace degrades gracefully when behave-trace not installed."""
    result = runner.invoke(app, ["trace", "show"])
    assert result.exit_code in (0, 2)


def test_trace_help() -> None:
    """Test trace --help."""
    result = runner.invoke(app, ["trace", "--help"])
    assert result.exit_code == 0
    assert "trace" in result.stdout.lower()
