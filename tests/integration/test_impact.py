"""Integration tests for behave-runner impact command."""

from __future__ import annotations

import importlib.util
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from behave_runner.cli.app import app
from behave_runner.commands.impact import _extract_scenario_names

runner = CliRunner()


def test_impact_with_dep() -> None:
    """Test impact when behave-doctor is installed."""
    if not importlib.util.find_spec("behave_doctor"):
        pytest.skip("behave-doctor not installed")
    result = runner.invoke(app, ["impact", "tests/fixtures/minimal"])
    assert result.exit_code in (0, 1)


def test_impact_format_json() -> None:
    """Test impact --format json passes format to behave-doctor."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch("behave_runner.commands.impact.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        result = runner.invoke(app, ["impact", "tests/fixtures/minimal", "--format", "json"])
    assert result.exit_code == 0
    cmd = mock_run.call_args[0][0]
    assert "--format" in cmd
    assert "json" in cmd


def test_impact_format_sarif() -> None:
    """Test impact --format sarif passes format to behave-doctor."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch("behave_runner.commands.impact.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        result = runner.invoke(app, ["impact", "tests/fixtures/minimal", "--format", "sarif"])
    assert result.exit_code == 0
    cmd = mock_run.call_args[0][0]
    assert "--format" in cmd
    assert "sarif" in cmd


def test_impact_invalid_format() -> None:
    """Test impact with invalid format exits with code 2."""
    result = runner.invoke(app, ["impact", "tests/fixtures/minimal", "--format", "xml"])
    assert result.exit_code == 2
    assert "Unknown format" in result.output
    assert "xml" in result.output


def test_impact_without_dep() -> None:
    """Test impact degrades gracefully when behave-doctor not installed."""
    with patch("behave_runner.core.deps.is_installed", return_value=False):
        result = runner.invoke(app, ["impact", "tests/fixtures/minimal"])
    assert result.exit_code == 2
    assert "impact requires behave_doctor" in result.stdout


def test_impact_default_path() -> None:
    """Test impact with no path uses '.' as default."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch("behave_runner.commands.impact.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        runner.invoke(app, ["impact"])
    cmd = mock_run.call_args[0][0]
    assert "behave-doctor" in cmd
    assert "scan" in cmd
    assert "." in cmd


def test_impact_custom_path() -> None:
    """Test impact with custom path passes it to behave-doctor."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch("behave_runner.commands.impact.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        runner.invoke(app, ["impact", "src/"])
    cmd = mock_run.call_args[0][0]
    assert "src/" in cmd


def test_impact_format_passed_to_doctor() -> None:
    """Test --format is passed to behave-doctor scan."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch("behave_runner.commands.impact.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        runner.invoke(app, ["impact", "src/", "--format", "sarif"])
    cmd = mock_run.call_args[0][0]
    assert "--format" in cmd
    assert "sarif" in cmd


def test_impact_run_uses_json_internally() -> None:
    """Test --run forces JSON format internally for parsing."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch("behave_runner.commands.impact.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = '{"diagnostics": []}'
        runner.invoke(app, ["impact", "src/", "--run"])
    cmd = mock_run.call_args[0][0]
    assert "json" in cmd


def test_impact_run_no_scenarios() -> None:
    """Test --run with no affected scenarios prints message."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch("behave_runner.commands.impact.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = '{"diagnostics": []}'
        result = runner.invoke(app, ["impact", "src/", "--run"])
    assert result.exit_code == 0
    assert "No affected scenarios" in result.stdout


def test_impact_propagates_exit_code() -> None:
    """Test impact propagates behave-doctor exit code."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch("behave_runner.commands.impact.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 1
        result = runner.invoke(app, ["impact", "tests/fixtures/minimal"])
    assert result.exit_code == 1


def test_impact_file_not_found() -> None:
    """Test impact handles FileNotFoundError when CLI binary is missing."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch(
            "behave_runner.commands.impact.subprocess.run",
            side_effect=FileNotFoundError,
        ),
    ):
        result = runner.invoke(app, ["impact", "tests/fixtures/minimal"])
    assert result.exit_code == 2
    assert "behave-doctor not found" in result.stdout


def test_impact_os_error() -> None:
    """Test impact handles OSError gracefully."""
    with (
        patch("behave_runner.core.deps.is_installed", return_value=True),
        patch(
            "behave_runner.commands.impact.subprocess.run",
            side_effect=OSError("permission denied"),
        ),
    ):
        result = runner.invoke(app, ["impact", "tests/fixtures/minimal"])
    assert result.exit_code == 2
    assert "Error running behave-doctor" in result.stdout


def test_impact_help() -> None:
    """Test impact --help."""
    result = runner.invoke(app, ["impact", "--help"])
    assert result.exit_code == 0
    assert "impact" in result.stdout.lower()


# --- Unit tests for _extract_scenario_names ---


def test_extract_names_from_diagnostics() -> None:
    """Test extracting scenario names from behave-doctor diagnostics format."""
    stdout = (
        '{"diagnostics": ['
        '  {"metadata": {"scenario": "Login test"}},'
        '  {"metadata": {"scenario": "Logout test"}}'
        "]}"
    )
    names = _extract_scenario_names(stdout)
    assert names == ["Login test", "Logout test"]


def test_extract_names_dedup_not_needed() -> None:
    """Test that duplicate scenario names are preserved (each is a separate finding)."""
    stdout = (
        '{"diagnostics": ['
        '  {"metadata": {"scenario": "Login"}},'
        '  {"metadata": {"scenario": "Login"}}'
        "]}"
    )
    names = _extract_scenario_names(stdout)
    assert names == ["Login", "Login"]


def test_extract_names_empty_stdout() -> None:
    """Test empty stdout returns empty list."""
    assert _extract_scenario_names("") == []
    assert _extract_scenario_names("   ") == []


def test_extract_names_invalid_json() -> None:
    """Test invalid JSON returns empty list."""
    assert _extract_scenario_names("not json") == []


def test_extract_names_list_format() -> None:
    """Test extracting from a top-level list format."""
    stdout = '[{"scenario": "Test 1"}, {"scenario": "Test 2"}]'
    names = _extract_scenario_names(stdout)
    assert names == ["Test 1", "Test 2"]


def test_extract_names_findings_key() -> None:
    """Test extracting from 'findings' key (legacy format)."""
    stdout = '{"findings": [{"name": "Test 1"}]}'
    names = _extract_scenario_names(stdout)
    assert names == ["Test 1"]


def test_extract_names_no_scenario_field() -> None:
    """Test entries without scenario field are skipped."""
    stdout = '{"diagnostics": [{"rule_id": "BD101"}, {"metadata": {"count": 1}}]}'
    names = _extract_scenario_names(stdout)
    assert names == []


def test_extract_names_real_output() -> None:
    """Test with real behave-doctor JSON output structure."""
    stdout = (
        '{"diagnostics": ['
        '  {"metadata": {"scenario": "Successful login"}, "rule_id": "BD202"},'
        '  {"metadata": {"step": "I am on the login page"}, "rule_id": "BD302"},'
        '  {"metadata": {"count": 1}, "rule_id": "BD101"}'
        "]}"
    )
    names = _extract_scenario_names(stdout)
    assert names == ["Successful login"]
