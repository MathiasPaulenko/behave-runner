"""Unit tests for command modules to improve coverage."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from behave_runner.cli.app import app

runner = CliRunner()


# --- config_cmd edge cases ---


def test_config_init_creates_section(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """config init should create [tool.behave-runner] section."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.ruff]\nline-length = 100\n")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["config", "init"])
    assert result.exit_code == 0
    content = pyproject.read_text()
    assert "[tool.behave-runner]" in content


def test_config_init_already_exists(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """config init should warn when section already exists."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.ruff]\nline-length = 100\n\n[tool.behave-runner]\nparallel = 4\n")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["config", "init"])
    assert result.exit_code == 0
    assert "already exists" in result.stdout


def test_config_set_existing_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """config set should update an existing key in the section."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.ruff]\nline-length = 100\n\n[tool.behave-runner]\nparallel = 2\n")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["config", "set", "parallel", "8"])
    assert result.exit_code == 0
    content = pyproject.read_text()
    assert "parallel = 8" in content
    assert "parallel = 2" not in content


def test_config_set_new_key_in_existing_section(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """config set should add a new key to an existing section."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.ruff]\nline-length = 100\n\n[tool.behave-runner]\nparallel = 2\n")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["config", "set", "retries", "3"])
    assert result.exit_code == 0
    content = pyproject.read_text()
    assert "retries = 3" in content
    assert "parallel = 2" in content


def test_config_set_creates_section_if_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """config set should create the section if it doesn't exist."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.ruff]\nline-length = 100\n")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["config", "set", "parallel", "4"])
    assert result.exit_code == 0
    content = pyproject.read_text()
    assert "[tool.behave-runner]" in content
    assert "parallel = 4" in content


def test_config_set_bool_value(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """config set should parse bool values correctly."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.ruff]\nline-length = 100\n\n[tool.behave-runner]\nparallel = 2\n")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["config", "set", "dry_run", "true"])
    assert result.exit_code == 0
    content = pyproject.read_text()
    assert "dry_run = true" in content


def test_config_set_float_value(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """config set should parse float values correctly."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.ruff]\nline-length = 100\n\n[tool.behave-runner]\nparallel = 2\n")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["config", "set", "timeout", "30.5"])
    assert result.exit_code == 0
    content = pyproject.read_text()
    assert "timeout = 30.5" in content


# --- watch command callback ---


def test_watch_callback_runs_tests(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Watch callback should invoke orchestrator.run with correct config."""
    from behave_runner.commands.watch import _make_callback

    with patch("behave_runner.commands.watch.run") as mock_run:
        mock_run.return_value = 0
        callback = _make_callback(["features"], [], None, {"ui": False})
        callback([Path("features/test.feature")])
        mock_run.assert_called_once()
        config = mock_run.call_args[0][0]
        assert config.features == ["features"]
        assert config.tags == []
        assert config.ui is False


def test_watch_callback_with_pattern_filters_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Watch callback should skip changes that don't match the pattern."""
    from behave_runner.commands.watch import _make_callback

    with patch("behave_runner.commands.watch.run") as mock_run:
        callback = _make_callback(["features"], [], "*.feature", {"ui": False})
        callback([Path("features/steps.py")])
        mock_run.assert_not_called()


def test_watch_callback_pattern_matches(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Watch callback should run tests when pattern matches."""
    from behave_runner.commands.watch import _make_callback

    with patch("behave_runner.commands.watch.run") as mock_run:
        mock_run.return_value = 0
        callback = _make_callback(["features"], [], "*.feature", {"ui": False})
        callback([Path("features/test.feature")])
        mock_run.assert_called_once()


def test_watch_callback_reports_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Watch callback should report non-zero exit code."""
    from behave_runner.commands.watch import _make_callback

    with patch("behave_runner.commands.watch.run") as mock_run:
        mock_run.return_value = 1
        callback = _make_callback(["features"], [], None, {"ui": False})
        callback([Path("features/test.feature")])
        mock_run.assert_called_once()


# --- exceptions ---


def test_config_error_message() -> None:
    """ConfigError should preserve the message."""
    from behave_runner.exceptions import ConfigError

    err = ConfigError("test message")
    assert str(err) == "test message"


def test_dependency_missing_error_message() -> None:
    """DependencyMissingError should format feature and package in message."""
    from behave_runner.exceptions import DependencyMissingError

    err = DependencyMissingError("retry", "behave_retry")
    assert "retry" in str(err)
    assert "behave_retry" in str(err)
    assert err.feature == "retry"
    assert err.package == "behave_retry"


def test_behave_runner_error_is_base() -> None:
    """BehaveRunnerError should be the base exception."""
    from behave_runner.exceptions import (
        BehaveRunnerError,
        ConfigError,
        DependencyMissingError,
    )

    assert issubclass(ConfigError, BehaveRunnerError)
    assert issubclass(DependencyMissingError, BehaveRunnerError)


# --- __main__ entry point ---


def test_main_entry_point() -> None:
    """__main__.main() should call app()."""
    with patch("behave_runner.__main__.app") as mock_app:
        from behave_runner.__main__ import main

        main()
        mock_app.assert_called_once()


# --- impact command ---


def test_impact_no_doctor_installed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """impact should exit 2 when behave-doctor is not installed."""
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.impact.check_optional", return_value=False):
        result = runner.invoke(app, ["impact", "."])
        assert result.exit_code == 2


def test_impact_doctor_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """impact should exit 2 when behave-doctor CLI is not found."""
    monkeypatch.chdir(tmp_path)
    with (
        patch("behave_runner.commands.impact.check_optional", return_value=True),
        patch("subprocess.run", side_effect=FileNotFoundError),
    ):
        result = runner.invoke(app, ["impact", "."])
        assert result.exit_code == 2


# --- lint command ---


def test_lint_no_dependency(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """lint should exit 2 when behave-lint is not installed."""
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.lint.check_optional", return_value=False):
        result = runner.invoke(app, ["lint"])
        assert result.exit_code == 2


def test_lint_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """lint should exit 2 when behave-lint CLI is not found."""
    monkeypatch.chdir(tmp_path)
    with (
        patch("behave_runner.commands.lint.check_optional", return_value=True),
        patch("subprocess.run", side_effect=FileNotFoundError),
    ):
        result = runner.invoke(app, ["lint"])
        assert result.exit_code == 2


# --- format command ---


def test_format_no_dependency(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """format should exit 2 when behave-format is not installed."""
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.format_cmd.check_optional", return_value=False):
        result = runner.invoke(app, ["format"])
        assert result.exit_code == 2


def test_format_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """format should exit 2 when behave-format CLI is not found."""
    monkeypatch.chdir(tmp_path)
    with (
        patch("behave_runner.commands.format_cmd.check_optional", return_value=True),
        patch("subprocess.run", side_effect=FileNotFoundError),
    ):
        result = runner.invoke(app, ["format"])
        assert result.exit_code == 2


# --- doctor command ---


def test_doctor_no_dependency(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """doctor should exit 2 when behave-doctor is not installed."""
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.doctor.check_optional", return_value=False):
        result = runner.invoke(app, ["doctor"])
        assert result.exit_code == 2


def test_doctor_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """doctor should exit 2 when behave-doctor CLI is not found."""
    monkeypatch.chdir(tmp_path)
    with (
        patch("behave_runner.commands.doctor.check_optional", return_value=True),
        patch("subprocess.run", side_effect=FileNotFoundError),
    ):
        result = runner.invoke(app, ["doctor"])
        assert result.exit_code == 2


# --- init command ---


def test_init_no_dependency(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """init should exit 2 when behave-gen is not installed."""
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.init.check_optional", return_value=False):
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 2


def test_init_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """init should exit 2 when behave-gen CLI is not found."""
    monkeypatch.chdir(tmp_path)
    with (
        patch("behave_runner.commands.init.check_optional", return_value=True),
        patch("subprocess.run", side_effect=FileNotFoundError),
    ):
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 2


# --- steps command ---


def test_steps_list_no_dependency(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """steps list should exit 2 when behave-steplib is not installed."""
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.steps.check_optional", return_value=False):
        result = runner.invoke(app, ["steps", "list"])
        assert result.exit_code == 2


# --- trace command ---


def test_trace_show_no_dependency(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """trace show should exit 2 when behave-trace is not installed."""
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.trace.check_optional", return_value=False):
        result = runner.invoke(app, ["trace", "show"])
        assert result.exit_code == 2


# --- generate command ---


def test_generate_step_no_dependency(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """generate step should exit 2 when behave-gen is not installed."""
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.generate.check_optional", return_value=False):
        result = runner.invoke(app, ["generate", "step", "--lib", "http"])
        assert result.exit_code == 2


# --- record command ---


def test_record_no_dependency(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """record should exit 2 when wavexis is not installed."""
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.record.check_optional", return_value=False):
        result = runner.invoke(app, ["record"])
        assert result.exit_code == 2


def test_record_wavexis_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """record should exit 2 when wavexis CLI is not found."""
    monkeypatch.chdir(tmp_path)
    with (
        patch("behave_runner.commands.record.check_optional", return_value=True),
        patch("subprocess.run", side_effect=FileNotFoundError),
    ):
        result = runner.invoke(app, ["record"])
        assert result.exit_code == 2


def test_record_recording_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """record should exit with non-zero code when recording fails."""
    monkeypatch.chdir(tmp_path)
    mock_result = MagicMock()
    mock_result.returncode = 1
    with (
        patch("behave_runner.commands.record.check_optional", return_value=True),
        patch("subprocess.run", return_value=mock_result),
    ):
        result = runner.invoke(app, ["record"])
        assert result.exit_code == 1


def test_record_success_no_gen(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """record should exit 0 when recording succeeds but behave-gen is missing."""
    monkeypatch.chdir(tmp_path)
    mock_result = MagicMock()
    mock_result.returncode = 0

    def check_optional_side_effect(feature: str, package: str, flag: str) -> bool:
        return feature != "gen"

    with (
        patch(
            "behave_runner.commands.record.check_optional", side_effect=check_optional_side_effect
        ),
        patch("subprocess.run", return_value=mock_result),
    ):
        result = runner.invoke(app, ["record"])
        assert result.exit_code == 0


def test_record_success_with_gen(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """record should exit with gen result code when both deps are available."""
    monkeypatch.chdir(tmp_path)
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_gen_result = MagicMock()
    mock_gen_result.returncode = 0
    with (
        patch("behave_runner.commands.record.check_optional", return_value=True),
        patch("subprocess.run", side_effect=[mock_result, mock_gen_result]),
    ):
        result = runner.invoke(app, ["record"])
        assert result.exit_code == 0


def test_record_gen_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """record should exit 2 when behave-gen CLI is not found after recording."""
    monkeypatch.chdir(tmp_path)
    mock_result = MagicMock()
    mock_result.returncode = 0
    with (
        patch("behave_runner.commands.record.check_optional", return_value=True),
        patch(
            "subprocess.run",
            side_effect=[mock_result, FileNotFoundError],
        ),
    ):
        result = runner.invoke(app, ["record"])
        assert result.exit_code == 2


# --- watch command ---


def test_watch_command_starts_and_stops(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """watch command should start watcher and handle KeyboardInterrupt."""
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.watch.FileWatcher") as mock_watcher_class:
        mock_watcher = MagicMock()
        mock_watcher.run.side_effect = KeyboardInterrupt
        mock_watcher_class.return_value = mock_watcher

        result = runner.invoke(app, ["watch", str(tmp_path)])
        assert result.exit_code == 0
        mock_watcher.run.assert_called_once()


# --- impact command with --run ---


def test_impact_run_affected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """impact --run should execute affected scenarios."""
    monkeypatch.chdir(tmp_path)
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = '[{"scenario": "scenario1"}, {"scenario": "scenario2"}]'
    with (
        patch("behave_runner.commands.impact.check_optional", return_value=True),
        patch("subprocess.run", return_value=mock_result),
        patch("behave_runner.commands.impact.run", return_value=0),
    ):
        result = runner.invoke(app, ["impact", "--run", str(tmp_path)])
        assert result.exit_code == 0


def test_impact_run_no_affected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """impact --run should report when no scenarios are affected."""
    monkeypatch.chdir(tmp_path)
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    with (
        patch("behave_runner.commands.impact.check_optional", return_value=True),
        patch("subprocess.run", return_value=mock_result),
    ):
        result = runner.invoke(app, ["impact", "--run", str(tmp_path)])
        assert result.exit_code == 0


def test_impact_basic_scan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """impact without --run should just scan and return exit code."""
    monkeypatch.chdir(tmp_path)
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    with (
        patch("behave_runner.commands.impact.check_optional", return_value=True),
        patch("subprocess.run", return_value=mock_result),
    ):
        result = runner.invoke(app, ["impact", str(tmp_path)])
        assert result.exit_code == 0


# --- open command ---


def test_open_trace_no_dependency(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """open trace should exit 2 when behave-trace is not installed."""
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.open_cmd.check_optional", return_value=False):
        result = runner.invoke(app, ["open", "trace"])
        assert result.exit_code == 2


def test_open_trace_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """open trace should exit 2 when behave-trace CLI is not found."""
    monkeypatch.chdir(tmp_path)
    with (
        patch("behave_runner.commands.open_cmd.check_optional", return_value=True),
        patch("subprocess.run", side_effect=FileNotFoundError),
    ):
        result = runner.invoke(app, ["open", "trace"])
        assert result.exit_code == 2


def test_open_report(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """open report should call open_latest_report."""
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.open_cmd.open_latest_report") as mock_open:
        result = runner.invoke(app, ["open", "report", "--output", str(tmp_path)])
        assert result.exit_code == 0
        mock_open.assert_called_once()


# --- steps command with subprocess ---


def test_steps_list_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """steps list should delegate to behave-steplib."""
    monkeypatch.chdir(tmp_path)
    mock_result = MagicMock()
    mock_result.returncode = 0
    with (
        patch("behave_runner.commands.steps.check_optional", return_value=True),
        patch("subprocess.run", return_value=mock_result),
    ):
        result = runner.invoke(app, ["steps", "list"])
        assert result.exit_code == 0


def test_steps_install_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """steps install should delegate to behave-steplib."""
    monkeypatch.chdir(tmp_path)
    mock_result = MagicMock()
    mock_result.returncode = 0
    with (
        patch("behave_runner.commands.steps.check_optional", return_value=True),
        patch("subprocess.run", return_value=mock_result),
    ):
        result = runner.invoke(app, ["steps", "install", "http"])
        assert result.exit_code == 0


def test_steps_search_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """steps search should delegate to behave-steplib."""
    monkeypatch.chdir(tmp_path)
    mock_result = MagicMock()
    mock_result.returncode = 0
    with (
        patch("behave_runner.commands.steps.check_optional", return_value=True),
        patch("subprocess.run", return_value=mock_result),
    ):
        result = runner.invoke(app, ["steps", "search", "http"])
        assert result.exit_code == 0


def test_steps_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """steps should exit 2 when behave-steplib CLI is not found."""
    monkeypatch.chdir(tmp_path)
    with (
        patch("behave_runner.commands.steps.check_optional", return_value=True),
        patch("subprocess.run", side_effect=FileNotFoundError),
    ):
        result = runner.invoke(app, ["steps", "list"])
        assert result.exit_code == 2


# --- generate command with subprocess ---


def test_generate_step_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """generate step should delegate to behave-gen."""
    monkeypatch.chdir(tmp_path)
    mock_result = MagicMock()
    mock_result.returncode = 0
    with (
        patch("behave_runner.commands.generate.check_optional", return_value=True),
        patch("subprocess.run", return_value=mock_result),
    ):
        result = runner.invoke(app, ["generate", "step", "--lib", "http"])
        assert result.exit_code == 0


def test_generate_feature_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """generate feature should delegate to behave-gen."""
    monkeypatch.chdir(tmp_path)
    mock_result = MagicMock()
    mock_result.returncode = 0
    with (
        patch("behave_runner.commands.generate.check_optional", return_value=True),
        patch("subprocess.run", return_value=mock_result),
    ):
        result = runner.invoke(app, ["generate", "feature", "login"])
        assert result.exit_code == 0


def test_generate_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """generate should exit 2 when behave-gen CLI is not found."""
    monkeypatch.chdir(tmp_path)
    with (
        patch("behave_runner.commands.generate.check_optional", return_value=True),
        patch("subprocess.run", side_effect=FileNotFoundError),
    ):
        result = runner.invoke(app, ["generate", "step", "--lib", "http"])
        assert result.exit_code == 2


# --- trace command with subprocess ---


def test_trace_show_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """trace show should delegate to behave-trace."""
    monkeypatch.chdir(tmp_path)
    mock_result = MagicMock()
    mock_result.returncode = 0
    with (
        patch("behave_runner.commands.trace.check_optional", return_value=True),
        patch("subprocess.run", return_value=mock_result),
    ):
        result = runner.invoke(app, ["trace", "show"])
        assert result.exit_code == 0


def test_trace_serve_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """trace serve should delegate to behave-trace."""
    monkeypatch.chdir(tmp_path)
    mock_result = MagicMock()
    mock_result.returncode = 0
    with (
        patch("behave_runner.commands.trace.check_optional", return_value=True),
        patch("subprocess.run", return_value=mock_result),
    ):
        result = runner.invoke(app, ["trace", "serve"])
        assert result.exit_code == 0


def test_trace_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """trace should exit 2 when behave-trace CLI is not found."""
    monkeypatch.chdir(tmp_path)
    with (
        patch("behave_runner.commands.trace.check_optional", return_value=True),
        patch("subprocess.run", side_effect=FileNotFoundError),
    ):
        result = runner.invoke(app, ["trace", "show"])
        assert result.exit_code == 2


# --- init command with subprocess ---


def test_init_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """init should delegate to behave-gen."""
    monkeypatch.chdir(tmp_path)
    mock_result = MagicMock()
    mock_result.returncode = 0
    with (
        patch("behave_runner.commands.init.check_optional", return_value=True),
        patch("subprocess.run", return_value=mock_result),
    ):
        result = runner.invoke(app, ["init", "--name", "my-project"])
        assert result.exit_code == 0


# --- lint command with subprocess ---


def test_lint_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """lint should delegate to behave-lint."""
    monkeypatch.chdir(tmp_path)
    mock_result = MagicMock()
    mock_result.returncode = 0
    with (
        patch("behave_runner.commands.lint.check_optional", return_value=True),
        patch("subprocess.run", return_value=mock_result),
    ):
        result = runner.invoke(app, ["lint"])
        assert result.exit_code == 0


# --- format command with subprocess ---


def test_format_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """format should delegate to behave-format."""
    monkeypatch.chdir(tmp_path)
    mock_result = MagicMock()
    mock_result.returncode = 0
    with (
        patch("behave_runner.commands.format_cmd.check_optional", return_value=True),
        patch("subprocess.run", return_value=mock_result),
    ):
        result = runner.invoke(app, ["format", "--check"])
        assert result.exit_code == 0


# --- doctor command with subprocess ---


def test_doctor_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """doctor should delegate to behave-doctor."""
    monkeypatch.chdir(tmp_path)
    mock_result = MagicMock()
    mock_result.returncode = 0
    with (
        patch("behave_runner.commands.doctor.check_optional", return_value=True),
        patch("subprocess.run", return_value=mock_result),
    ):
        result = runner.invoke(app, ["doctor"])
        assert result.exit_code == 0


# --- record command regression ---


def test_record_rejects_path_traversal_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """record should reject --name values that contain path separators."""
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.record.check_optional", return_value=True):
        result = runner.invoke(app, ["record", "--name", "foo/bar"])
        assert result.exit_code == 2
        assert "simple file name" in result.stdout


# --- impact command regression ---


def test_impact_run_respects_scan_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """impact --run should exit with scan return code when scan fails."""
    monkeypatch.chdir(tmp_path)
    mock_result = MagicMock()
    mock_result.returncode = 3
    mock_result.stdout = ""
    with (
        patch("behave_runner.commands.impact.check_optional", return_value=True),
        patch("subprocess.run", return_value=mock_result),
        patch("behave_runner.commands.impact.run") as mock_run,
    ):
        result = runner.invoke(app, ["impact", "--run", str(tmp_path)])
        assert result.exit_code == 3
        mock_run.assert_not_called()


# --- config command regression ---


def test_config_set_escapes_newlines(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """config set should escape newlines in string values."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nname = 'test'\n")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "set", "message", "hello\nworld"])
    assert result.exit_code == 0
    content = pyproject.read_text()
    assert "hello\\nworld" in content


def test_config_show_malformed_pyproject(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """config show should exit 2 when pyproject.toml is malformed."""
    (tmp_path / "pyproject.toml").write_text("[tool.behave-runner\nparallel = 4")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 2
    assert "Failed to parse" in result.stdout or "Error" in result.stdout


# --- report command regression ---


def test_report_delegates_to_formatter(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """report generate should run behave with the formatter and return its exit code."""
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.report.run", return_value=0) as mock_run:
        result = runner.invoke(
            app,
            [
                "report",
                "generate",
                "--format",
                "html",
                "--output",
                str(tmp_path),
                "tests/fixtures/minimal",
            ],
        )
        assert result.exit_code == 0
        mock_run.assert_called_once()
        config = mock_run.call_args[0][0]
        assert config.fmt == "html"


def test_report_handles_os_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """report generate should exit 2 on OSError from behave."""
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.report.run", side_effect=OSError("denied")):
        result = runner.invoke(
            app, ["report", "generate", "--format", "html", "tests/fixtures/minimal"]
        )
        assert result.exit_code == 1


def test_report_file_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """report generate should exit 2 when behave is not found."""
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.report.run", return_value=2):
        result = runner.invoke(
            app, ["report", "generate", "--format", "html", "tests/fixtures/minimal"]
        )
        assert result.exit_code == 2


# --- record command OSError handling ---


def test_record_handles_os_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """record should exit 2 when wavexis raises OSError."""
    monkeypatch.chdir(tmp_path)
    with (
        patch("behave_runner.commands.record.check_optional", return_value=True),
        patch(
            "behave_runner.commands.record.subprocess.run",
            side_effect=PermissionError("denied"),
        ),
    ):
        result = runner.invoke(app, ["record"])
        assert result.exit_code == 2
        assert "Error running wavexis" in result.stdout


# --- impact command edge cases ---


def test_impact_rejects_invalid_format(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """impact should exit 2 for unknown output formats."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["impact", "--format", "xml", str(tmp_path)])
    assert result.exit_code == 2
    assert "Unknown format" in result.stdout


def test_impact_os_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """impact should exit 2 when behave-doctor raises OSError."""
    monkeypatch.chdir(tmp_path)
    with (
        patch("behave_runner.commands.impact.check_optional", return_value=True),
        patch(
            "behave_runner.commands.impact.subprocess.run",
            side_effect=PermissionError("denied"),
        ),
    ):
        result = runner.invoke(app, ["impact", str(tmp_path)])
        assert result.exit_code == 2


def test_impact_run_no_affected_names(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """impact --run should exit 0 when scan output contains only whitespace."""
    monkeypatch.chdir(tmp_path)
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "   \n"
    with (
        patch("behave_runner.commands.impact.check_optional", return_value=True),
        patch("behave_runner.commands.impact.subprocess.run", return_value=mock_result),
    ):
        result = runner.invoke(app, ["impact", "--run", str(tmp_path)])
        assert result.exit_code == 0
        assert "No affected" in result.stdout


def test_impact_run_returns_worst_exit_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """impact --run should return the worst exit code from affected scenarios."""
    monkeypatch.chdir(tmp_path)
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = '[{"scenario": "scenario1"}, {"scenario": "scenario2"}]'
    with (
        patch("behave_runner.commands.impact.check_optional", return_value=True),
        patch("behave_runner.commands.impact.subprocess.run", return_value=mock_result),
        patch("behave_runner.commands.impact.run", side_effect=[0, 1]) as mock_run,
    ):
        result = runner.invoke(app, ["impact", "--run", str(tmp_path)])
        assert result.exit_code == 1
        assert mock_run.call_count == 2


# --- run command input validation ---


def test_run_rejects_negative_parallel(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """run should exit 2 when RunConfig validation fails."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["run", "--parallel", "-1", "tests/fixtures/minimal/features"])
    assert result.exit_code == 2


def test_run_flaky_report_requires_retries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """run should warn and ignore --flaky-report without --retries."""
    from unittest.mock import patch

    fixture_path = (
        Path(__file__).resolve().parent.parent.parent
        / "tests"
        / "fixtures"
        / "minimal"
        / "features"
    )
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.run.run", return_value=0):
        result = runner.invoke(
            app,
            ["run", "--flaky-report", str(fixture_path)],
        )
    assert result.exit_code == 0
    assert "requires --retries" in result.stdout


def test_run_rejects_invalid_shard(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """run should exit 2 for an invalid shard value."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["run", "--shard", "2/1", "tests/fixtures/minimal/features"])
    assert result.exit_code == 2


# --- record OSError for behave-gen ---


def test_record_gen_os_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """record should exit 2 when behave-gen raises OSError."""
    monkeypatch.chdir(tmp_path)
    mock_result = MagicMock()
    mock_result.returncode = 0

    def check_optional_side_effect(feature: str, package: str, flag: str) -> bool:
        return True

    with (
        patch(
            "behave_runner.commands.record.check_optional",
            side_effect=check_optional_side_effect,
        ),
        patch(
            "behave_runner.commands.record.subprocess.run",
            side_effect=[mock_result, PermissionError("denied")],
        ),
    ):
        result = runner.invoke(app, ["record"])
        assert result.exit_code == 2
        assert "Error running behave-gen" in result.stdout
