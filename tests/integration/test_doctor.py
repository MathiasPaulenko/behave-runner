"""Integration tests for behave-runner doctor command."""

from __future__ import annotations

import importlib.util
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from behave_runner.cli.app import app

runner = CliRunner()


def test_doctor_with_dep() -> None:
    """Test doctor when behave-doctor is installed."""
    if not importlib.util.find_spec("behave_doctor"):
        pytest.skip("behave-doctor not installed")
    result = runner.invoke(app, ["doctor", "tests/fixtures/minimal"])
    assert result.exit_code in (0, 1)


def test_doctor_without_dep() -> None:
    """Test doctor degrades gracefully when behave-doctor not installed."""
    with patch("behave_runner.core.deps.is_installed", return_value=False):
        result = runner.invoke(app, ["doctor", "tests/fixtures/minimal"])
    assert result.exit_code == 2
    assert "doctor requires behave_doctor" in result.stdout


def test_doctor_passes_flags_through() -> None:
    """Test doctor passes -- flags through to behave-doctor."""
    if not importlib.util.find_spec("behave_doctor"):
        pytest.skip("behave-doctor not installed")
    with patch("behave_runner.commands.doctor.subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        runner.invoke(app, ["doctor", "tests/fixtures/minimal", "--fix"])
    assert mock_run.called
    cmd = mock_run.call_args[0][0]
    assert "--fix" in cmd
    assert "behave-doctor" in cmd
    assert "tests/fixtures/minimal" in cmd


def test_doctor_passes_multiple_flags() -> None:
    """Test doctor passes multiple -- flags through to behave-doctor."""
    if not importlib.util.find_spec("behave_doctor"):
        pytest.skip("behave-doctor not installed")
    with patch("behave_runner.commands.doctor.subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        runner.invoke(app, ["doctor", "--fix", "--verbose", "tests/fixtures/minimal"])
    cmd = mock_run.call_args[0][0]
    assert "--fix" in cmd
    assert "--verbose" in cmd
    assert "tests/fixtures/minimal" in cmd


def test_doctor_no_args() -> None:
    """Test doctor with no args calls behave-doctor with no extra args."""
    if not importlib.util.find_spec("behave_doctor"):
        pytest.skip("behave-doctor not installed")
    with patch("behave_runner.commands.doctor.subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        runner.invoke(app, ["doctor"])
    cmd = mock_run.call_args[0][0]
    assert cmd == ["behave-doctor"]


def test_doctor_propagates_exit_code() -> None:
    """Test doctor propagates behave-doctor exit code."""
    if not importlib.util.find_spec("behave_doctor"):
        pytest.skip("behave-doctor not installed")
    with patch("behave_runner.commands.doctor.subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        result = runner.invoke(app, ["doctor", "tests/fixtures/minimal"])
    assert result.exit_code == 1


def test_doctor_file_not_found() -> None:
    """Test doctor handles FileNotFoundError when CLI binary is missing."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch(
            "behave_runner.commands.doctor.subprocess.run",
            side_effect=FileNotFoundError,
        ),
    ):
        result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 2
    assert "behave-doctor not found" in result.stdout


def test_doctor_os_error() -> None:
    """Test doctor handles OSError gracefully."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch(
            "behave_runner.commands.doctor.subprocess.run",
            side_effect=OSError("permission denied"),
        ),
    ):
        result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 2
    assert "Error running behave-doctor" in result.stdout


def test_doctor_help() -> None:
    """Test doctor --help."""
    result = runner.invoke(app, ["doctor", "--help"])
    assert result.exit_code == 0
    assert "doctor" in result.stdout.lower()
