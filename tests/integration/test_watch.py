"""Integration tests for behave-runner watch command."""

from __future__ import annotations

from typer.testing import CliRunner

from behave_runner.cli.app import app

runner = CliRunner()


def test_watch_help() -> None:
    """Test watch --help."""
    result = runner.invoke(app, ["watch", "--help"])
    assert result.exit_code == 0
    assert "watch" in result.stdout.lower()


def test_watch_debounce_option() -> None:
    """Test --debounce option is accepted."""
    result = runner.invoke(app, ["watch", "--help"])
    assert result.exit_code == 0
    assert "debounce" in result.stdout.lower()


def test_watch_pattern_option() -> None:
    """Test --pattern option is accepted."""
    result = runner.invoke(app, ["watch", "--help"])
    assert result.exit_code == 0
    assert "pattern" in result.stdout.lower()
