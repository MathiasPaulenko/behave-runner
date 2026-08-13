"""Integration tests for behave-runner trace command."""

from __future__ import annotations

import importlib.util

import pytest
from typer.testing import CliRunner

from behave_runner.cli.app import app

runner = CliRunner()

TRACE_INSTALLED = importlib.util.find_spec("behave_trace") is not None


def test_trace_show_with_dep() -> None:
    """Test trace show when behave-trace is installed."""
    if not TRACE_INSTALLED:
        pytest.skip("behave-trace not installed")
    result = runner.invoke(app, ["trace", "show"])
    assert result.exit_code in (0, 1, 2)


def test_trace_serve_with_dep() -> None:
    """Test trace serve when behave-trace is installed."""
    if not TRACE_INSTALLED:
        pytest.skip("behave-trace not installed")
    result = runner.invoke(app, ["trace", "serve"])
    assert result.exit_code in (0, 1, 2)


def test_trace_without_dep() -> None:
    """Test trace degrades gracefully when behave-trace not installed."""
    if TRACE_INSTALLED:
        pytest.skip("behave-trace is installed")
    result = runner.invoke(app, ["trace", "show"])
    assert result.exit_code == 2


def test_trace_help() -> None:
    """Test trace --help."""
    result = runner.invoke(app, ["trace", "--help"])
    assert result.exit_code == 0
    assert "trace" in result.stdout.lower()


def test_trace_no_args_shows_help() -> None:
    """Test trace with no args shows help (no_args_is_help=True)."""
    result = runner.invoke(app, ["trace"])
    assert result.exit_code == 0
    assert "trace" in result.stdout.lower()


def test_trace_show_help() -> None:
    """Test trace show --help."""
    result = runner.invoke(app, ["trace", "show", "--help"])
    assert result.exit_code == 0
    assert "show" in result.stdout.lower()


def test_trace_serve_help() -> None:
    """Test trace serve --help."""
    result = runner.invoke(app, ["trace", "serve", "--help"])
    assert result.exit_code == 0
    assert "serve" in result.stdout.lower()


def test_trace_help_lists_subcommands() -> None:
    """Test trace --help lists both subcommands."""
    result = runner.invoke(app, ["trace", "--help"])
    assert result.exit_code == 0
    assert "show" in result.stdout
    assert "serve" in result.stdout


@pytest.mark.skipif(TRACE_INSTALLED, reason="behave-trace is installed")
def test_trace_serve_without_dep() -> None:
    """Test trace serve degrades gracefully."""
    result = runner.invoke(app, ["trace", "serve"])
    assert result.exit_code == 2


@pytest.mark.skipif(TRACE_INSTALLED, reason="behave-trace is installed")
def test_trace_show_with_args_without_dep() -> None:
    """Test trace show with extra args degrades gracefully."""
    result = runner.invoke(app, ["trace", "show", "trace.json", "--port", "8080"])
    assert result.exit_code == 2


@pytest.mark.skipif(TRACE_INSTALLED, reason="behave-trace is installed")
def test_trace_serve_with_args_without_dep() -> None:
    """Test trace serve with extra args degrades gracefully."""
    result = runner.invoke(app, ["trace", "serve", "--port", "8080"])
    assert result.exit_code == 2
