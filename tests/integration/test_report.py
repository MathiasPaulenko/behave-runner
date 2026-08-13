"""Integration tests for behave-runner report command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from behave_runner.cli.app import app
from behave_runner.core.orchestrator import RunConfig

runner = CliRunner()


# --- report generate ---


@pytest.mark.parametrize("fmt", ["console", "html", "md", "json", "sheets", "file"])
def test_report_generate_format(fmt: str) -> None:
    """Test each report format builds correct RunConfig."""
    with patch("behave_runner.commands.report.run", return_value=0) as mock_run:
        result = runner.invoke(
            app, ["report", "generate", "--format", fmt, "tests/fixtures/minimal"]
        )
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert isinstance(config, RunConfig)
    assert config.fmt == fmt
    assert len(config.features) == 1
    assert Path(config.features[0]).as_posix() == "tests/fixtures/minimal"


def test_report_generate_default_features() -> None:
    """Test report generate with no features uses 'features'."""
    with patch("behave_runner.commands.report.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["report", "generate"])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert config.features == ["features"]


def test_report_generate_default_format() -> None:
    """Test default format is console."""
    with patch("behave_runner.commands.report.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["report", "generate"])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert config.fmt == "console"


def test_report_generate_invalid_format() -> None:
    """Test invalid format shows error and exits with code 2."""
    result = runner.invoke(app, ["report", "generate", "--format", "xml", "tests/fixtures/minimal"])
    assert result.exit_code == 2
    assert "Unknown format" in result.output
    assert "xml" in result.output


def test_report_generate_output_creates_dir(tmp_path: Path) -> None:
    """Test --output creates the output directory."""
    out = tmp_path / "my_reports"
    with patch("behave_runner.commands.report.run", return_value=0):
        result = runner.invoke(
            app,
            ["report", "generate", "--format", "json", "--output", str(out)],
        )
    assert result.exit_code == 0
    assert out.exists()
    assert out.is_dir()


def test_report_generate_outfile_per_format(tmp_path: Path) -> None:
    """Test outfile path is constructed correctly for each format."""
    out = tmp_path / "reports"
    cases = {
        "json": "report.json",
        "html": "report.html",
        "md": "report.md",
        "sheets": "report.xlsx",
        "file": "report.docx",
    }
    for fmt, filename in cases.items():
        with patch("behave_runner.commands.report.run", return_value=0) as mock_run:
            runner.invoke(
                app,
                ["report", "generate", "--format", fmt, "--output", str(out)],
            )
        config = mock_run.call_args[0][0]
        assert config.outfile is not None
        assert config.outfile.endswith(filename)


def test_report_generate_console_no_outfile(tmp_path: Path) -> None:
    """Test console format does not set outfile even with --output."""
    out = tmp_path / "reports"
    with patch("behave_runner.commands.report.run", return_value=0) as mock_run:
        runner.invoke(
            app,
            ["report", "generate", "--format", "console", "--output", str(out)],
        )
    config = mock_run.call_args[0][0]
    assert config.outfile is None


def test_report_generate_no_output_no_outfile() -> None:
    """Test without --output, outfile is None."""
    with patch("behave_runner.commands.report.run", return_value=0) as mock_run:
        runner.invoke(app, ["report", "generate", "--format", "json"])
    config = mock_run.call_args[0][0]
    assert config.outfile is None


def test_report_generate_propagates_exit_code() -> None:
    """Test non-zero exit code from run() is propagated."""
    with patch("behave_runner.commands.report.run", return_value=1):
        result = runner.invoke(app, ["report", "generate"])
    assert result.exit_code == 1


# --- report show ---


def test_report_show_no_reports(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test report show when no reports exist."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["report", "show"])
    assert result.exit_code == 0
    assert "No reports" in result.stdout


def test_report_show_with_report(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test report show opens the latest report."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "report.html").write_text("<html></html>")
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.core.output.open_in_browser") as mock_open:
        result = runner.invoke(app, ["report", "show"])
    assert result.exit_code == 0
    assert "Opening" in result.stdout
    mock_open.assert_called_once()


def test_report_show_custom_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test report show --output uses custom directory."""
    custom = tmp_path / "custom_reports"
    custom.mkdir()
    (custom / "report.html").write_text("<html></html>")
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.core.output.open_in_browser") as mock_open:
        result = runner.invoke(app, ["report", "show", "--output", str(custom)])
    assert result.exit_code == 0
    assert "Opening" in result.stdout
    opened_path = mock_open.call_args[0][0]
    assert "custom_reports" in opened_path


# --- help ---


def test_report_help() -> None:
    """Test report --help."""
    result = runner.invoke(app, ["report", "--help"])
    assert result.exit_code == 0
    assert "report" in result.stdout.lower()
    assert "generate" in result.stdout
    assert "show" in result.stdout


def test_report_generate_help() -> None:
    """Test report generate --help."""
    result = runner.invoke(app, ["report", "generate", "--help"])
    assert result.exit_code == 0
    assert "generate" in result.stdout.lower()
    assert "--format" in result.stdout
    assert "--output" in result.stdout


def test_report_show_help() -> None:
    """Test report show --help."""
    result = runner.invoke(app, ["report", "show", "--help"])
    assert result.exit_code == 0
    assert "show" in result.stdout.lower()
    assert "--output" in result.stdout
