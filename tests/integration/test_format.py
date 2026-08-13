"""Integration tests for behave-runner format command."""

from __future__ import annotations

import importlib.util
from unittest.mock import patch

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


def test_format_diff() -> None:
    """Test format --diff when behave-format is installed."""
    if not importlib.util.find_spec("behave_format"):
        pytest.skip("behave-format not installed")
    result = runner.invoke(app, ["format", "--diff", "tests/fixtures/minimal/features"])
    assert result.exit_code in (0, 1)


def test_format_default() -> None:
    """Test format with no flags formats by default (no --in-place needed)."""
    if not importlib.util.find_spec("behave_format"):
        pytest.skip("behave-format not installed")
    with patch("behave_runner.commands.format_cmd.subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        runner.invoke(app, ["format", "tests/fixtures/minimal/features"])
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "behave-format"
    assert "--check" not in cmd
    assert "--diff" not in cmd
    assert "--in-place" not in cmd
    assert "tests/fixtures/minimal/features" in cmd


def test_format_check_flag_in_cmd() -> None:
    """Test --check is passed to behave-format."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch("behave_runner.commands.format_cmd.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        runner.invoke(app, ["format", "--check", "features/"])
    cmd = mock_run.call_args[0][0]
    assert "--check" in cmd


def test_format_diff_flag_in_cmd() -> None:
    """Test --diff is passed to behave-format."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch("behave_runner.commands.format_cmd.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        runner.invoke(app, ["format", "--diff", "features/"])
    cmd = mock_run.call_args[0][0]
    assert "--diff" in cmd


def test_format_passthrough_flags() -> None:
    """Test that unknown -- flags pass through to behave-format."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch("behave_runner.commands.format_cmd.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        runner.invoke(
            app, ["format", "--quiet", "--indent", "4", "tests/fixtures/minimal/features"]
        )
    cmd = mock_run.call_args[0][0]
    assert "--quiet" in cmd
    assert "--indent" in cmd
    assert "4" in cmd


def test_format_no_args() -> None:
    """Test format with no args calls behave-format with no extra args."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch("behave_runner.commands.format_cmd.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        runner.invoke(app, ["format"])
    cmd = mock_run.call_args[0][0]
    assert cmd == ["behave-format"]


def test_format_propagates_exit_code() -> None:
    """Test format propagates behave-format exit code."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch("behave_runner.commands.format_cmd.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 1
        result = runner.invoke(app, ["format", "tests/fixtures/minimal/features"])
    assert result.exit_code == 1


def test_format_without_dep() -> None:
    """Test format degrades gracefully when behave-format not installed."""
    with patch("behave_runner.core.deps.is_installed", return_value=False):
        result = runner.invoke(app, ["format", "tests/fixtures/minimal/features"])
    assert result.exit_code == 2
    assert "format requires behave_format" in result.stdout


def test_format_file_not_found() -> None:
    """Test format handles FileNotFoundError when CLI binary is missing."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch(
            "behave_runner.commands.format_cmd.subprocess.run",
            side_effect=FileNotFoundError,
        ),
    ):
        result = runner.invoke(app, ["format"])
    assert result.exit_code == 2
    assert "behave-format not found" in result.stdout


def test_format_os_error() -> None:
    """Test format handles OSError gracefully."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch(
            "behave_runner.commands.format_cmd.subprocess.run",
            side_effect=OSError("permission denied"),
        ),
    ):
        result = runner.invoke(app, ["format"])
    assert result.exit_code == 2
    assert "Error running behave-format" in result.stdout


def test_format_help() -> None:
    """Test format --help."""
    result = runner.invoke(app, ["format", "--help"])
    assert result.exit_code == 0
    assert "format" in result.stdout.lower()
