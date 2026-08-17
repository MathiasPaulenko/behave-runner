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


def test_watch_negative_debounce_exits_2() -> None:
    """Test --debounce with negative value exits with code 2."""
    result = runner.invoke(app, ["watch", "--debounce", "-1"])
    assert result.exit_code == 2
    assert "non-negative" in result.stdout


def test_watch_help_lists_all_options() -> None:
    """Test watch --help lists all expected options."""
    result = runner.invoke(app, ["watch", "--help"])
    assert result.exit_code == 0
    for opt in [
        "--tags",
        "--debounce",
        "--pattern",
        "--profile",
        "--retries",
        "--parallel",
        "--format",
        "--ui",
        "--debug",
        "--trace",
        "--priority-order",
        "--fail-fast",
        "--scenario-timeout",
    ]:
        assert opt in result.stdout, f"Missing {opt} in help output"


def test_watch_help_shows_usage() -> None:
    """Test watch --help shows usage with features argument."""
    result = runner.invoke(app, ["watch", "--help"])
    assert result.exit_code == 0
    assert "features" in result.stdout.lower()
    assert "Feature paths to watch and run" in result.stdout
