"""Integration tests for behave-runner open command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from behave_runner.cli.app import app

runner = CliRunner()


# --- open report ---


def test_open_no_reports(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test open with no reports shows friendly message."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["open"])
    assert result.exit_code == 0
    assert "No reports" in result.stdout


def test_open_with_report(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test open finds and opens the latest report."""
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "report.html").write_text("<html></html>")
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.core.output.open_in_browser") as mock_open:
        result = runner.invoke(app, ["open"])
    assert result.exit_code == 0
    assert "Opening" in result.stdout
    mock_open.assert_called_once()


def test_open_report_alias(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test open report is alias for open."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["open", "report"])
    assert result.exit_code == 0
    assert "No reports" in result.stdout


def test_open_custom_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test --output specifies custom report directory."""
    custom = tmp_path / "custom_reports"
    custom.mkdir()
    (custom / "latest.html").write_text("<html></html>")
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.core.output.open_in_browser"):
        result = runner.invoke(app, ["open", "--output", str(custom)])
    assert result.exit_code == 0
    assert "Opening" in result.stdout


def test_open_latest_report_by_mtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test open picks the most recently modified report."""
    reports = tmp_path / "reports"
    reports.mkdir()
    old = reports / "old.html"
    old.write_text("<html>old</html>")
    import time

    time.sleep(0.1)
    new = reports / "new.html"
    new.write_text("<html>new</html>")
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.core.output.open_in_browser") as mock_open:
        result = runner.invoke(app, ["open"])
    assert result.exit_code == 0
    opened_path = mock_open.call_args[0][0]
    assert "new.html" in opened_path


# --- open trace ---


def test_open_trace_without_dep() -> None:
    """Test open trace degrades gracefully when behave-trace not installed."""
    with patch("behave_runner.core.deps.is_installed", return_value=False):
        result = runner.invoke(app, ["open", "trace"])
    assert result.exit_code == 2
    assert "trace requires behave_trace" in result.stdout


def test_open_trace_with_dep_no_trace_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test open trace warns when trace.json not found but still runs."""
    monkeypatch.chdir(tmp_path)
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch("behave_runner.commands.open_cmd.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        result = runner.invoke(app, ["open", "trace"])
    assert result.exit_code == 0
    assert "trace.json not found" in result.stdout
    cmd = mock_run.call_args[0][0]
    assert cmd == ["behave-trace", "show"]


def test_open_trace_with_trace_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test open trace passes trace.json to behave-trace show."""
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "trace.json").write_text("{}")
    monkeypatch.chdir(tmp_path)
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch("behave_runner.commands.open_cmd.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        result = runner.invoke(app, ["open", "trace"])
    assert result.exit_code == 0
    cmd = mock_run.call_args[0][0]
    assert "behave-trace" in cmd
    assert "show" in cmd
    assert any("trace.json" in c for c in cmd)


def test_open_trace_propagates_exit_code() -> None:
    """Test open trace propagates behave-trace exit code."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch("behave_runner.commands.open_cmd.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 1
        result = runner.invoke(app, ["open", "trace"])
    assert result.exit_code == 1


def test_open_trace_file_not_found() -> None:
    """Test open trace handles FileNotFoundError."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch(
            "behave_runner.commands.open_cmd.subprocess.run",
            side_effect=FileNotFoundError,
        ),
    ):
        result = runner.invoke(app, ["open", "trace"])
    assert result.exit_code == 2
    assert "behave-trace not found" in result.stdout


def test_open_trace_os_error() -> None:
    """Test open trace handles OSError gracefully."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch(
            "behave_runner.commands.open_cmd.subprocess.run",
            side_effect=OSError("permission denied"),
        ),
    ):
        result = runner.invoke(app, ["open", "trace"])
    assert result.exit_code == 2
    assert "Error running behave-trace" in result.stdout


# --- edge cases ---


def test_open_invalid_target() -> None:
    """Test open with invalid target exits with code 2."""
    result = runner.invoke(app, ["open", "invalid"])
    assert result.exit_code == 2
    assert "invalid" in result.output


def test_open_help() -> None:
    """Test open --help."""
    result = runner.invoke(app, ["open", "--help"])
    assert result.exit_code == 0
    assert "open" in result.stdout.lower()
    assert "report" in result.stdout
    assert "trace" in result.stdout
    assert "--output" in result.stdout
