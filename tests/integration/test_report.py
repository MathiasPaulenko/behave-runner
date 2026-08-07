"""Integration tests for behave-runner report command."""

from __future__ import annotations

import importlib.util
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
    "xlsx": "behave_modern_xlsx_report",
    "pdf": "behave_modern_pdf_report",
}


@pytest.mark.parametrize("fmt", ["console", "html", "md", "json", "xlsx", "pdf"])
def test_report_format(fmt: str) -> None:
    """Test each report format when its formatter is installed."""
    pkg_name = _FORMAT_PACKAGES[fmt]
    if not importlib.util.find_spec(pkg_name):
        pytest.skip(f"{pkg_name} not installed")
    result = runner.invoke(app, ["report", "generate", "--format", fmt, "tests/fixtures/minimal"])
    assert result.exit_code == 0


def test_report_without_dep() -> None:
    """Test report degrades gracefully when formatter not installed."""
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
