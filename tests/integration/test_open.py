"""Integration tests for behave-runner open command."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from behave_runner.cli.app import app

runner = CliRunner()


def test_open_no_reports(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test open with no reports shows friendly message."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["open"])
    assert result.exit_code == 0
    assert "No reports" in result.stdout or "not found" in result.stdout.lower()


def test_open_with_report(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test open finds and opens the latest report."""
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "report.html").write_text("<html></html>")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["open"])
    assert result.exit_code == 0


def test_open_report_alias(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test open report is alias for open."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["open", "report"])
    assert result.exit_code == 0
    assert "No reports" in result.stdout or "not found" in result.stdout.lower()


def test_open_trace_without_dep() -> None:
    """Test open trace degrades gracefully when behave-trace not installed."""
    result = runner.invoke(app, ["open", "trace"])
    assert result.exit_code in (0, 2)


def test_open_help() -> None:
    """Test open --help."""
    result = runner.invoke(app, ["open", "--help"])
    assert result.exit_code == 0
    assert "open" in result.stdout.lower()
