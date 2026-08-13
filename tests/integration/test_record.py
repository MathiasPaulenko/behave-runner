"""Integration tests for behave-runner record command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from behave_runner.cli.app import app

runner = CliRunner()


def test_record_cmd_construction(tmp_path: Path) -> None:
    """Test record builds correct wavexis command."""
    with (
        patch("behave_runner.core.deps.is_installed", side_effect=[True, False]),
        patch("behave_runner.commands.record.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        runner.invoke(app, ["record", "https://example.com"])
    cmd = mock_run.call_args_list[0][0][0]
    assert cmd[0] == "wavexis"
    assert "record" in cmd
    assert "https://example.com" in cmd
    assert "--output" in cmd
    assert "--interactive" in cmd


def test_record_default_url(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test record with no URL uses about:blank."""
    monkeypatch.chdir(tmp_path)
    with (
        patch("behave_runner.core.deps.is_installed", side_effect=[True, False]),
        patch("behave_runner.commands.record.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        runner.invoke(app, ["record"])
    cmd = mock_run.call_args_list[0][0][0]
    assert "about:blank" in cmd


def test_record_custom_output(tmp_path: Path) -> None:
    """Test --output specifies custom directory."""
    custom = tmp_path / "custom_recordings"
    with (
        patch("behave_runner.core.deps.is_installed", side_effect=[True, False]),
        patch("behave_runner.commands.record.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        runner.invoke(app, ["record", "--output", str(custom)])
    cmd = mock_run.call_args_list[0][0][0]
    output_idx = cmd.index("--output")
    assert str(custom) in cmd[output_idx + 1]
    assert custom.exists()


def test_record_custom_name(tmp_path: Path) -> None:
    """Test --name specifies recording file name."""
    with (
        patch("behave_runner.core.deps.is_installed", side_effect=[True, False]),
        patch("behave_runner.commands.record.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        runner.invoke(app, ["record", "--name", "login_flow"])
    cmd = mock_run.call_args_list[0][0][0]
    output_idx = cmd.index("--output")
    assert "login_flow.yaml" in cmd[output_idx + 1]


def test_record_invalid_name_with_slash() -> None:
    """Test --name with path separator exits with code 2."""
    result = runner.invoke(app, ["record", "--name", "invalid/name"])
    assert result.exit_code == 2
    assert "must be a simple file name" in result.output


def test_record_invalid_name_empty() -> None:
    """Test --name with whitespace only exits with code 2."""
    result = runner.invoke(app, ["record", "--name", "   "])
    assert result.exit_code == 2
    assert "must be a simple file name" in result.output


def test_record_without_wavexis_dep() -> None:
    """Test record degrades gracefully when wavexis not installed."""
    with patch("behave_runner.core.deps.is_installed", return_value=False):
        result = runner.invoke(app, ["record"])
    assert result.exit_code == 2
    assert "record requires wavexis" in result.stdout


def test_record_wavexis_file_not_found() -> None:
    """Test record handles FileNotFoundError when wavexis binary is missing."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch(
            "behave_runner.commands.record.subprocess.run",
            side_effect=FileNotFoundError,
        ),
    ):
        result = runner.invoke(app, ["record"])
    assert result.exit_code == 2
    assert "wavexis not found" in result.stdout


def test_record_wavexis_os_error() -> None:
    """Test record handles OSError from wavexis."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch(
            "behave_runner.commands.record.subprocess.run",
            side_effect=OSError("permission denied"),
        ),
    ):
        result = runner.invoke(app, ["record"])
    assert result.exit_code == 2
    assert "Error running wavexis" in result.stdout


def test_record_wavexis_failure_exit_code() -> None:
    """Test record propagates wavexis non-zero exit code."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch("behave_runner.commands.record.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 1
        result = runner.invoke(app, ["record"])
    assert result.exit_code == 1
    assert "Recording failed" in result.stdout


def test_record_gen_skipped_when_missing(tmp_path: Path) -> None:
    """Test step generation is skipped when behave-gen not installed."""
    with (
        patch("behave_runner.core.deps.is_installed", side_effect=[True, False]),
        patch("behave_runner.commands.record.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        result = runner.invoke(app, ["record"])
    assert result.exit_code == 0
    assert "behave-gen not installed" in result.stdout
    assert "Skipping step generation" in result.stdout
    assert mock_run.call_count == 1


def test_record_gen_success(tmp_path: Path) -> None:
    """Test full flow: wavexis succeeds, behave-gen succeeds."""
    with (
        patch("behave_runner.core.deps.is_installed", side_effect=[True, True]),
        patch("behave_runner.commands.record.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        result = runner.invoke(app, ["record"])
    assert result.exit_code == 0
    assert mock_run.call_count == 2
    gen_cmd = mock_run.call_args_list[1][0][0]
    assert "behave-gen" in gen_cmd
    assert "add" in gen_cmd
    assert "steps" in gen_cmd
    assert "--from-recording" in gen_cmd


def test_record_gen_file_not_found() -> None:
    """Test behave-gen FileNotFoundError after successful recording."""
    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:

            class R:
                returncode = 0

            return R()
        raise FileNotFoundError

    with (
        patch("behave_runner.core.deps.is_installed", side_effect=[True, True]),
        patch(
            "behave_runner.commands.record.subprocess.run",
            side_effect=side_effect,
        ),
    ):
        result = runner.invoke(app, ["record"])
    assert result.exit_code == 2
    assert "behave-gen not found" in result.stdout


def test_record_gen_os_error() -> None:
    """Test behave-gen OSError after successful recording."""
    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:

            class R:
                returncode = 0

            return R()
        raise OSError("permission denied")

    with (
        patch("behave_runner.core.deps.is_installed", side_effect=[True, True]),
        patch(
            "behave_runner.commands.record.subprocess.run",
            side_effect=side_effect,
        ),
    ):
        result = runner.invoke(app, ["record"])
    assert result.exit_code == 2
    assert "Error running behave-gen" in result.stdout


def test_record_gen_propagates_exit_code() -> None:
    """Test behave-gen non-zero exit code is propagated."""
    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:

            class R:
                returncode = 0

            return R()

        class R2:
            returncode = 3

        return R2()

    with (
        patch("behave_runner.core.deps.is_installed", side_effect=[True, True]),
        patch(
            "behave_runner.commands.record.subprocess.run",
            side_effect=side_effect,
        ),
    ):
        result = runner.invoke(app, ["record"])
    assert result.exit_code == 3


def test_record_help() -> None:
    """Test record --help."""
    result = runner.invoke(app, ["record", "--help"])
    assert result.exit_code == 0
    assert "record" in result.stdout.lower()
    assert "--output" in result.stdout
    assert "--name" in result.stdout
