"""Integration tests for behave-runner generate command."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from behave_runner.cli.app import app

runner = CliRunner()


def test_generate_step(tmp_path: Path, monkeypatch) -> None:
    """Test generate step when behave-gen is installed."""
    if not importlib.util.find_spec("behave_gen"):
        pytest.skip("behave-gen not installed")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["generate", "step", "--lib", "http"])
    assert result.exit_code == 0


def test_generate_feature(tmp_path: Path, monkeypatch) -> None:
    """Test generate feature when behave-gen is installed."""
    if not importlib.util.find_spec("behave_gen"):
        pytest.skip("behave-gen not installed")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["generate", "feature", "Login"])
    assert result.exit_code == 0


def test_generate_feature_with_tags(tmp_path: Path, monkeypatch) -> None:
    """Test generate feature with --tags passes tags to behave-gen."""
    if not importlib.util.find_spec("behave_gen"):
        pytest.skip("behave-gen not installed")
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.core.deps.subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        runner.invoke(app, ["generate", "feature", "Login", "--tags", "@smoke,@auth"])
    cmd = mock_run.call_args[0][0]
    assert "behave-gen" in cmd
    assert "add" in cmd
    assert "feature" in cmd
    assert "Login" in cmd
    assert "--tags" in cmd
    assert "@smoke,@auth" in cmd


def test_generate_step_cmd_construction() -> None:
    """Test generate step builds correct behave-gen command."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch("behave_runner.core.deps.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        runner.invoke(app, ["generate", "step", "--lib", "auth"])
    cmd = mock_run.call_args[0][0]
    assert cmd == ["behave-gen", "add", "steps", "--lib", "auth"]


def test_generate_feature_cmd_construction() -> None:
    """Test generate feature builds correct behave-gen command."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch("behave_runner.core.deps.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        runner.invoke(app, ["generate", "feature", "Logout"])
    cmd = mock_run.call_args[0][0]
    assert cmd == ["behave-gen", "add", "feature", "Logout"]


def test_generate_feature_no_tags_no_flag() -> None:
    """Test generate feature without --tags doesn't add --tags flag."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch("behave_runner.core.deps.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        runner.invoke(app, ["generate", "feature", "Login"])
    cmd = mock_run.call_args[0][0]
    assert "--tags" not in cmd


def test_generate_step_missing_lib() -> None:
    """Test generate step without --lib exits with code 2."""
    result = runner.invoke(app, ["generate", "step"])
    assert result.exit_code == 2
    assert "Missing option '--lib'" in result.output


def test_generate_feature_missing_name() -> None:
    """Test generate feature without name exits with code 2."""
    result = runner.invoke(app, ["generate", "feature"])
    assert result.exit_code == 2
    assert "missing argument 'name'" in result.output.lower()


def test_generate_without_dep() -> None:
    """Test generate degrades gracefully when behave-gen not installed."""
    with patch("behave_runner.core.deps.is_installed", return_value=False):
        result = runner.invoke(app, ["generate", "step", "--lib", "http"])
    assert result.exit_code == 2
    assert "generate requires behave_gen" in result.stdout


def test_generate_feature_without_dep() -> None:
    """Test generate feature degrades gracefully when behave-gen not installed."""
    with patch("behave_runner.core.deps.is_installed", return_value=False):
        result = runner.invoke(app, ["generate", "feature", "Login"])
    assert result.exit_code == 2
    assert "generate requires behave_gen" in result.stdout


def test_generate_propagates_exit_code() -> None:
    """Test generate propagates behave-gen exit code."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch("behave_runner.core.deps.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 1
        result = runner.invoke(app, ["generate", "step", "--lib", "http"])
    assert result.exit_code == 1


def test_generate_file_not_found() -> None:
    """Test generate handles FileNotFoundError when CLI binary is missing."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch(
            "behave_runner.core.deps.subprocess.run",
            side_effect=FileNotFoundError,
        ),
    ):
        result = runner.invoke(app, ["generate", "step", "--lib", "http"])
    assert result.exit_code == 2
    assert "behave-gen not found" in result.stdout


def test_generate_os_error() -> None:
    """Test generate handles OSError gracefully."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch(
            "behave_runner.core.deps.subprocess.run",
            side_effect=OSError("permission denied"),
        ),
    ):
        result = runner.invoke(app, ["generate", "step", "--lib", "http"])
    assert result.exit_code == 2
    assert "Error running behave-gen" in result.stdout


def test_generate_help() -> None:
    """Test generate --help."""
    result = runner.invoke(app, ["generate", "--help"])
    assert result.exit_code == 0
    assert "generate" in result.stdout.lower()


def test_generate_step_help() -> None:
    """Test generate step --help."""
    result = runner.invoke(app, ["generate", "step", "--help"])
    assert result.exit_code == 0
    assert "--lib" in result.stdout


def test_generate_feature_help() -> None:
    """Test generate feature --help."""
    result = runner.invoke(app, ["generate", "feature", "--help"])
    assert result.exit_code == 0
    assert "--tags" in result.stdout
