"""Integration tests for behave-runner report command."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from behave_runner.cli.app import app

runner = CliRunner()

_FORMAT_PACKAGES = {
    "console": "behave_modern_console_report",
    "html": "behave_modern_html_report",
    "md": "behave_modern_md_report",
    "json": "behave_modern_json_report",
    "sheets": "behave_modern_sheets_report",
}

_FORMAT_CMDS = {
    "console": "behave-modern-console-report",
    "html": "behave-modern-html-report",
    "md": "behave-modern-md-report",
    "json": "behave-modern-json-report",
    "sheets": "behave-modern-sheets-report",
}


@pytest.mark.parametrize("fmt", ["console", "html", "md", "json", "sheets"])
def test_report_format(fmt: str) -> None:
    """Test each report format when its formatter CLI is available."""
    cmd = _FORMAT_CMDS[fmt]
    if not shutil.which(cmd):
        pytest.skip(f"{cmd} CLI not available")
    result = runner.invoke(app, ["report", "generate", "--format", fmt, "tests/fixtures/minimal"])
    assert result.exit_code == 0


def test_report_without_dep() -> None:
    """Test report degrades gracefully when formatter CLI not available."""
    result = runner.invoke(
        app, ["report", "generate", "--format", "json", "tests/fixtures/minimal"]
    )
    assert result.exit_code in (0, 2)


def test_report_invalid_format() -> None:
    """Test invalid format shows error."""
    result = runner.invoke(app, ["report", "generate", "--format", "xml", "tests/fixtures/minimal"])
    assert result.exit_code == 2


def test_report_help() -> None:
    """Test report --help."""
    result = runner.invoke(app, ["report", "--help"])
    assert result.exit_code == 0
    assert "report" in result.stdout.lower()


def test_report_show_no_reports(tmp_path: Path, monkeypatch) -> None:
    """Test report show when no reports exist."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["report", "show"])
    assert result.exit_code == 0
    assert "No reports" in result.stdout or "not found" in result.stdout.lower()


def test_report_show_with_report(tmp_path: Path, monkeypatch) -> None:
    """Test report show opens the latest report."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "report.html").write_text("<html></html>")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["report", "show"])
    assert result.exit_code == 0
    assert "Opening" in result.stdout
