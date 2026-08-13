"""Integration tests for behave-runner lint command."""

from __future__ import annotations

import importlib.util
from unittest.mock import patch

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


def test_lint_no_args() -> None:
    """Test lint with no args calls behave-lint with no extra args."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch("behave_runner.core.deps.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        runner.invoke(app, ["lint"])
    cmd = mock_run.call_args[0][0]
    assert cmd == ["behave-lint"]


def test_lint_with_path() -> None:
    """Test lint passes path argument to behave-lint."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch("behave_runner.core.deps.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        runner.invoke(app, ["lint", "features/login.feature"])
    cmd = mock_run.call_args[0][0]
    assert "behave-lint" in cmd
    assert "features/login.feature" in cmd


def test_lint_passthrough_flags() -> None:
    """Test that unknown -- flags pass through to behave-lint."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch("behave_runner.core.deps.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        runner.invoke(
            app,
            ["lint", "features/", "--output", "json", "--fail-on", "error"],
        )
    cmd = mock_run.call_args[0][0]
    assert "behave-lint" in cmd
    assert "--output" in cmd
    assert "json" in cmd
    assert "--fail-on" in cmd
    assert "error" in cmd


def test_lint_passthrough_quiet() -> None:
    """Test --quiet flag passes through to behave-lint."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch("behave_runner.core.deps.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        runner.invoke(app, ["lint", "features/", "--quiet"])
    cmd = mock_run.call_args[0][0]
    assert "--quiet" in cmd


def test_lint_without_dep() -> None:
    """Test lint degrades gracefully when behave-lint not installed."""
    with patch("behave_runner.core.deps.is_installed", return_value=False):
        result = runner.invoke(app, ["lint", "tests/fixtures/minimal/features"])
    assert result.exit_code == 2
    assert "lint requires behave_lint" in result.stdout


def test_lint_propagates_exit_code() -> None:
    """Test lint propagates behave-lint exit code."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch("behave_runner.core.deps.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 1
        result = runner.invoke(app, ["lint", "tests/fixtures/minimal/features"])
    assert result.exit_code == 1


def test_lint_file_not_found() -> None:
    """Test lint handles FileNotFoundError when CLI binary is missing."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch(
            "behave_runner.core.deps.subprocess.run",
            side_effect=FileNotFoundError,
        ),
    ):
        result = runner.invoke(app, ["lint"])
    assert result.exit_code == 2
    assert "behave-lint not found" in result.stdout


def test_lint_os_error() -> None:
    """Test lint handles OSError gracefully."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch(
            "behave_runner.core.deps.subprocess.run",
            side_effect=OSError("permission denied"),
        ),
    ):
        result = runner.invoke(app, ["lint"])
    assert result.exit_code == 2
    assert "Error running behave-lint" in result.stdout


def test_lint_help() -> None:
    """Test lint --help."""
    result = runner.invoke(app, ["lint", "--help"])
    assert result.exit_code == 0
    assert "lint" in result.stdout.lower()
