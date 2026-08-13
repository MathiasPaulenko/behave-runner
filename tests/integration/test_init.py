"""Integration tests for behave-runner init command."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from behave_runner.cli.app import app

runner = CliRunner()


def test_init_creates_structure(tmp_path: Path, monkeypatch) -> None:
    """Test init creates project structure when behave-gen is installed."""
    if not importlib.util.find_spec("behave_gen"):
        pytest.skip("behave-gen not installed")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "--name", "myproject"])
    assert result.exit_code == 0
    assert (tmp_path / "myproject" / "features").exists()


def test_init_cmd_construction() -> None:
    """Test init builds correct behave-gen command with --name as positional."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch("behave_runner.commands.init.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        runner.invoke(app, ["init", "--name", "myproject"])
    cmd = mock_run.call_args[0][0]
    assert cmd == ["behave-gen", "init", "myproject"]


def test_init_passes_extra_args() -> None:
    """Test init passes extra positional args to behave-gen."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch("behave_runner.commands.init.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        runner.invoke(app, ["init", "--name", "myproject", "--template", "minimal"])
    cmd = mock_run.call_args[0][0]
    assert "behave-gen" in cmd
    assert "init" in cmd
    assert "myproject" in cmd
    assert "--template" in cmd
    assert "minimal" in cmd


def test_init_missing_name() -> None:
    """Test init without --name exits with code 2."""
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 2
    assert "Missing option '--name'" in result.output


def test_init_without_dep() -> None:
    """Test init degrades gracefully when behave-gen not installed."""
    with patch("behave_runner.core.deps.is_installed", return_value=False):
        result = runner.invoke(app, ["init", "--name", "myproject"])
    assert result.exit_code == 2
    assert "init requires behave_gen" in result.stdout


def test_init_propagates_exit_code() -> None:
    """Test init propagates behave-gen exit code."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch("behave_runner.commands.init.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 1
        result = runner.invoke(app, ["init", "--name", "myproject"])
    assert result.exit_code == 1


def test_init_file_not_found() -> None:
    """Test init handles FileNotFoundError when CLI binary is missing."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch(
            "behave_runner.commands.init.subprocess.run",
            side_effect=FileNotFoundError,
        ),
    ):
        result = runner.invoke(app, ["init", "--name", "myproject"])
    assert result.exit_code == 2
    assert "behave-gen not found" in result.stdout


def test_init_os_error() -> None:
    """Test init handles OSError gracefully."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch(
            "behave_runner.commands.init.subprocess.run",
            side_effect=OSError("permission denied"),
        ),
    ):
        result = runner.invoke(app, ["init", "--name", "myproject"])
    assert result.exit_code == 2
    assert "Error running behave-gen" in result.stdout


def test_init_help() -> None:
    """Test init --help."""
    result = runner.invoke(app, ["init", "--help"])
    assert result.exit_code == 0
    assert "init" in result.stdout.lower()
    assert "--name" in result.stdout
