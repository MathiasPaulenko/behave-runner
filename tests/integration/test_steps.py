"""Integration tests for behave-runner steps command."""

from __future__ import annotations

import importlib.util

import pytest
from typer.testing import CliRunner

from behave_runner.cli.app import app

runner = CliRunner()

STEPLIB_INSTALLED = importlib.util.find_spec("behave_steplib") is not None


def test_steps_list_with_dep() -> None:
    """Test steps list when behave-steplib is installed."""
    if not STEPLIB_INSTALLED:
        pytest.skip("behave-steplib not installed")
    result = runner.invoke(app, ["steps", "list"])
    assert result.exit_code in (0, 1)


def test_steps_without_dep() -> None:
    """Test steps degrades gracefully when behave-steplib not installed."""
    if STEPLIB_INSTALLED:
        pytest.skip("behave-steplib is installed")
    result = runner.invoke(app, ["steps", "list"])
    assert result.exit_code == 2


def test_steps_help() -> None:
    """Test steps --help."""
    result = runner.invoke(app, ["steps", "--help"])
    assert result.exit_code == 0
    assert "steps" in result.stdout.lower()


def test_steps_no_args_shows_help() -> None:
    """Test steps with no args shows help (no_args_is_help=True)."""
    result = runner.invoke(app, ["steps"])
    assert result.exit_code == 0
    assert "steps" in result.stdout.lower()


# --- Subcommand help ---


def test_steps_list_help() -> None:
    """Test steps list --help."""
    result = runner.invoke(app, ["steps", "list", "--help"])
    assert result.exit_code == 0
    assert "list" in result.stdout.lower()


def test_steps_show_help() -> None:
    """Test steps show --help."""
    result = runner.invoke(app, ["steps", "show", "--help"])
    assert result.exit_code == 0
    assert "show" in result.stdout.lower()


def test_steps_search_help() -> None:
    """Test steps search --help."""
    result = runner.invoke(app, ["steps", "search", "--help"])
    assert result.exit_code == 0
    assert "search" in result.stdout.lower()


def test_steps_validate_help() -> None:
    """Test steps validate --help."""
    result = runner.invoke(app, ["steps", "validate", "--help"])
    assert result.exit_code == 0
    assert "validate" in result.stdout.lower()


def test_steps_init_help() -> None:
    """Test steps init --help."""
    result = runner.invoke(app, ["steps", "init", "--help"])
    assert result.exit_code == 0
    assert "init" in result.stdout.lower()


def test_steps_install_help() -> None:
    """Test steps install --help."""
    result = runner.invoke(app, ["steps", "install", "--help"])
    assert result.exit_code == 0
    assert "install" in result.stdout.lower()


# --- Graceful degradation when steplib not installed ---


@pytest.mark.skipif(STEPLIB_INSTALLED, reason="behave-steplib is installed")
def test_steps_show_without_dep() -> None:
    """Test steps show degrades gracefully."""
    result = runner.invoke(app, ["steps", "show", "some pattern"])
    assert result.exit_code == 2


@pytest.mark.skipif(STEPLIB_INSTALLED, reason="behave-steplib is installed")
def test_steps_search_without_dep() -> None:
    """Test steps search degrades gracefully."""
    result = runner.invoke(app, ["steps", "search", "auth"])
    assert result.exit_code == 2


@pytest.mark.skipif(STEPLIB_INSTALLED, reason="behave-steplib is installed")
def test_steps_validate_without_dep() -> None:
    """Test steps validate degrades gracefully."""
    result = runner.invoke(app, ["steps", "validate"])
    assert result.exit_code == 2


@pytest.mark.skipif(STEPLIB_INSTALLED, reason="behave-steplib is installed")
def test_steps_init_without_dep() -> None:
    """Test steps init degrades gracefully."""
    result = runner.invoke(app, ["steps", "init"])
    assert result.exit_code == 2


@pytest.mark.skipif(STEPLIB_INSTALLED, reason="behave-steplib is installed")
def test_steps_install_without_dep() -> None:
    """Test steps install degrades gracefully."""
    result = runner.invoke(app, ["steps", "install", "http"])
    assert result.exit_code == 2


# --- Subcommands listed in help ---


def test_steps_help_lists_all_subcommands() -> None:
    """Test steps --help lists all 6 subcommands."""
    result = runner.invoke(app, ["steps", "--help"])
    assert result.exit_code == 0
    assert "list" in result.stdout
    assert "show" in result.stdout
    assert "search" in result.stdout
    assert "validate" in result.stdout
    assert "init" in result.stdout
    assert "install" in result.stdout
