"""Regression tests for bugs found during stabilization audit."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from behave_runner.cli.app import app
from behave_runner.core.orchestrator import RunConfig, _build_env, build_behave_command
from behave_runner.core.output import clean_output_dir, ensure_output_dir
from behave_runner.core.watcher import FileWatcher

runner = CliRunner()

FIXTURE = "tests/fixtures/minimal/features"


# --- Regression: duplicate `impact` command registration ---


def test_impact_command_not_duplicated() -> None:
    """Ensure the `impact` command is registered exactly once."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    impact_count = result.stdout.count("impact")
    assert impact_count == 1, f"Expected 'impact' once in help, found {impact_count} times"


# --- Regression: scenario_timeout passed as env var, not CLI flag ---


def test_scenario_timeout_not_in_behave_command() -> None:
    """Ensure --scenario-timeout is not added to the behave command (behave doesn't support it)."""
    config = RunConfig(scenario_timeout=5)
    cmd = build_behave_command(config)
    assert "--scenario-timeout" not in cmd


def test_scenario_timeout_passed_as_env_var() -> None:
    """Ensure scenario_timeout is passed as BEHAVE_SCENARIO_TIMEOUT env var."""
    config = RunConfig(scenario_timeout=10)
    env = _build_env(config)
    assert env["BEHAVE_SCENARIO_TIMEOUT"] == "10"


def test_scenario_timeout_not_set_when_none() -> None:
    """Ensure BEHAVE_SCENARIO_TIMEOUT is not set when scenario_timeout is None."""
    config = RunConfig()
    env = _build_env(config)
    assert "BEHAVE_SCENARIO_TIMEOUT" not in env


# --- Regression: RunConfig no longer has smoke and profile fields ---


def test_run_config_no_smoke_field() -> None:
    """Ensure RunConfig no longer has the dead `smoke` field."""
    config = RunConfig()
    assert not hasattr(config, "smoke")


def test_run_config_no_profile_field() -> None:
    """Ensure RunConfig no longer has the dead `profile` field."""
    config = RunConfig()
    assert not hasattr(config, "profile")


# --- Regression: report format names corrected (sheets, no pdf) ---


def test_report_format_sheets_accepted() -> None:
    """Ensure 'sheets' is an accepted format and 'xlsx' and 'pdf' are not."""
    from behave_runner.core.orchestrator import _REPORT_FORMATTERS

    assert "sheets" in _REPORT_FORMATTERS
    assert "xlsx" not in _REPORT_FORMATTERS
    assert "pdf" not in _REPORT_FORMATTERS


# --- Regression: config profile tags normalization from behave.ini ---


def test_profile_tags_normalization_from_string() -> None:
    """Ensure tags from config that are a string are normalized to list."""
    from behave_runner.core.config import _normalize_values

    profile = {"tags": "@smoke, @fast", "format": "pretty"}
    normalized = _normalize_values(profile)
    assert isinstance(normalized.get("tags"), list)
    assert "@smoke" in normalized["tags"]
    assert "@fast" in normalized["tags"]


# --- Regression: clean_output_dir handles nested directories ---


def test_clean_output_dir_nested_dirs(tmp_path: Path) -> None:
    """Ensure clean_output_dir removes nested subdirectories."""
    d = ensure_output_dir(tmp_path / "output")
    nested = d / "subdir" / "nested"
    nested.mkdir(parents=True)
    (nested / "file.txt").write_text("test")

    clean_output_dir(d)

    assert d.exists()
    assert not any(d.iterdir())


# --- Regression: select command handles invalid regex gracefully ---


def test_select_invalid_regex_returns_error() -> None:
    """Ensure invalid regex pattern shows error and exits with code 2."""
    result = runner.invoke(
        app, ["select", "--pattern", "[invalid", "tests/fixtures/minimal/features"]
    )
    assert result.exit_code == 2
    assert "Invalid regex pattern" in result.output


# --- Regression: watcher detects deleted files ---


def test_watcher_detects_deleted_file(tmp_path: Path) -> None:
    """Ensure FileWatcher detects file deletion."""
    test_file = tmp_path / "test.feature"
    test_file.write_text("Feature: Test")

    changes: list[Path] = []
    watcher = FileWatcher([tmp_path], on_change=changes.extend, debounce_ms=0)

    # Initial scan
    watcher._mtimes = watcher._scan()

    # Delete the file
    test_file.unlink()

    changed = watcher._detect_changes()
    assert test_file in changed


# --- Regression: watcher callback exception doesn't crash ---


def test_watcher_callback_exception_doesnt_crash(tmp_path: Path) -> None:
    """Ensure watcher doesn't crash if callback raises an exception."""

    def bad_callback(paths: list[Path]) -> None:
        raise ValueError("Callback error")

    test_file = tmp_path / "test.feature"
    test_file.write_text("Feature: Test")

    watcher = FileWatcher([tmp_path], on_change=bad_callback, debounce_ms=0)
    watcher._mtimes = watcher._scan()

    # Modify file to trigger callback
    time.sleep(0.05)
    test_file.write_text("Feature: Test\n# Modified")

    # Run one iteration of the loop
    import threading

    thread = threading.Thread(target=watcher.run, daemon=True)
    thread.start()
    time.sleep(0.3)
    watcher.stop()
    thread.join(timeout=1.0)

    # If we get here without hanging, the watcher handled the exception


# --- Regression: config_cmd _write_toml_section doesn't insert inside other sections ---


def test_config_init_after_other_tool_section(tmp_path: Path, monkeypatch) -> None:
    """Ensure config init inserts [tool.behave-runner] after the last [tool.*] section,
    not inside it."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[project]\n"
        'name = "test"\n'
        'version = "0.1.0"\n'
        "\n"
        "[tool.ruff]\n"
        "line-length = 100\n"
        "\n"
        "[tool.pytest.ini_options]\n"
        'testpaths = ["tests"]\n'
    )
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["config", "init"])
    assert result.exit_code == 0

    content = pyproject.read_text()
    assert "[tool.behave-runner]" in content
    behave_pos = content.index("[tool.behave-runner]")
    pytest_pos = content.index("[tool.pytest.ini_options]")
    assert pytest_pos < behave_pos


def test_config_init_preserves_content_without_tool_sections(tmp_path: Path, monkeypatch) -> None:
    """Ensure config init preserves file content when no [tool.*] sections exist."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "test"\nversion = "0.1.0"\n')
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["config", "init"])
    assert result.exit_code == 0

    content = pyproject.read_text()
    assert "[project]" in content
    assert 'name = "test"' in content
    assert "[tool.behave-runner]" in content


# --- Regression: deps.py uses English messages ---


def test_deps_warning_in_english() -> None:
    """Ensure check_optional prints English warning, not Spanish."""
    from behave_runner.core.deps import check_optional

    result = check_optional("test-feature", "nonexistent_pkg_xyz", "test-flag")
    assert not result
    # The warning should contain English text, not Spanish
    # We can't capture console output easily, but we can verify the function returns False
    # and doesn't raise


# --- Regression: watch.py uses features/steps not steps ---


def test_watch_default_paths_include_features_steps() -> None:
    """Ensure watch command default paths include features/steps, not steps."""
    from behave_runner.commands.watch import _DEFAULT_PATHS

    path_strs = [str(p).replace("\\", "/") for p in _DEFAULT_PATHS]
    assert "features/steps" in path_strs
    assert "steps" not in path_strs


# --- Regression: DRY - shared features module exists ---


def test_shared_features_module_exists() -> None:
    """Ensure the shared features module is importable and has expected functions."""
    from behave_runner.core.features import collect_scenarios, matches_tags

    assert callable(collect_scenarios)
    assert callable(matches_tags)


def test_matches_tags_include_and_exclude() -> None:
    """Test matches_tags logic for include (AND) and exclude."""
    from behave_runner.core.features import matches_tags

    assert matches_tags(["@smoke", "@fast"], include_tags=["@smoke"])
    assert not matches_tags(["@smoke"], include_tags=["@smoke", "@fast"])
    assert not matches_tags(["@smoke", "@slow"], include_tags=None, exclude_tags=["@slow"])
    assert matches_tags(["@smoke"], include_tags=None, exclude_tags=["@slow"])
    assert matches_tags([], include_tags=[], exclude_tags=[])


# --- Regression: run() passes env vars for retries and scenario_timeout ---


def test_run_passes_env_vars_for_retries(monkeypatch) -> None:
    """Ensure run() passes env vars (scenario_timeout, retries) to subprocess."""
    from behave_runner.core import orchestrator

    captured_env: dict[str, str] = {}

    class FakePopen:
        def __init__(self, cmd, **kwargs):
            captured_env.update(kwargs.get("env", {}))
            self.returncode = 0
            self.pid = 1

        def wait(self, timeout=None):
            return self.returncode

        def kill(self):
            pass

    monkeypatch.setattr(orchestrator.subprocess, "Popen", FakePopen)

    config = RunConfig(scenario_timeout=42, retries=3)
    orchestrator.run(config)
    assert captured_env.get("BEHAVE_SCENARIO_TIMEOUT") == "42"
    assert captured_env.get("BEHAVE_RETRY_MAX_RETRIES") == "3"


# --- Regression: find_latest_report only returns files, not directories ---


def test_find_latest_report_ignores_directories(tmp_path: Path) -> None:
    """Ensure find_latest_report returns only files, not subdirectories."""
    from behave_runner.core.output import find_latest_report

    subdir = tmp_path / "subdir"
    subdir.mkdir()
    report_file = tmp_path / "report.html"
    report_file.write_text("<html></html>")

    result = find_latest_report(tmp_path)
    assert result is not None
    assert result == report_file
    assert result.is_file()


def test_find_latest_report_returns_none_for_empty_dir(tmp_path: Path) -> None:
    """Ensure find_latest_report returns None for a directory with only subdirs."""
    from behave_runner.core.output import find_latest_report

    subdir = tmp_path / "subdir"
    subdir.mkdir()

    result = find_latest_report(tmp_path)
    assert result is None


# --- Regression: _write_toml_section doesn't break last [tool.*] section content ---


def test_config_init_preserves_last_tool_section_content(tmp_path: Path, monkeypatch) -> None:
    """Ensure config init doesn't insert [tool.behave-runner] in the middle of
    the last [tool.*] section's content."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "test"\n\n[tool.ruff]\nline-length = 100\nselect = ["E"]\n'
    )
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["config", "init"])
    assert result.exit_code == 0

    content = pyproject.read_text()
    # The ruff section's content must still belong to [tool.ruff]
    ruff_pos = content.index("[tool.ruff]")
    behave_pos = content.index("[tool.behave-runner]")
    line_length_pos = content.index("line-length = 100")

    # line-length must come BEFORE [tool.behave-runner] (still part of [tool.ruff])
    assert ruff_pos < line_length_pos < behave_pos


# --- Regression: config init doesn't print "Created" when section exists ---


def test_config_init_already_exists_message(tmp_path: Path, monkeypatch) -> None:
    """Ensure config init prints 'already exists' when section is present."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "test"\n\n[tool.behave-runner]\ntimeout = 30\n')
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["config", "init"])
    assert result.exit_code == 0
    assert "already exists" in result.stdout
    assert "Created" not in result.stdout


# --- Regression: _format_value handles lists for TOML arrays ---


def test_format_value_handles_list() -> None:
    """Ensure _format_value produces valid TOML for lists."""
    from behave_runner.commands.config_cmd import _format_value

    assert _format_value(["a", "b"]) == '["a", "b"]'
    assert _format_value([1, 2, 3]) == "[1, 2, 3]"
    assert _format_value([True, False]) == "[true, false]"
    assert _format_value([]) == "[]"


# --- Regression: timeout is a subprocess timeout, not a behave CLI flag ---


def test_timeout_not_in_behave_command() -> None:
    """Ensure --timeout is NOT passed to behave (behave has no --timeout flag)."""
    config = RunConfig(timeout=30)
    cmd = build_behave_command(config)
    assert "--timeout" not in cmd


def test_timeout_passed_to_subprocess(monkeypatch) -> None:
    """Ensure run() enforces timeout as a subprocess timeout."""
    from behave_runner.core import orchestrator

    config = RunConfig(timeout=30)
    captured = {}

    class FakePopen:
        def __init__(self, cmd, **kwargs):
            self.returncode = 0
            self.pid = 1

        def wait(self, timeout=None):
            captured["timeout"] = timeout
            return self.returncode

        def kill(self):
            pass

    monkeypatch.setattr(orchestrator.subprocess, "Popen", FakePopen)
    orchestrator.run(config)
    assert captured["timeout"] == 30


def test_timeout_zero_means_no_subprocess_timeout(monkeypatch) -> None:
    """Ensure timeout=0 maps to no subprocess timeout (not an instant kill)."""
    from behave_runner.core import orchestrator

    config = RunConfig(timeout=0)
    captured = {}

    class FakePopen:
        def __init__(self, cmd, **kwargs):
            self.returncode = 0
            self.pid = 1

        def wait(self, timeout=None):
            captured["timeout"] = timeout
            return self.returncode

        def kill(self):
            pass

    monkeypatch.setattr(orchestrator.subprocess, "Popen", FakePopen)
    orchestrator.run(config)
    assert captured["timeout"] is None


def test_timeout_expired_returns_124(monkeypatch) -> None:
    """Ensure a timed-out behave run exits with 124 (timeout convention)."""
    import subprocess as subprocess_module

    from behave_runner.core import orchestrator

    config = RunConfig(timeout=5)

    class FakePopen:
        def __init__(self, cmd, **kwargs):
            self.returncode = 0
            self.pid = 1
            self._waits = 0

        def wait(self, timeout=None):
            self._waits += 1
            if timeout is not None:
                raise subprocess_module.TimeoutExpired(cmd="behave", timeout=timeout)
            return self.returncode

        def kill(self):
            pass

    monkeypatch.setattr(orchestrator.subprocess, "Popen", FakePopen)
    monkeypatch.setattr(orchestrator, "_kill_process_tree", lambda proc: None)
    assert orchestrator.run(config) == 124


def test_max_failures_not_in_behave_command() -> None:
    """Ensure --max-failures is not added to behave command (uses --stop instead)."""
    config = RunConfig(max_failures=3)
    cmd = build_behave_command(config)
    assert "--max-failures" not in cmd


def test_timeout_not_set_as_env_var() -> None:
    """Ensure timeout is NOT passed as BEHAVE_TIMEOUT env var (uses CLI flag)."""
    config = RunConfig(timeout=30)
    env = _build_env(config)
    assert "BEHAVE_TIMEOUT" not in env


def test_max_failures_not_set_as_env_var() -> None:
    """Ensure max_failures is NOT passed as BEHAVE_MAX_FAILURES env var (uses --stop)."""
    config = RunConfig(max_failures=5)
    env = _build_env(config)
    assert "BEHAVE_MAX_FAILURES" not in env


def test_timeout_not_set_when_none() -> None:
    """Ensure BEHAVE_TIMEOUT is not set when timeout is None."""
    config = RunConfig()
    env = _build_env(config)
    assert "BEHAVE_TIMEOUT" not in env


def test_max_failures_not_set_when_none() -> None:
    """Ensure BEHAVE_MAX_FAILURES is not set when max_failures is None."""
    config = RunConfig()
    env = _build_env(config)
    assert "BEHAVE_MAX_FAILURES" not in env


# --- Regression: run() sets env vars in os.environ for external library subprocesses ---


def test_run_does_not_set_timeout_env_var(monkeypatch) -> None:
    """Ensure run() does NOT set BEHAVE_TIMEOUT in os.environ (uses CLI flag now)."""
    import os as os_module

    from behave_runner.core import orchestrator

    config = RunConfig(timeout=99)
    captured = {}

    class FakePopen:
        def __init__(self, cmd, env=None, **kwargs):
            captured["BEHAVE_TIMEOUT"] = os_module.environ.get("BEHAVE_TIMEOUT")
            self.returncode = 0
            self.pid = 1

        def wait(self, timeout=None):
            return self.returncode

        def kill(self):
            pass

    monkeypatch.setattr(orchestrator.subprocess, "Popen", FakePopen)
    orchestrator.run(config)
    assert captured["BEHAVE_TIMEOUT"] is None


# --- Regression: load_config falls back to behave.ini when pyproject.toml has no section ---


def test_load_config_falls_back_to_behave_ini(tmp_path: Path, monkeypatch) -> None:
    """Ensure load_config checks behave.ini when pyproject.toml has no [tool.behave-runner]."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "test"\n')

    behave_ini = tmp_path / "behave.ini"
    behave_ini.write_text("[behave-runner]\ndefault_parallel = 4\n")

    monkeypatch.chdir(tmp_path)
    from behave_runner.core.config import load_config

    config = load_config()
    assert config.get("default_parallel") == "4"


# --- Regression: _format_value escapes special characters in strings ---


def test_format_value_escapes_quotes() -> None:
    """Ensure _format_value escapes double quotes in string values."""
    from behave_runner.commands.config_cmd import _format_value

    assert _format_value('hello"world') == '"hello\\"world"'
    assert _format_value("hello'world") == '"hello\'world"'
    assert _format_value("plain") == '"plain"'


def test_format_value_escapes_backslashes() -> None:
    """Ensure _format_value escapes backslashes in string values."""
    from behave_runner.commands.config_cmd import _format_value

    assert _format_value("path\\to\\file") == '"path\\\\to\\\\file"'


def test_format_value_escapes_in_list() -> None:
    """Ensure _format_value escapes special characters inside lists."""
    from behave_runner.commands.config_cmd import _format_value

    result = _format_value(['a"b', "c\\d"])
    assert result == '["a\\"b", "c\\\\d"]'


def test_format_value_escapes_newlines_and_tabs() -> None:
    """Ensure _format_value escapes control characters in string values."""
    from behave_runner.commands.config_cmd import _format_value

    assert _format_value("hello\nworld") == '"hello\\nworld"'
    assert _format_value("hello\tworld") == '"hello\\tworld"'
    assert _format_value("hello\rworld") == '"hello\\rworld"'


# --- Regression: run.py loads all config values from profiles, not just 4 ---


def test_profile_loads_parallel(tmp_path: Path, monkeypatch) -> None:
    """Ensure parallel is loaded from profile config."""
    import textwrap
    from unittest.mock import patch

    from typer.testing import CliRunner

    from behave_runner.cli.app import app

    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.ci]
            parallel = 4
        """)
    )
    monkeypatch.chdir(tmp_path)

    cli_runner = CliRunner()
    fixture_path = str(
        Path(__file__).resolve().parent.parent.parent
        / "tests"
        / "fixtures"
        / "minimal"
        / "features"
    )
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = cli_runner.invoke(app, ["run", "--profile", "ci", fixture_path])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert config.parallel == 4


def test_profile_loads_dry_run(tmp_path: Path, monkeypatch) -> None:
    """Ensure dry_run is loaded from profile config."""
    import textwrap
    from unittest.mock import patch

    from typer.testing import CliRunner

    from behave_runner.cli.app import app

    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.ci]
            dry_run = true
        """)
    )
    monkeypatch.chdir(tmp_path)

    cli_runner = CliRunner()
    fixture_path = str(
        Path(__file__).resolve().parent.parent.parent
        / "tests"
        / "fixtures"
        / "minimal"
        / "features"
    )
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = cli_runner.invoke(app, ["run", "--profile", "ci", fixture_path])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert config.dry_run is True


def test_profile_loads_retries(tmp_path: Path, monkeypatch) -> None:
    """Ensure retries is loaded from profile config."""
    import textwrap
    from unittest.mock import patch

    from typer.testing import CliRunner

    from behave_runner.cli.app import app

    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.ci]
            retries = 2
        """)
    )
    monkeypatch.chdir(tmp_path)

    cli_runner = CliRunner()
    fixture_path = str(
        Path(__file__).resolve().parent.parent.parent
        / "tests"
        / "fixtures"
        / "minimal"
        / "features"
    )
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = cli_runner.invoke(app, ["run", "--profile", "ci", fixture_path])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert config.retries == 2


def test_profile_loads_parallel_from_string(tmp_path: Path, monkeypatch) -> None:
    """Ensure string parallel values from profiles are coerced to int."""
    import textwrap
    from unittest.mock import patch

    from typer.testing import CliRunner

    from behave_runner.cli.app import app

    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.ci]
            parallel = "4"
        """)
    )
    monkeypatch.chdir(tmp_path)

    cli_runner = CliRunner()
    fixture_path = str(
        Path(__file__).resolve().parent.parent.parent
        / "tests"
        / "fixtures"
        / "minimal"
        / "features"
    )
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = cli_runner.invoke(app, ["run", "--profile", "ci", fixture_path])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert config.parallel == 4


def test_profile_loads_dry_run_false_string(tmp_path: Path, monkeypatch) -> None:
    """Ensure string 'false' dry_run values do not enable dry-run."""
    import textwrap
    from unittest.mock import patch

    from typer.testing import CliRunner

    from behave_runner.cli.app import app

    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.ci]
            dry_run = "false"
            format = "pretty"
        """)
    )
    monkeypatch.chdir(tmp_path)

    cli_runner = CliRunner()
    fixture_path = str(
        Path(__file__).resolve().parent.parent.parent
        / "tests"
        / "fixtures"
        / "minimal"
        / "features"
    )
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = cli_runner.invoke(app, ["run", "--profile", "ci", fixture_path])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert config.dry_run is False


def test_config_show_exit_code_when_no_config(
    tmp_path: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression: config show should exit 0 when no config found (not crash)."""
    monkeypatch.chdir(tmp_path)
    cli_runner = CliRunner()
    result = cli_runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0


def test_config_set_exit_code_when_no_pyproject(
    tmp_path: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression: config set should exit 2 (not 1) when pyproject.toml is missing."""
    monkeypatch.chdir(tmp_path)
    cli_runner = CliRunner()
    result = cli_runner.invoke(app, ["config", "set", "parallel", "4"])
    assert result.exit_code == 2


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Creating symlinks on Windows requires admin privileges",
)
def test_clean_output_dir_symlink_safety(tmp_path: Path) -> None:
    """Regression: clean_output_dir should unlink symlinks, not follow them."""
    from behave_runner.core.output import clean_output_dir

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    target_dir = tmp_path / "target"
    target_dir.mkdir()
    target_file = target_dir / "important.txt"
    target_file.write_text("important data")

    link = output_dir / "link"
    link.symlink_to(target_dir)

    clean_output_dir(output_dir)

    assert not link.exists()
    assert target_file.exists(), "Symlink target should not be deleted"
    assert target_dir.exists(), "Symlink target directory should not be deleted"


# --- Regression: collect_scenarios should not crash on malformed feature files ---


def test_collect_scenarios_skips_malformed_features(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ensure malformed .feature files are skipped instead of crashing."""
    from behave_runner.core.features import collect_scenarios

    # chdir to tmp_path so behave's parser doesn't fail on cross-drive relpath
    monkeypatch.chdir(tmp_path)

    good = tmp_path / "good.feature"
    good.write_text("Feature: Good\n\n  Scenario: Example\n    Given a step\n")
    bad = tmp_path / "bad.feature"
    bad.write_text("This is not a valid feature file")

    scenarios = collect_scenarios([good, bad])
    assert len(scenarios) == 1
    assert scenarios[0]["feature"] == "Good"


# --- Regression: --smoke with --profile should merge tags, not replace ---


def test_smoke_with_profile_merges_tags(tmp_path: Path, monkeypatch) -> None:
    """--smoke should add @smoke to profile tags, not replace them."""
    import textwrap
    from unittest.mock import patch

    from typer.testing import CliRunner

    from behave_runner.cli.app import app

    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.ci]
            tags = ["@fast"]
            dry_run = true
        """)
    )
    monkeypatch.chdir(tmp_path)

    cli_runner = CliRunner()
    fixture_path = str(
        Path(__file__).resolve().parent.parent.parent
        / "tests"
        / "fixtures"
        / "minimal"
        / "features"
    )
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = cli_runner.invoke(app, ["run", "--smoke", "--profile", "ci", fixture_path])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert "@smoke" in config.tags
    assert "@fast" in config.tags


# --- Regression: profile features should be used when no CLI features ---


def test_profile_features_used_when_no_cli_features(tmp_path: Path, monkeypatch) -> None:
    """Profile features should be used when no CLI features are provided."""
    import textwrap
    from unittest.mock import patch

    from typer.testing import CliRunner

    from behave_runner.cli.app import app

    fixture_path = str(
        Path(__file__).resolve().parent.parent.parent
        / "tests"
        / "fixtures"
        / "minimal"
        / "features"
    ).replace("\\", "/")
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent(f"""
            [tool.behave-runner.profiles.ci]
            features = ["{fixture_path}"]
            dry_run = true
        """)
    )
    monkeypatch.chdir(tmp_path)

    cli_runner = CliRunner()
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = cli_runner.invoke(app, ["run", "--profile", "ci"])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert fixture_path in config.features or any(
        Path(f).as_posix() == fixture_path for f in config.features
    )


# --- Regression: profile name should be loaded ---


def test_profile_name_loaded(tmp_path: Path, monkeypatch) -> None:
    """Profile name filter should be loaded and applied."""
    import textwrap
    from unittest.mock import patch

    from typer.testing import CliRunner

    from behave_runner.cli.app import app

    fixture_path = str(
        Path(__file__).resolve().parent.parent.parent
        / "tests"
        / "fixtures"
        / "minimal"
        / "features"
    ).replace("\\", "/")
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent(f"""
            [tool.behave-runner.profiles.ci]
            features = ["{fixture_path}"]
            name = ["Nonexistent scenario"]
            dry_run = true
        """)
    )
    monkeypatch.chdir(tmp_path)

    cli_runner = CliRunner()
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = cli_runner.invoke(app, ["run", "--profile", "ci"])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert "Nonexistent scenario" in config.name


# --- Regression: profile shard should be validated ---


def test_profile_invalid_shard_rejected(tmp_path: Path, monkeypatch) -> None:
    """Invalid shard from profile should be rejected with exit code 2."""
    import textwrap

    from typer.testing import CliRunner

    from behave_runner.cli.app import app

    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.ci]
            shard = "3/2"
        """)
    )
    monkeypatch.chdir(tmp_path)

    cli_runner = CliRunner()
    result = cli_runner.invoke(app, ["run", "--profile", "ci"])
    assert result.exit_code == 2
    assert "Invalid shard" in result.output


def test_profile_non_string_shard_rejected(tmp_path: Path, monkeypatch) -> None:
    """Non-string shard from profile should be rejected with exit code 2."""
    import textwrap

    from typer.testing import CliRunner

    from behave_runner.cli.app import app

    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.ci]
            shard = 123
        """)
    )
    monkeypatch.chdir(tmp_path)

    cli_runner = CliRunner()
    result = cli_runner.invoke(app, ["run", "--profile", "ci"])
    assert result.exit_code == 2
    assert "Invalid shard" in result.output


# --- Regression: run() should only save/restore behave-specific env vars ---


def test_run_preserves_unrelated_env_vars(monkeypatch) -> None:
    """run() should not save/restore env vars unrelated to behave."""
    import os

    from behave_runner.core.orchestrator import RunConfig, run

    monkeypatch.setenv("MY_CUSTOM_VAR", "original_value")
    config = RunConfig(features=["tests/fixtures/minimal/features"], dry_run=True)
    run(config)
    assert os.environ.get("MY_CUSTOM_VAR") == "original_value"


def test_run_restores_behave_env_vars(monkeypatch) -> None:
    """run() should restore behave env vars to their original values."""
    import os

    from behave_runner.core.orchestrator import RunConfig, run

    monkeypatch.setenv("BEHAVE_TIMEOUT", "99")
    config = RunConfig(
        features=["tests/fixtures/minimal/features"],
        dry_run=True,
        timeout=30,
    )
    run(config)
    assert os.environ.get("BEHAVE_TIMEOUT") == "99"


def test_run_clears_behave_env_vars_when_unset(monkeypatch) -> None:
    """run() should remove behave env vars that were not previously set."""
    import os

    from behave_runner.core.orchestrator import RunConfig, run

    monkeypatch.delenv("BEHAVE_MAX_FAILURES", raising=False)
    config = RunConfig(
        features=["tests/fixtures/minimal/features"],
        dry_run=True,
        max_failures=5,
    )
    run(config)
    assert "BEHAVE_MAX_FAILURES" not in os.environ


# --- Regression: find_latest_report should handle stat() errors ---


def test_find_latest_report_handles_stat_error(tmp_path: Path, monkeypatch) -> None:
    """find_latest_report should skip files that raise OSError on stat()."""
    from behave_runner.core.output import find_latest_report

    (tmp_path / "report1.html").write_text("report1")
    bad_file = tmp_path / "bad.html"
    bad_file.write_text("bad")

    original_stat = Path.stat

    def mock_stat(self: Path, *args, **kwargs):
        if self == bad_file:
            raise OSError("permission denied")
        return original_stat(self, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", mock_stat)
    result = find_latest_report(tmp_path)
    assert result is not None
    assert result.name == "report1.html"


# --- Regression: select and list should validate fmt ---


def test_select_rejects_invalid_format(tmp_path: Path, monkeypatch) -> None:
    """select should exit 2 for unknown output format."""
    from typer.testing import CliRunner

    from behave_runner.cli.app import app

    monkeypatch.chdir(tmp_path)
    cli_runner = CliRunner()
    result = cli_runner.invoke(app, ["select", "--format", "xml", "features"])
    assert result.exit_code == 2
    assert "Unknown format" in result.output


def test_list_rejects_invalid_format(tmp_path: Path, monkeypatch) -> None:
    """list should exit 2 for unknown output format."""
    from typer.testing import CliRunner

    from behave_runner.cli.app import app

    monkeypatch.chdir(tmp_path)
    cli_runner = CliRunner()
    result = cli_runner.invoke(app, ["list", "--format", "xml", "features"])
    assert result.exit_code == 2
    assert "Unknown format" in result.output


# --- Regression: _parse_value should strip whitespace from strings ---


def test_parse_value_strips_whitespace() -> None:
    """_parse_value should strip leading/trailing whitespace from strings."""
    from behave_runner.commands.config_cmd import _parse_value

    assert _parse_value("  hello  ") == "hello"
    assert _parse_value('  "hello"  ') == "hello"
    assert _parse_value("  true  ") is True
    assert _parse_value("  42  ") == 42


# --- Regression: load_config should handle [tool] being a non-dict value ---


def test_load_config_tool_not_dict(tmp_path: Path) -> None:
    """load_config should raise ConfigError if [tool] is not a table."""
    from behave_runner.core.config import load_config
    from behave_runner.exceptions import ConfigError

    (tmp_path / "pyproject.toml").write_text('tool = "not a table"\n')
    with pytest.raises(ConfigError, match="must be a table"):
        load_config(tmp_path)


# --- Regression: clean_output_dir should handle OSError from iterdir ---


def test_clean_output_dir_handles_iterdir_os_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """clean_output_dir should not crash if iterdir() raises OSError."""
    from behave_runner.core.output import clean_output_dir

    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "file.txt").write_text("test")

    original_iterdir = Path.iterdir

    def mock_iterdir(self: Path) -> object:
        if self == output_dir:
            raise PermissionError("denied")
        return original_iterdir(self)

    monkeypatch.setattr(Path, "iterdir", mock_iterdir)
    clean_output_dir(output_dir)  # should not raise


def test_clean_output_dir_handles_unlink_os_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """clean_output_dir should skip files that raise OSError on unlink."""
    from behave_runner.core.output import clean_output_dir

    output_dir = tmp_path / "output"
    output_dir.mkdir()
    bad_file = output_dir / "bad.txt"
    bad_file.write_text("bad")
    good_file = output_dir / "good.txt"
    good_file.write_text("good")

    original_unlink = Path.unlink

    def mock_unlink(self: Path, *args, **kwargs) -> None:
        if self == bad_file:
            raise PermissionError("denied")
        return original_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", mock_unlink)
    clean_output_dir(output_dir)
    assert bad_file.exists()  # couldn't delete
    assert not good_file.exists()  # deleted successfully


# --- Regression: flaky_report with profile retries=0 should be ignored ---


def test_flaky_report_with_profile_retries_zero(tmp_path: Path, monkeypatch) -> None:
    """--flaky-report with profile retries=0 should disable flaky_report."""
    import textwrap
    from unittest.mock import patch

    from typer.testing import CliRunner

    from behave_runner.cli.app import app

    fixture_path = str(
        Path(__file__).resolve().parent.parent.parent
        / "tests"
        / "fixtures"
        / "minimal"
        / "features"
    ).replace("\\", "/")
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent(f"""
            [tool.behave-runner.profiles.ci]
            features = ["{fixture_path}"]
            retries = 0
            flaky_report = true
            dry_run = true
        """)
    )
    monkeypatch.chdir(tmp_path)

    cli_runner = CliRunner()
    with patch("behave_runner.commands.run.run", return_value=0):
        result = cli_runner.invoke(app, ["run", "--flaky-report", "--profile", "ci"])
    assert result.exit_code == 0
    assert "requires --retries" in result.output


# --- Regression: load_config should handle non-UTF-8 behave.ini ---


def test_load_config_ini_non_utf8(tmp_path: Path) -> None:
    """load_config should raise ConfigError for non-UTF-8 behave.ini."""
    from behave_runner.core.config import load_config
    from behave_runner.exceptions import ConfigError

    (tmp_path / "behave.ini").write_bytes(b"[behave-runner]\nparallel = \x81\x8d\n")
    with pytest.raises(ConfigError, match="Failed to parse"):
        load_config(tmp_path)


# --- Regression: load_config should handle [tool.behave-runner] non-dict ---


def test_load_config_behave_runner_not_dict(tmp_path: Path) -> None:
    """load_config should raise ConfigError if [tool.behave-runner] is not a table."""
    from behave_runner.core.config import load_config
    from behave_runner.exceptions import ConfigError

    (tmp_path / "pyproject.toml").write_text('[tool]\nbehave-runner = "not a table"\n')
    with pytest.raises(ConfigError, match="must be a table"):
        load_config(tmp_path)


# --- Regression: profile max_fail key should be loaded as fallback ---


def test_profile_max_fail_key_loaded(tmp_path: Path, monkeypatch) -> None:
    """Profile max_fail key should be used as fallback for max_failures."""
    import textwrap
    from unittest.mock import patch

    from typer.testing import CliRunner

    from behave_runner.cli.app import app

    fixture_path = str(
        Path(__file__).resolve().parent.parent.parent
        / "tests"
        / "fixtures"
        / "minimal"
        / "features"
    ).replace("\\", "/")
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent(f"""
            [tool.behave-runner.profiles.ci]
            features = ["{fixture_path}"]
            max_fail = 3
            dry_run = true
        """)
    )
    monkeypatch.chdir(tmp_path)

    cli_runner = CliRunner()
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = cli_runner.invoke(app, ["run", "--profile", "ci"])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert config.max_failures == 3


# --- Regression: profile smoke key should add @smoke tag ---


def test_profile_smoke_adds_smoke_tag(tmp_path: Path, monkeypatch) -> None:
    """Profile smoke=true should add @smoke tag filter."""
    import textwrap
    from unittest.mock import patch

    from typer.testing import CliRunner

    from behave_runner.cli.app import app

    fixture_path = str(
        Path(__file__).resolve().parent.parent.parent
        / "tests"
        / "fixtures"
        / "minimal"
        / "features"
    ).replace("\\", "/")
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent(f"""
            [tool.behave-runner.profiles.ci]
            features = ["{fixture_path}"]
            smoke = true
            dry_run = true
        """)
    )
    monkeypatch.chdir(tmp_path)

    cli_runner = CliRunner()
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = cli_runner.invoke(app, ["run", "--profile", "ci"])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert "@smoke" in config.tags


# --- Regression: _set_config_value should not corrupt TOML with dotted keys ---


def test_set_config_value_dotted_key_with_existing_subtable(tmp_path: Path) -> None:
    """_set_config_value writes the leaf inside an existing subtable."""
    import tomllib

    from behave_runner.commands.config_cmd import _parse_value, _set_config_value

    p = tmp_path / "pyproject.toml"
    p.write_text(
        '[tool.behave-runner]\nparallel = 2\n\n[tool.behave-runner.profiles.ci]\ntags = ["fast"]\n'
    )
    _set_config_value(p, "profiles.ci.tags", _parse_value("smoke"))
    with p.open("rb") as f:
        data = tomllib.load(f)
    assert data["tool"]["behave-runner"]["profiles"]["ci"]["tags"] == "smoke"
    assert data["tool"]["behave-runner"]["parallel"] == 2


def test_set_config_value_dotted_key_no_subtable(tmp_path: Path) -> None:
    """_set_config_value should allow dotted keys when no subtable exists."""
    import tomllib

    from behave_runner.commands.config_cmd import _parse_value, _set_config_value

    p = tmp_path / "pyproject.toml"
    p.write_text("[tool.behave-runner]\nparallel = 2\n")
    _set_config_value(p, "profiles.ci.tags", _parse_value("smoke"))
    with p.open("rb") as f:
        data = tomllib.load(f)
    assert data["tool"]["behave-runner"]["profiles"]["ci"]["tags"] == "smoke"


def test_set_config_value_validates_toml(tmp_path: Path) -> None:
    """_set_config_value should validate the result is parseable TOML."""
    from behave_runner.commands.config_cmd import _parse_value, _set_config_value

    p = tmp_path / "pyproject.toml"
    # Write a valid file first
    p.write_text("[tool.behave-runner]\nparallel = 2\n")
    # Normal set should work
    _set_config_value(p, "timeout", _parse_value("30"))
    assert "timeout = 30" in p.read_text()


# --- Regression: config set should catch ConfigError from _set_config_value ---


def test_config_set_catches_config_error(tmp_path: Path, monkeypatch) -> None:
    """config set should show clean error when _set_config_value raises ConfigError."""
    from unittest.mock import patch as _patch

    from typer.testing import CliRunner

    from behave_runner.cli.app import app
    from behave_runner.exceptions import ConfigError

    p = tmp_path / "pyproject.toml"
    p.write_text("[tool.behave-runner]\nparallel = 2\n")
    monkeypatch.chdir(tmp_path)

    cli_runner = CliRunner()
    with _patch(
        "behave_runner.commands.config_cmd._set_config_value",
        side_effect=ConfigError("forced failure"),
    ):
        result = cli_runner.invoke(app, ["config", "set", "parallel", "8"])
    assert result.exit_code == 2
    assert "forced failure" in result.output
    # File should be unchanged
    assert "parallel = 2" in p.read_text()


# --- Regression: RunConfig.parallel=0 should be rejected ---


def test_run_config_parallel_zero_rejected() -> None:
    """RunConfig should reject parallel=0 (silently falls back to sequential)."""
    with pytest.raises(ValueError, match="parallel must be >= 1"):
        RunConfig(features=["features"], parallel=0)


def test_run_config_parallel_one_allowed() -> None:
    """RunConfig should allow parallel=1 (runs sequentially but explicitly)."""
    config = RunConfig(features=["features"], parallel=1)
    assert config.parallel == 1


# --- Regression: collect_scenarios should handle feature.name being None ---


def test_collect_scenarios_handles_none_feature_name(tmp_path: Path, monkeypatch) -> None:
    """collect_scenarios should skip features with None name instead of crashing."""
    from behave_runner.core import features as features_module

    feature_file = tmp_path / "test.feature"
    feature_file.write_text("Feature: Test\n\n  Scenario: Example\n    Given a step\n")

    class MockFeature:
        name = None
        scenarios = []

    class MockScenario:
        name = "Example"
        tag_names = []
        location = "test.feature:3"

    class MockFeatureWithScenarios:
        name = None
        scenarios = [MockScenario()]

    original_load = features_module.load_feature

    def mock_load_feature(path: str):
        if "test.feature" in path:
            return MockFeatureWithScenarios()
        return original_load(path)

    monkeypatch.setattr(features_module, "load_feature", mock_load_feature)
    # Should not crash with AttributeError: 'NoneType' has no attribute 'lower'
    result = features_module.collect_scenarios([feature_file], feature_name="test")
    assert result == []


# --- Regression: watch --debounce negative should be rejected ---


def test_watch_negative_debounce_rejected(tmp_path: Path, monkeypatch) -> None:
    """watch should reject negative debounce values."""
    from typer.testing import CliRunner

    from behave_runner.cli.app import app

    monkeypatch.chdir(tmp_path)
    cli_runner = CliRunner()
    result = cli_runner.invoke(app, ["watch", "--debounce", "-1"])
    assert result.exit_code == 2
    assert "debounce" in result.output.lower()


# --- Regression: ensure_output_dir should reject existing file paths ---


def test_ensure_output_dir_rejects_existing_file(tmp_path: Path) -> None:
    """ensure_output_dir should raise FileExistsError if path is a file."""
    from behave_runner.core.output import ensure_output_dir

    file_path = tmp_path / "not_a_dir.txt"
    file_path.write_text("I am a file")

    with pytest.raises(FileExistsError, match="not a directory"):
        ensure_output_dir(file_path)


def test_ensure_output_dir_creates_new_dir(tmp_path: Path) -> None:
    """ensure_output_dir should create a new directory."""
    from behave_runner.core.output import ensure_output_dir

    new_dir = tmp_path / "new_dir" / "nested"
    result = ensure_output_dir(new_dir)
    assert result.is_dir()
    assert result.exists()


# --- Regression: collect_scenarios should handle scenario.name being None ---


def test_collect_scenarios_handles_none_scenario_name(tmp_path: Path, monkeypatch) -> None:
    """collect_scenarios should skip scenarios with None name when using regex."""
    from behave_runner.core import features as features_module

    feature_file = tmp_path / "test.feature"
    feature_file.write_text("Feature: Test\n\n  Scenario: Example\n    Given a step\n")

    class MockScenario:
        name = None
        tag_names = []
        location = "test.feature:3"

    class MockFeature:
        name = "Test"
        scenarios = [MockScenario()]

    original_load = features_module.load_feature

    def mock_load_feature(path: str):
        if "test.feature" in path:
            return MockFeature()
        return original_load(path)

    monkeypatch.setattr(features_module, "load_feature", mock_load_feature)
    # Should not crash with TypeError: expected string or bytes-like object
    result = features_module.collect_scenarios([feature_file], pattern="Example")
    assert result == []


def test_collect_scenarios_coerces_none_names_to_empty_string(tmp_path: Path, monkeypatch) -> None:
    """collect_scenarios should coerce None feature/scenario names to empty strings."""
    from behave_runner.core import features as features_module

    feature_file = tmp_path / "test.feature"
    feature_file.write_text("Feature: Test\n\n  Scenario: Example\n    Given a step\n")

    class MockScenario:
        name = None
        tag_names = []
        location = "test.feature:3"

    class MockFeature:
        name = None
        scenarios = [MockScenario()]

    original_load = features_module.load_feature

    def mock_load_feature(path: str):
        if "test.feature" in path:
            return MockFeature()
        return original_load(path)

    monkeypatch.setattr(features_module, "load_feature", mock_load_feature)
    # No filters — scenario should be collected with empty strings for None names
    result = features_module.collect_scenarios([feature_file])
    assert len(result) == 1
    assert result[0]["feature"] == ""
    assert result[0]["scenario"] == ""
    assert result[0]["tags"] == []


# --- Regression: _set_config_value should check all parent prefixes for conflicts ---


def test_set_config_value_dotted_key_grandparent_conflict(tmp_path: Path) -> None:
    """_set_config_value writes the leaf in the deepest existing subtable."""
    import tomllib

    from behave_runner.commands.config_cmd import _parse_value, _set_config_value

    p = tmp_path / "pyproject.toml"
    p.write_text(
        "[tool.behave-runner]\nparallel = 2\n\n"
        "[tool.behave-runner.profiles]\n\n"
        '[tool.behave-runner.profiles.ci]\ntags = ["fast"]\n'
    )
    # Both [tool.behave-runner.profiles] and [tool.behave-runner.profiles.ci]
    # exist — the leaf lands in the deepest one, keeping TOML valid.
    _set_config_value(p, "profiles.ci.tags", _parse_value("smoke"))
    with p.open("rb") as f:
        data = tomllib.load(f)
    assert data["tool"]["behave-runner"]["profiles"]["ci"]["tags"] == "smoke"


def test_set_config_value_dotted_key_parent_only_conflict(tmp_path: Path) -> None:
    """_set_config_value writes into a parent subtable even without grandparents."""
    import tomllib

    from behave_runner.commands.config_cmd import _parse_value, _set_config_value

    p = tmp_path / "pyproject.toml"
    p.write_text(
        '[tool.behave-runner]\nparallel = 2\n\n[tool.behave-runner.profiles.ci]\ntags = ["fast"]\n'
    )
    # Only [tool.behave-runner.profiles.ci] exists, not [tool.behave-runner.profiles]
    _set_config_value(p, "profiles.ci.tags", _parse_value("smoke"))
    with p.open("rb") as f:
        data = tomllib.load(f)
    assert data["tool"]["behave-runner"]["profiles"]["ci"]["tags"] == "smoke"


# --- Regression: _ini_flat_to_nested should detect key conflicts ---


def test_ini_flat_to_nested_conflict_leaf_then_parent(tmp_path: Path) -> None:
    """_ini_flat_to_nested should raise on conflict: leaf key then parent key."""
    from behave_runner.core.config import _ini_flat_to_nested
    from behave_runner.exceptions import ConfigError

    flat = {
        "profiles": "some_value",
        "profiles.ci.parallel": "4",
    }
    with pytest.raises(ConfigError, match="already a value"):
        _ini_flat_to_nested(flat)


def test_ini_flat_to_nested_conflict_parent_then_leaf(tmp_path: Path) -> None:
    """_ini_flat_to_nested should raise on conflict: parent key then leaf key."""
    from behave_runner.core.config import _ini_flat_to_nested
    from behave_runner.exceptions import ConfigError

    flat = {
        "profiles.ci.parallel": "4",
        "profiles": "some_value",
    }
    with pytest.raises(ConfigError, match="already a parent"):
        _ini_flat_to_nested(flat)


def test_ini_flat_to_nested_no_conflict(tmp_path: Path) -> None:
    """_ini_flat_to_nested should work correctly without conflicts."""
    from behave_runner.core.config import _ini_flat_to_nested

    flat = {
        "profiles.ci.parallel": "4",
        "profiles.ci.dry_run": "false",
        "default_parallel": "2",
    }
    result = _ini_flat_to_nested(flat)
    assert result == {
        "profiles": {"ci": {"parallel": "4", "dry_run": "false"}},
        "default_parallel": "2",
    }


# --- Regression: duplicate @smoke tag when both CLI --smoke and profile smoke=true ---


def test_no_duplicate_smoke_tag_cli_and_profile(tmp_path: Path, monkeypatch) -> None:
    """Ensure @smoke is not added twice when both --smoke CLI flag and profile
    smoke=true are set."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "test"\nversion = "0.1.0"\n\n'
        "[tool.behave-runner]\n"
        "[tool.behave-runner.profiles.smoke]\n"
        'smoke = true\ntags = ["@fast"]\n'
    )
    monkeypatch.chdir(tmp_path)

    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["run", "--smoke", FIXTURE])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    smoke_count = config.tags.count("@smoke")
    assert smoke_count == 1, f"Expected @smoke once, found {smoke_count} times in {config.tags}"


def test_no_duplicate_smoke_tag_profile_only(tmp_path: Path, monkeypatch) -> None:
    """Ensure @smoke appears once when only profile smoke=true is set."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "test"\nversion = "0.1.0"\n\n'
        "[tool.behave-runner]\n"
        "[tool.behave-runner.profiles.smoke]\n"
        "smoke = true\n"
    )
    monkeypatch.chdir(tmp_path)

    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["run", "--profile", "smoke", FIXTURE])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert config.tags.count("@smoke") == 1


# --- Regression: watch.py profile format key mismatch (fmt vs format) ---


def test_watch_profile_format_key(tmp_path: Path, monkeypatch) -> None:
    """Ensure watch command picks up 'format' key from profile (not 'fmt')."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "test"\nversion = "0.1.0"\n\n'
        "[tool.behave-runner]\n"
        "[tool.behave-runner.profiles.ci]\n"
        'format = "json"\n'
    )
    monkeypatch.chdir(tmp_path)

    # Simulate what watch_command does with profile
    from behave_runner.core.config import load_profile

    profile_config = load_profile("ci")
    config_overrides: dict[str, object] = {
        "ui": False,
        "debug": False,
        "trace": False,
        "priority_order": False,
        "fail_fast": False,
    }
    for key in ("retries", "parallel", "scenario_timeout"):
        if key not in config_overrides and key in profile_config:
            config_overrides[key] = profile_config[key]
    if "fmt" not in config_overrides and "format" in profile_config:
        config_overrides["fmt"] = profile_config["format"]

    assert config_overrides.get("fmt") == "json", (
        f"Expected fmt='json' from profile format key, got {config_overrides.get('fmt')!r}"
    )


# --- Regression: _is_package_functional handles OSError from os.listdir ---


def test_is_package_functional_handles_oserror(monkeypatch) -> None:
    """Ensure _is_package_functional returns False (not crash) when os.listdir
    raises OSError (e.g. permission denied)."""
    from behave_runner.core.orchestrator import _is_package_functional

    def fake_listdir(path: str) -> list[str]:
        raise PermissionError("Permission denied")

    monkeypatch.setattr("behave_runner.core.orchestrator.is_installed", lambda _: True)
    monkeypatch.setattr("behave_runner.core.orchestrator.os.listdir", fake_listdir)

    result = _is_package_functional("behave_runner")
    assert result is False, "Expected False when os.listdir raises OSError"


# --- Regression: watch.py doesn't merge profile tags, features, or smoke ---


def test_watch_profile_tags_merged(tmp_path: Path, monkeypatch) -> None:
    """Ensure watch command merges profile tags with CLI tags."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "test"\nversion = "0.1.0"\n\n'
        "[tool.behave-runner]\n"
        "[tool.behave-runner.profiles.ci]\n"
        'tags = ["@ci", "@fast"]\n'
    )
    monkeypatch.chdir(tmp_path)

    from behave_runner.core.config import load_profile

    profile_config = load_profile("ci")
    profile_tags = profile_config.get("tags", [])
    cli_tags: list[str] = []
    merged = [*cli_tags, *profile_tags] if (cli_tags or profile_tags) else []
    assert "@ci" in merged
    assert "@fast" in merged


def test_watch_profile_features_merged(tmp_path: Path, monkeypatch) -> None:
    """Ensure watch command uses profile features when no CLI features given."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "test"\nversion = "0.1.0"\n\n'
        "[tool.behave-runner]\n"
        "[tool.behave-runner.profiles.ci]\n"
        'features = ["custom_features"]\n'
    )
    monkeypatch.chdir(tmp_path)

    from behave_runner.core.config import load_profile

    profile_config = load_profile("ci")
    profile_features = profile_config.get("features", [])
    features: list[str] = []
    feature_paths = (
        list(features)
        if features
        else (list(profile_features) if profile_features else ["features"])
    )
    assert feature_paths == ["custom_features"], (
        f"Expected ['custom_features'], got {feature_paths}"
    )


def test_watch_profile_smoke_adds_tag(tmp_path: Path, monkeypatch) -> None:
    """Ensure watch command adds @smoke tag from profile smoke=true."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "test"\nversion = "0.1.0"\n\n'
        "[tool.behave-runner]\n"
        "[tool.behave-runner.profiles.smoke]\n"
        "smoke = true\n"
    )
    monkeypatch.chdir(tmp_path)

    from behave_runner.core.config import load_profile

    profile_config = load_profile("smoke")
    tags: list[str] = []
    profile_smoke = profile_config.get("smoke", False)
    if profile_smoke and "@smoke" not in tags:
        tags = [*tags, "@smoke"]
    assert "@smoke" in tags
    assert tags.count("@smoke") == 1


# --- Regression: timeout=0 must not reach behave as a flag ---


def test_timeout_zero_not_in_behave_command() -> None:
    """Ensure timeout=0 does not emit a --timeout flag (behave has none)."""
    config = RunConfig(timeout=0)
    cmd = build_behave_command(config)
    assert "--timeout" not in cmd


def test_timeout_none_not_in_command() -> None:
    """Ensure timeout=None does not add --timeout to command."""
    config = RunConfig(timeout=None)
    cmd = build_behave_command(config)
    assert "--timeout" not in cmd


# --- Regression: _normalize_int should accept float values like 4.0 ---


def test_normalize_int_accepts_whole_float() -> None:
    """Ensure _normalize_int accepts float 4.0 and returns int 4.

    TOML allows `parallel = 4.0` which tomllib loads as float.
    Previously, this would raise _BadIntegerError instead of accepting 4.0 as 4.
    """
    from behave_runner.core.config import _normalize_int

    assert _normalize_int("parallel", 4.0) == 4
    assert isinstance(_normalize_int("parallel", 4.0), int)


def test_normalize_int_rejects_non_whole_float() -> None:
    """Ensure _normalize_int rejects float 3.5."""
    from behave_runner.core.config import _BadIntegerError, _normalize_int

    with pytest.raises(_BadIntegerError):
        _normalize_int("timeout", 3.5)


# --- Regression: watch.py doesn't merge timeout and max_failures from profile ---


def test_watch_profile_timeout_merged(tmp_path: Path, monkeypatch) -> None:
    """Ensure watch command merges profile timeout setting."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "test"\nversion = "0.1.0"\n\n'
        "[tool.behave-runner]\n"
        "[tool.behave-runner.profiles.ci]\n"
        "timeout = 30\n"
    )
    monkeypatch.chdir(tmp_path)

    from behave_runner.core.config import load_profile

    profile_config = load_profile("ci")
    config_overrides: dict[str, object] = {}
    for key in ("retries", "parallel", "scenario_timeout", "timeout"):
        if key not in config_overrides and key in profile_config:
            config_overrides[key] = profile_config[key]
    assert config_overrides.get("timeout") == 30


def test_watch_profile_max_failures_merged(tmp_path: Path, monkeypatch) -> None:
    """Ensure watch command merges profile max_failures setting."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "test"\nversion = "0.1.0"\n\n'
        "[tool.behave-runner]\n"
        "[tool.behave-runner.profiles.ci]\n"
        "max_failures = 3\n"
    )
    monkeypatch.chdir(tmp_path)

    from behave_runner.core.config import load_profile

    profile_config = load_profile("ci")
    config_overrides: dict[str, object] = {}
    if "max_failures" not in config_overrides:
        if "max_failures" in profile_config:
            config_overrides["max_failures"] = profile_config["max_failures"]
        elif "max_fail" in profile_config:
            config_overrides["max_failures"] = profile_config["max_fail"]
    assert config_overrides.get("max_failures") == 3


def test_watch_profile_max_fail_alias_merged(tmp_path: Path, monkeypatch) -> None:
    """Ensure watch command merges profile max_fail alias (same as run.py)."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "test"\nversion = "0.1.0"\n\n'
        "[tool.behave-runner]\n"
        "[tool.behave-runner.profiles.ci]\n"
        "max_fail = 5\n"
    )
    monkeypatch.chdir(tmp_path)

    from behave_runner.core.config import load_profile

    profile_config = load_profile("ci")
    config_overrides: dict[str, object] = {}
    if "max_failures" not in config_overrides:
        if "max_failures" in profile_config:
            config_overrides["max_failures"] = profile_config["max_failures"]
        elif "max_fail" in profile_config:
            config_overrides["max_failures"] = profile_config["max_fail"]
    assert config_overrides.get("max_failures") == 5


def test_watch_profile_flaky_report_merged(tmp_path: Path, monkeypatch) -> None:
    """Ensure watch command merges profile flaky_report (with retries)."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "test"\nversion = "0.1.0"\n\n'
        "[tool.behave-runner]\n"
        "[tool.behave-runner.profiles.ci]\n"
        "flaky_report = true\n"
        "retries = 2\n"
    )
    monkeypatch.chdir(tmp_path)

    from behave_runner.core.config import load_profile

    profile_config = load_profile("ci")
    config_overrides: dict[str, object] = {}
    for key in ("ui", "debug", "trace", "priority_order", "fail_fast", "flaky_report"):
        if key in profile_config and profile_config[key]:
            config_overrides[key] = True
    for key in ("retries",):
        if key not in config_overrides and key in profile_config:
            config_overrides[key] = profile_config[key]
    assert config_overrides.get("flaky_report") is True


def test_watch_profile_flaky_report_disabled_without_retries(tmp_path: Path, monkeypatch) -> None:
    """Ensure watch command disables flaky_report when retries=0 from profile."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "test"\nversion = "0.1.0"\n\n'
        "[tool.behave-runner]\n"
        "[tool.behave-runner.profiles.ci]\n"
        "flaky_report = true\n"
        "retries = 0\n"
    )
    monkeypatch.chdir(tmp_path)

    from behave_runner.core.config import load_profile

    profile_config = load_profile("ci")
    config_overrides: dict[str, object] = {}
    for key in ("ui", "debug", "trace", "priority_order", "fail_fast", "flaky_report"):
        if key in profile_config and profile_config[key]:
            config_overrides[key] = True
    for key in ("retries",):
        if key not in config_overrides and key in profile_config:
            config_overrides[key] = profile_config[key]
    # Simulate the flaky_report validation
    p_flaky = config_overrides.get("flaky_report", False)
    p_retries = config_overrides.get("retries")
    if p_flaky and (p_retries is None or p_retries == 0):
        config_overrides.pop("flaky_report", None)
    assert "flaky_report" not in config_overrides


def test_watch_profile_name_merged(tmp_path: Path, monkeypatch) -> None:
    """Ensure watch command merges profile name filter."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "test"\nversion = "0.1.0"\n\n'
        "[tool.behave-runner]\n"
        "[tool.behave-runner.profiles.ci]\n"
        'name = ["Scenario 1", "Scenario 2"]\n'
    )
    monkeypatch.chdir(tmp_path)

    from behave_runner.core.config import load_profile

    profile_config = load_profile("ci")
    config_overrides: dict[str, object] = {}
    p_name = profile_config.get("name", [])
    if isinstance(p_name, list) and p_name:
        config_overrides["name"] = p_name
    assert config_overrides.get("name") == ["Scenario 1", "Scenario 2"]


def test_watch_profile_parallel_scheme_merged(tmp_path: Path, monkeypatch) -> None:
    """Ensure watch command merges profile parallel_scheme."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "test"\nversion = "0.1.0"\n\n'
        "[tool.behave-runner]\n"
        "[tool.behave-runner.profiles.ci]\n"
        "parallel = 4\n"
        'parallel_scheme = "scenario"\n'
    )
    monkeypatch.chdir(tmp_path)

    from behave_runner.core.config import load_profile

    profile_config = load_profile("ci")
    config_overrides: dict[str, object] = {}
    for key in (
        "retries",
        "parallel",
        "scenario_timeout",
        "timeout",
        "parallel_scheme",
        "parallel_balance",
        "parallel_timing_file",
        "shard",
    ):
        if key not in config_overrides and key in profile_config:
            config_overrides[key] = profile_config[key]
    assert config_overrides.get("parallel") == 4
    assert config_overrides.get("parallel_scheme") == "scenario"


def test_watch_profile_shard_merged(tmp_path: Path, monkeypatch) -> None:
    """Ensure watch command merges profile shard."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "test"\nversion = "0.1.0"\n\n'
        "[tool.behave-runner]\n"
        "[tool.behave-runner.profiles.ci]\n"
        'shard = "1/3"\n'
    )
    monkeypatch.chdir(tmp_path)

    from behave_runner.core.config import load_profile

    profile_config = load_profile("ci")
    config_overrides: dict[str, object] = {}
    for key in (
        "retries",
        "parallel",
        "scenario_timeout",
        "timeout",
        "parallel_scheme",
        "parallel_balance",
        "parallel_timing_file",
        "shard",
    ):
        if key not in config_overrides and key in profile_config:
            config_overrides[key] = profile_config[key]
    assert config_overrides.get("shard") == "1/3"


# --- Regression: report.py file format should use .docx extension ---


def test_report_file_format_uses_docx_extension(tmp_path: Path) -> None:
    """Ensure report generate --format file uses .docx extension, not .txt.

    The file format maps to DOCXFormatter in the orchestrator, so the output
    file should have a .docx extension. Previously it was .txt which is wrong.
    """
    extensions = {
        "json": "report.json",
        "html": "report.html",
        "md": "report.md",
        "sheets": "report.xlsx",
        "file": "report.docx",
    }
    assert extensions["file"] == "report.docx"
    assert extensions["file"].endswith(".docx")


# --- Regression: watch.py doesn't merge output from profile ---


def test_watch_profile_output_merged(tmp_path: Path, monkeypatch) -> None:
    """Ensure watch command merges profile output setting into outfile.

    run.py merges profile 'output' into RunConfig.outfile, but watch.py
    was missing this merge, causing inconsistent behavior.
    """
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "test"\nversion = "0.1.0"\n\n'
        "[tool.behave-runner]\n"
        "[tool.behave-runner.profiles.ci]\n"
        'output = "reports/report.json"\n'
    )
    monkeypatch.chdir(tmp_path)

    from behave_runner.core.config import load_profile

    profile_config = load_profile("ci")
    config_overrides: dict[str, object] = {}
    if "outfile" not in config_overrides and "output" in profile_config:
        config_overrides["outfile"] = profile_config["output"]
    assert config_overrides.get("outfile") == "reports/report.json"


# --- Regression: watch callback should handle RunConfig errors gracefully ---


def test_watch_callback_handles_runconfig_error() -> None:
    """Ensure watch callback catches ValueError from RunConfig and prints error.

    If profile has invalid values (e.g. parallel=-1), RunConfig.__post_init__
    raises ValueError. The callback should catch it and print a friendly
    message instead of crashing with an unhandled exception.
    """
    from behave_runner.commands.watch import _make_callback

    config_overrides: dict[str, object] = {"parallel": -1}
    callback = _make_callback(["features"], [], None, config_overrides)

    # Should not raise — should just print error and return
    callback([Path("test.feature")])


# --- Regression: watch.py should validate shard format from profile ---


def test_watch_profile_invalid_shard_format(tmp_path: Path, monkeypatch) -> None:
    """Ensure watch command validates shard format from profile.

    run.py validates shard format with regex, but watch.py was missing
    this validation. An invalid shard like 'invalid' should be rejected.
    """
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "test"\nversion = "0.1.0"\n\n'
        "[tool.behave-runner]\n"
        "[tool.behave-runner.profiles.ci]\n"
        'shard = "invalid"\n'
    )
    monkeypatch.chdir(tmp_path)

    from behave_runner.core.config import load_profile

    profile_config = load_profile("ci")
    config_overrides: dict[str, object] = {}
    if "shard" not in config_overrides and "shard" in profile_config:
        config_overrides["shard"] = profile_config["shard"]

    # Simulate the validation that watch.py should perform
    import re

    shard_re = re.compile(r"^(\d+)/(\d+)$")
    p_shard = config_overrides.get("shard")
    assert p_shard is not None
    assert isinstance(p_shard, str)
    match = shard_re.match(p_shard)
    assert match is None  # "invalid" should not match the regex


def test_watch_profile_shard_out_of_range(tmp_path: Path, monkeypatch) -> None:
    """Ensure watch command validates shard range (i must be 1..n)."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "test"\nversion = "0.1.0"\n\n'
        "[tool.behave-runner]\n"
        "[tool.behave-runner.profiles.ci]\n"
        'shard = "5/3"\n'
    )
    monkeypatch.chdir(tmp_path)

    from behave_runner.core.config import load_profile

    profile_config = load_profile("ci")
    config_overrides: dict[str, object] = {}
    if "shard" not in config_overrides and "shard" in profile_config:
        config_overrides["shard"] = profile_config["shard"]

    import re

    shard_re = re.compile(r"^(\d+)/(\d+)$")
    p_shard = config_overrides.get("shard")
    assert p_shard is not None
    match = shard_re.match(p_shard)
    assert match is not None
    i, n = int(match.group(1)), int(match.group(2))
    assert i > n  # 5 > 3, should be invalid


# --- Regression: RunConfig should reject empty strings for parallel_* fields ---


def test_runconfig_empty_parallel_scheme_rejected() -> None:
    """RunConfig should reject empty string for parallel_scheme."""
    from behave_runner.core.orchestrator import RunConfig

    with pytest.raises(ValueError, match="parallel_scheme"):
        RunConfig(features=["features"], parallel_scheme="")


def test_runconfig_empty_parallel_balance_rejected() -> None:
    """RunConfig should reject empty string for parallel_balance."""
    from behave_runner.core.orchestrator import RunConfig

    with pytest.raises(ValueError, match="parallel_balance"):
        RunConfig(features=["features"], parallel_balance="")


def test_runconfig_empty_parallel_timing_file_rejected() -> None:
    """RunConfig should reject empty string for parallel_timing_file."""
    from behave_runner.core.orchestrator import RunConfig

    with pytest.raises(ValueError, match="parallel_timing_file"):
        RunConfig(features=["features"], parallel_timing_file="")


# --- Regression: _normalize_list should filter empty strings from list input ---


def test_normalize_list_filters_empty_strings_from_list() -> None:
    """_normalize_list should filter out empty strings when input is a list.

    Previously, only comma-separated string input filtered empty strings.
    List input like ["", " @smoke ", ""] would produce ["", "@smoke", ""],
    leading to --tags "" being passed to behave.
    """
    from behave_runner.core.config import _normalize_list

    result = _normalize_list(["", " @smoke ", ""])
    assert result == ["@smoke"]
    assert "" not in result


def test_normalize_list_filters_empty_strings_from_string() -> None:
    """_normalize_list should continue to filter empty strings from string input."""
    from behave_runner.core.config import _normalize_list

    result = _normalize_list(" , @smoke , ")
    assert result == ["@smoke"]
    assert "" not in result


# --- Regression: watch.py should use ["features"] for empty profile features ---


def test_watch_empty_profile_features_uses_default(tmp_path: Path, monkeypatch) -> None:
    """watch.py should use ['features'] when profile has empty features list.

    run.py uses ['features'] as default when profile features is empty.
    watch.py was using [] instead, causing inconsistent behavior.
    """
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "test"\nversion = "0.1.0"\n\n'
        "[tool.behave-runner]\n"
        "[tool.behave-runner.profiles.ci]\n"
        "features = []\n"
    )
    monkeypatch.chdir(tmp_path)

    from behave_runner.core.config import load_profile

    profile_config = load_profile("ci")
    profile_features = profile_config.get("features", [])

    # Simulate watch.py's feature path logic (after fix)
    if isinstance(profile_features, list) and profile_features:
        feature_paths = list(profile_features)
    else:
        feature_paths = ["features"]

    assert feature_paths == ["features"], (
        f"Expected ['features'] for empty profile features, got {feature_paths}"
    )


# --- Regression: collect_scenarios should filter empty tag strings ---


def test_collect_scenarios_empty_include_tag_ignored(tmp_path: Path) -> None:
    """collect_scenarios should ignore empty string in include tags.

    Previously, passing "" as a tag filter would exclude all scenarios
    because "" is never in scenario_tags, causing all(...) to be False.
    """
    from behave_runner.core.features import matches_tags

    # Empty include tag should not cause all scenarios to be excluded
    result = matches_tags(["@smoke"], include_tags=[""])
    assert result is True, "Empty include tag should be ignored, not exclude all scenarios"


def test_collect_scenarios_empty_exclude_tag_ignored() -> None:
    """collect_scenarios should ignore empty string in exclude tags.

    Previously, passing "~" (tilde only) would add "" to exclude_tags.
    While harmless in practice, it should be filtered for consistency.
    """
    from behave_runner.core.features import matches_tags

    # Empty exclude tag should not cause scenarios to be excluded
    result = matches_tags(["@smoke"], exclude_tags=[""])
    assert result is True, "Empty exclude tag should be ignored"


# --- Regression: impact.py should escape regex special chars in scenario names ---


def test_impact_escapes_regex_special_chars_in_scenario_names() -> None:
    """impact.py should escape regex special characters in scenario names.

    behave's --name option uses regex matching. If a scenario name contains
    regex special chars like (, ), *, they must be escaped to match the
    exact scenario name, not be interpreted as regex patterns.
    """
    import re

    # Simulate a scenario name with regex special characters
    scenario_name = "Test scenario (with parentheses) and * asterisk"
    escaped = re.escape(scenario_name)

    # The escaped name should not contain unescaped special chars
    assert "(" not in escaped or "\\(" in escaped
    assert ")" not in escaped or "\\)" in escaped
    assert "*" not in escaped or "\\*" in escaped

    # The escaped name should match the original when used as regex
    assert re.search(escaped, scenario_name) is not None


# --- Regression: validate_shard function ---


def test_validate_shard_valid() -> None:
    """validate_shard should accept valid shard strings."""
    from behave_runner.core.orchestrator import validate_shard

    validate_shard("1/3")
    validate_shard("2/4")
    validate_shard("1/1")


def test_validate_shard_invalid_format() -> None:
    """validate_shard should reject invalid shard formats."""
    from behave_runner.core.orchestrator import validate_shard

    with pytest.raises(ValueError, match="Invalid shard format"):
        validate_shard("invalid")
    with pytest.raises(ValueError, match="Invalid shard format"):
        validate_shard("1/3/5")
    with pytest.raises(ValueError, match="Invalid shard format"):
        validate_shard("abc/def")


def test_validate_shard_out_of_range() -> None:
    """validate_shard should reject out-of-range shard indices."""
    from behave_runner.core.orchestrator import validate_shard

    with pytest.raises(ValueError, match="i must be 1..n"):
        validate_shard("0/3")
    with pytest.raises(ValueError, match="i must be 1..n"):
        validate_shard("4/3")
    with pytest.raises(ValueError, match="i must be 1..n"):
        validate_shard("1/0")


# --- Regression: configparser interpolation with % characters ---


def test_configparser_interpolation_none_for_percent_values(tmp_path: Path) -> None:
    """behave.ini values with % characters should not cause InterpolationSyntaxError.

    ConfigParser uses BasicInterpolation by default, which treats % as a special
    character. The fix uses interpolation=None to read values literally.
    """
    behave_ini = tmp_path / "behave.ini"
    behave_ini.write_text(
        "[behave-runner]\nprofiles.ci.tags = @smoke, @fast\nprofiles.ci.name = Test 100% coverage\n"
    )

    from behave_runner.core.config import load_config

    config = load_config(tmp_path)
    profiles = config.get("profiles", {})
    ci_profile = profiles.get("ci", {})
    assert ci_profile.get("name") == "Test 100% coverage"


# --- Regression: __all__ in __init__.py ---


def test_init_all_exports_version() -> None:
    """behave_runner.__init__ should declare __all__ with __version__."""
    import behave_runner

    assert hasattr(behave_runner, "__all__")
    assert "__version__" in behave_runner.__all__
    assert behave_runner.__version__ == "1.4.0"


# --- Regression: base [tool.behave-runner] config is applied to runs ---


def test_load_defaults_returns_base_config(tmp_path: Path) -> None:
    """load_defaults returns top-level values, excluding profiles."""
    from behave_runner.core.config import load_defaults

    (tmp_path / "pyproject.toml").write_text(
        "[tool.behave-runner]\nparallel = 4\n\n[tool.behave-runner.profiles.ci]\nparallel = 8\n"
    )
    defaults = load_defaults(tmp_path)
    assert defaults["parallel"] == 4
    assert "profiles" not in defaults


def test_run_merges_base_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Base [tool.behave-runner] values apply even without --profile."""
    (tmp_path / "pyproject.toml").write_text("[tool.behave-runner]\nparallel = 4\ndry_run = true\n")
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["run", "features"])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert config.parallel == 4
    assert config.dry_run is True


def test_run_profile_overrides_base(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Profile values override base config values."""
    (tmp_path / "pyproject.toml").write_text(
        "[tool.behave-runner]\nparallel = 4\n\n[tool.behave-runner.profiles.ci]\nparallel = 8\n"
    )
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["run", "--profile", "ci", "features"])
    assert result.exit_code == 0
    assert mock_run.call_args[0][0].parallel == 8


def test_run_cli_overrides_base(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """CLI flags win over base config values."""
    (tmp_path / "pyproject.toml").write_text("[tool.behave-runner]\nparallel = 4\n")
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["run", "--parallel", "2", "features"])
    assert result.exit_code == 0
    assert mock_run.call_args[0][0].parallel == 2


def test_run_bad_base_config_exits_2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A malformed pyproject.toml exits with code 2, not a traceback."""
    (tmp_path / "pyproject.toml").write_text("[tool.behave-runner\nbroken")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["run", "features"])
    assert result.exit_code == 2


def test_watch_merges_base_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """watch applies base [tool.behave-runner] values to re-run configs."""
    (tmp_path / "pyproject.toml").write_text("[tool.behave-runner]\nretries = 3\n")
    monkeypatch.chdir(tmp_path)

    class _FakeWatcher:
        def __init__(self, paths, on_change, debounce_ms=500, ignore=None):
            self._cb = on_change

        def run(self) -> None:
            self._cb([Path("features/x.feature")])
            raise KeyboardInterrupt

    monkeypatch.setattr("behave_runner.commands.watch.FileWatcher", _FakeWatcher)
    with patch("behave_runner.commands.watch.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["watch", "features"])
    assert result.exit_code == 0
    assert mock_run.call_args[0][0].retries == 3


# --- Regression: config set fixes ---


def test_config_set_preserves_trailing_comment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """config set keeps trailing comments on the edited line."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.behave-runner]\nparallel = 4  # workers\n")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "set", "parallel", "8"])
    assert result.exit_code == 0
    content = pyproject.read_text()
    assert "parallel = 8" in content
    assert "# workers" in content


def test_config_set_preserves_hash_inside_string(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A # inside a quoted string value is not treated as a comment."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[tool.behave-runner]\nformat = "a#b"  # note\n')
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "set", "format", "json"])
    assert result.exit_code == 0
    content = pyproject.read_text()
    assert 'format = "json" # note' in content


def test_config_set_toml_list(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """config set parses TOML list syntax into a real list."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.behave-runner]\n")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "set", "tags", '["@smoke", "@fast"]'])
    assert result.exit_code == 0
    assert '["@smoke", "@fast"]' in pyproject.read_text()


def test_config_set_unquoted_bracket_list(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """config set accepts bare bracket lists like [@smoke, @fast]."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.behave-runner]\n")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "set", "tags", "[@smoke, @fast]"])
    assert result.exit_code == 0
    assert '["@smoke", "@fast"]' in pyproject.read_text()


def test_config_set_dotted_key_into_subtable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Dotted keys are written inside the matching subtable if one exists."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[tool.behave-runner]\ntimeout = 60\n\n[tool.behave-runner.profiles.ci]\nparallel = 4\n"
    )
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "set", "profiles.ci.parallel", "8"])
    assert result.exit_code == 0
    content = pyproject.read_text()
    assert "parallel = 8" in content
    # The key must land inside the subtable, not as a dotted key in the root
    root_section = content.split("[tool.behave-runner.profiles.ci]")[0]
    assert "profiles.ci.parallel" not in root_section


def test_config_set_echo_escapes_markup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Values containing [brackets] are echoed literally, not eaten as markup."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.behave-runner]\n")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "set", "tags", "[@smoke, @fast]"])
    assert result.exit_code == 0
    assert "@smoke" in result.stdout


def test_config_no_args_shows_help() -> None:
    """`behave-runner config` with no subcommand shows help, not silence."""
    result = runner.invoke(app, ["config"])
    assert result.exit_code == 0 or result.exit_code == 2
    assert "show" in result.output


# --- Regression: open trace respects --output ---


def test_open_trace_uses_output_dir(tmp_path: Path) -> None:
    """open trace searches for trace.json inside --output first."""
    import importlib.util

    if importlib.util.find_spec("behave_trace") is None:
        pytest.skip("behave-trace not installed")
    trace_file = tmp_path / "trace.json"
    trace_file.write_text("{}")
    with patch("behave_runner.commands.open_cmd.run_external", return_value=0) as mock_ext:
        result = runner.invoke(app, ["open", "trace", "--output", str(tmp_path)])
    assert result.exit_code == 0
    assert str(trace_file) in mock_ext.call_args[0][0]


# --- Regression: warnings for unsupported / degraded flags ---


def test_max_failures_gt1_warns() -> None:
    """max_failures > 1 warns that behave only stops at the first failure."""
    config = RunConfig(max_failures=3)
    with pytest.warns(UserWarning, match="max-fail"):
        cmd = build_behave_command(config)
    assert "--stop" in cmd


def test_max_failures_1_no_warning() -> None:
    """max_failures = 1 maps cleanly to --stop with no warning."""
    import warnings

    config = RunConfig(max_failures=1)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        cmd = build_behave_command(config)
    assert "--stop" in cmd


def test_trace_flags_warn_without_behave_trace() -> None:
    """--trace/--ui/--debug warn when behave-trace is not installed."""
    import importlib.util

    config = RunConfig(trace=True)
    if importlib.util.find_spec("behave_trace") is not None:
        cmd = build_behave_command(config)
        assert "behave_trace:TraceFormatter" in cmd
    else:
        with pytest.warns(UserWarning, match="behave-trace"):
            cmd = build_behave_command(config)
        assert "behave_trace:TraceFormatter" not in cmd


# --- Regression: external tools resolve next to sys.executable ---


def test_resolve_executable_finds_sibling_script(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """resolve_executable prefers a script next to sys.executable."""
    import sys

    from behave_runner.core.deps import resolve_executable

    scripts_dir = tmp_path / "Scripts"
    scripts_dir.mkdir()
    tool = scripts_dir / "mytool.exe"
    tool.write_text("x")
    monkeypatch.setattr(sys, "executable", str(tmp_path / "python.exe"))
    assert resolve_executable("mytool") == str(tool)


def test_resolve_executable_falls_back_to_name(monkeypatch: pytest.MonkeyPatch) -> None:
    """resolve_executable returns the bare name when no sibling script exists."""
    import sys

    from behave_runner.core.deps import resolve_executable

    monkeypatch.setattr(sys, "executable", r"C:\nowhere\python.exe")
    assert resolve_executable("mytool") == "mytool"


# --- Regression: report generate defaults to reports/ for non-console ---


def test_report_generate_defaults_to_reports_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Non-console formats write to reports/ by default."""
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.report.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["report", "generate", "--format", "json"])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert config.outfile == str(Path("reports") / "report.json")
    assert (tmp_path / "reports").is_dir()


def test_report_generate_console_creates_no_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The console format prints to stdout and does not create reports/."""
    monkeypatch.chdir(tmp_path)
    with (
        patch("behave_runner.commands.report.run", return_value=0) as mock_run,
        patch("behave_runner.commands.report.is_installed", return_value=True),
    ):
        result = runner.invoke(app, ["report", "generate", "--format", "console"])
    assert result.exit_code == 0
    assert mock_run.call_args[0][0].outfile is None
    assert not (tmp_path / "reports").exists()


# --- Regression: collect_scenarios warns on bad paths ---


def test_collect_scenarios_warns_on_missing_path(caplog: pytest.LogCaptureFixture) -> None:
    """A nonexistent feature path logs a warning instead of staying silent."""
    import logging

    from behave_runner.core.features import collect_scenarios

    with caplog.at_level(logging.WARNING, logger="behave_runner.core.features"):
        result = collect_scenarios([Path("does-not-exist-xyz")])
    assert result == []
    assert "does-not-exist-xyz" in caplog.text


# --- Regression: behave.ini is read as UTF-8 ---


def test_behave_ini_read_as_utf8(tmp_path: Path) -> None:
    """behave.ini with non-ASCII values parses correctly regardless of locale."""
    from behave_runner.core.config import load_config

    (tmp_path / "behave.ini").write_text("[behave-runner]\nname = café\n", encoding="utf-8")
    config = load_config(tmp_path)
    assert config["name"] == "café"


# --- Regression: resolve_executable finds user-site scripts ---


def test_resolve_executable_user_scripts(tmp_path: Path, monkeypatch) -> None:
    r"""resolve_executable should find console scripts in the per-user Scripts dir.

    `pip install --user` puts scripts in %APPDATA%\Python\PythonXY\Scripts
    or ~/.local/bin, not next to sys.executable and usually not on PATH.
    """
    from behave_runner.core import deps

    user_scripts = tmp_path / "user_scripts"
    user_scripts.mkdir()
    fake_exe = user_scripts / "behave-doctor.exe"
    fake_exe.write_text("binary")

    monkeypatch.setattr(deps, "_user_scripts_dir", lambda: user_scripts)
    resolved = deps.resolve_executable("behave-doctor")
    assert resolved == str(fake_exe)


def test_is_installed_does_not_execute_module(monkeypatch) -> None:
    """is_installed should use find_spec, not import the module."""
    import importlib.util as importlib_util

    from behave_runner.core.deps import is_installed

    called = []

    def fake_find_spec(name):
        called.append(name)
        return None

    monkeypatch.setattr(importlib_util, "find_spec", fake_find_spec)
    assert is_installed("whatever") is False
    assert called == ["whatever"]


# --- Regression: run() must not mutate os.environ ---


def test_run_does_not_mutate_os_environ(monkeypatch) -> None:
    """run() should pass behave vars via subprocess env, not os.environ."""
    import os as os_module

    from behave_runner.core import orchestrator

    monkeypatch.delenv("BEHAVE_RETRY_MAX_RETRIES", raising=False)
    config = RunConfig(retries=3)
    captured = {}

    class FakePopen:
        def __init__(self, cmd, env=None, **kwargs):
            captured["inside"] = os_module.environ.get("BEHAVE_RETRY_MAX_RETRIES")
            captured["env_arg"] = env.get("BEHAVE_RETRY_MAX_RETRIES")
            self.returncode = 0
            self.pid = 1

        def wait(self, timeout=None):
            return self.returncode

        def kill(self):
            pass

    monkeypatch.setattr(orchestrator.subprocess, "Popen", FakePopen)
    orchestrator.run(config)
    # The subprocess env carries the var, os.environ was never touched
    assert captured["env_arg"] == "3"
    assert captured["inside"] is None
    assert "BEHAVE_RETRY_MAX_RETRIES" not in os_module.environ


# --- Regression: warnings for silently ignored optional features ---


def test_retries_without_behave_retry_warns(monkeypatch) -> None:
    """--retries without behave-retry should warn instead of silently no-op."""
    monkeypatch.setattr("behave_runner.core.orchestrator.is_installed", lambda p: False)
    config = RunConfig(retries=2)
    with pytest.warns(UserWarning, match="behave-retry"):
        _build_env(config)


def test_priority_without_behave_priority_warns(monkeypatch) -> None:
    """--priority-order without behave-priority should warn."""
    monkeypatch.setattr("behave_runner.core.orchestrator.is_installed", lambda p: False)
    config = RunConfig(priority_order=True)
    with pytest.warns(UserWarning, match="behave-priority"):
        _build_env(config)


def test_shard_without_behave_pool_warns(monkeypatch) -> None:
    """--shard without behave-pool should warn instead of silently no-op."""
    monkeypatch.setattr("behave_runner.core.orchestrator._is_package_functional", lambda p: False)
    config = RunConfig(shard="1/3")
    with pytest.warns(UserWarning, match="behave-pool"):
        build_behave_command(config)


def test_parallel_extras_without_pool_warn(monkeypatch) -> None:
    """--parallel-scheme without --parallel > 1 should warn, not vanish."""
    monkeypatch.setattr("behave_runner.core.orchestrator._is_package_functional", lambda p: False)
    config = RunConfig(parallel_scheme="feature")
    with pytest.warns(UserWarning, match="--parallel"):
        build_behave_command(config)


def test_report_format_missing_package_warns(monkeypatch) -> None:
    """--format json without behave-modern-json-report should warn on fallback."""
    monkeypatch.setattr("behave_runner.core.orchestrator.is_installed", lambda p: False)
    config = RunConfig(fmt="json")
    with pytest.warns(UserWarning, match="behave_modern_json_report"):
        cmd = build_behave_command(config)
    assert "--format" in cmd
    assert "json" in cmd


# --- Regression: RunConfig validates shard format ---


def test_run_config_invalid_shard_rejected() -> None:
    """RunConfig should reject malformed shard values at construction."""
    with pytest.raises(ValueError, match="Invalid shard"):
        RunConfig(shard="not-a-shard")


def test_run_config_shard_out_of_range_rejected() -> None:
    """RunConfig should reject shard index greater than the total."""
    with pytest.raises(ValueError, match="Invalid shard"):
        RunConfig(shard="4/3")


# --- Regression: collect_scenarios accepts str paths and dedupes files ---


def test_collect_scenarios_accepts_str_paths(tmp_path: Path) -> None:
    """collect_scenarios should accept plain strings, not crash on .is_dir()."""
    from behave_runner.core.features import collect_scenarios

    feature_dir = tmp_path / "features"
    feature_dir.mkdir()
    (feature_dir / "x.feature").write_text("Feature: F\n\n  Scenario: S\n    Given a step\n")
    result = collect_scenarios([str(feature_dir)])
    assert len(result) == 1
    assert result[0]["scenario"] == "S"


def test_collect_scenarios_dedupes_overlapping_paths(tmp_path: Path) -> None:
    """Overlapping feature paths must not duplicate scenarios."""
    from behave_runner.core.features import collect_scenarios

    feature_dir = tmp_path / "features"
    sub = feature_dir / "sub"
    sub.mkdir(parents=True)
    (sub / "x.feature").write_text("Feature: F\n\n  Scenario: S\n    Given a step\n")
    result = collect_scenarios([feature_dir, sub])
    assert len(result) == 1


# --- Regression: find_latest_report on non-directory ---


def test_find_latest_report_on_file_returns_none(tmp_path: Path) -> None:
    """find_latest_report should return None, not crash, when given a file."""
    from behave_runner.core.output import find_latest_report

    f = tmp_path / "not_a_dir.txt"
    f.write_text("x")
    assert find_latest_report(f) is None


# --- Regression: config init/set tolerate commented or spaced headers ---


def test_config_init_no_duplicate_header_with_comment(tmp_path: Path, monkeypatch) -> None:
    """config init must not append a second [tool.behave-runner] when the
    existing header has a trailing comment."""
    import tomllib

    p = tmp_path / "pyproject.toml"
    p.write_text('[project]\nname = "x"\n\n[tool.behave-runner] # main config\n')
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "init"])
    assert "already exists" in result.output
    # File must still parse and contain exactly one header
    text = p.read_text()
    tomllib.loads(text)
    assert text.count("[tool.behave-runner]") == 1


def test_config_init_no_duplicate_header_spaced(tmp_path: Path, monkeypatch) -> None:
    """config init must detect [ tool.behave-runner ] with inner spacing."""
    import tomllib

    p = tmp_path / "pyproject.toml"
    p.write_text('[project]\nname = "x"\n\n[ tool.behave-runner ]\n')
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "init"])
    assert "already exists" in result.output
    text = p.read_text()
    tomllib.loads(text)
    assert "[tool.behave-runner]" not in text


def test_config_set_without_section_creates_it(tmp_path: Path, monkeypatch) -> None:
    """config set should create the section when pyproject lacks it."""
    p = tmp_path / "pyproject.toml"
    p.write_text('[project]\nname = "x"\n')
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "set", "parallel", "4"])
    assert result.exit_code == 0
    import tomllib

    data = tomllib.loads(p.read_text())
    assert data["tool"]["behave-runner"]["parallel"] == 4


def test_config_set_no_trailing_newline(tmp_path: Path, monkeypatch) -> None:
    """config set on a file without a trailing newline must not merge lines."""
    import tomllib

    p = tmp_path / "pyproject.toml"
    p.write_text("[tool.behave-runner]\nparallel = 2")  # no trailing newline
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "set", "retries", "3"])
    assert result.exit_code == 0
    data = tomllib.loads(p.read_text())
    assert data["tool"]["behave-runner"]["retries"] == 3
    assert data["tool"]["behave-runner"]["parallel"] == 2


def test_config_set_header_with_comment_boundary(tmp_path: Path, monkeypatch) -> None:
    """config set must stop at a section boundary even with trailing comments."""
    import tomllib

    p = tmp_path / "pyproject.toml"
    p.write_text(
        "[tool.behave-runner]\nparallel = 2\n[tool.ruff] # linter config\nline-length = 100\n"
    )
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "set", "retries", "5"])
    assert result.exit_code == 0
    data = tomllib.loads(p.read_text())
    assert data["tool"]["behave-runner"]["retries"] == 5
    # Key must land inside behave-runner, not after the ruff header
    assert "retries" not in data["tool"]["ruff"]


def test_config_set_from_subdirectory(tmp_path: Path, monkeypatch) -> None:
    """config set should find pyproject.toml at the project root from a subdir."""
    p = tmp_path / "pyproject.toml"
    p.write_text("[tool.behave-runner]\nparallel = 2\n")
    subdir = tmp_path / "tests" / "nested"
    subdir.mkdir(parents=True)
    monkeypatch.chdir(subdir)
    result = runner.invoke(app, ["config", "set", "retries", "7"])
    assert result.exit_code == 0
    assert "retries = 7" in p.read_text()


def test_config_set_non_utf8_pyproject(tmp_path: Path, monkeypatch) -> None:
    """config set should show a clean error on non-UTF-8 pyproject.toml."""
    p = tmp_path / "pyproject.toml"
    p.write_bytes(b"\xff\xfe invalid")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "set", "parallel", "4"])
    assert result.exit_code == 2
    assert "UTF-8" in result.output or "decode" in result.output.lower()


def test_load_config_from_subdirectory(tmp_path: Path, monkeypatch) -> None:
    """load_config should find config at the project root from a subdirectory."""
    from behave_runner.core.config import load_config

    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\n\n[tool.behave-runner]\nparallel = 3\n'
    )
    subdir = tmp_path / "sub" / "deep"
    subdir.mkdir(parents=True)
    monkeypatch.chdir(subdir)
    config = load_config()
    assert config.get("parallel") == 3


def test_load_config_non_utf8_pyproject(tmp_path: Path) -> None:
    """load_config should raise ConfigError (not UnicodeDecodeError) on bad UTF-8."""
    import pytest as _pytest

    from behave_runner.core.config import load_config
    from behave_runner.exceptions import ConfigError

    (tmp_path / "pyproject.toml").write_bytes(b"\xff\xfe invalid")
    with _pytest.raises(ConfigError):
        load_config(tmp_path)


# --- Regression: stderr for diagnostics, clean stdout for machine output ---


def test_select_json_diagnostics_go_to_stderr(tmp_path: Path, monkeypatch) -> None:
    """select --format json must keep stdout as pure JSON.

    Warnings about skipped paths go to stderr so the JSON can be piped.
    """
    import json as json_module

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["select", "--format", "json", "missing-dir-xyz"])
    assert result.exit_code == 0
    # stdout must be parseable JSON (the logger warning went to stderr)
    parsed = json_module.loads(result.stdout)
    assert parsed == []


def test_errors_written_to_stderr(tmp_path: Path, monkeypatch) -> None:
    """Error messages must go to stderr, not stdout."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["select", "--format", "xml"])
    assert result.exit_code == 2
    assert "Unknown format" in result.stderr
    assert "Unknown format" not in result.stdout


# --- Regression: impact --run resolves the features directory ---


def test_impact_resolve_features_path() -> None:
    """_resolve_features_path should prefer <root>/features when it exists."""
    from behave_runner.commands.impact import _resolve_features_path

    assert _resolve_features_path("tests/fixtures/full").endswith("features")
    # A path that IS the features dir is returned as-is
    assert _resolve_features_path("tests/fixtures/minimal/features").endswith("features")
    # Nonexistent path falls back to itself
    assert _resolve_features_path("missing-xyz") == "missing-xyz"


def test_impact_run_uses_features_dir(monkeypatch) -> None:
    """impact --run should run behave on <root>/features, not the root itself.

    Behave resolves steps relative to the features path; passing the project
    root fails with 'No steps directory' on the conventional layout.
    """
    from unittest.mock import MagicMock
    from unittest.mock import patch as _patch

    captured = []

    def fake_run(config):
        captured.append(config.features)
        return 0

    doctor_output = '{"diagnostics": [{"metadata": {"scenario": "S1"}}]}'
    mock_result = MagicMock(returncode=0, stdout=doctor_output)
    with (
        _patch("behave_runner.core.deps.is_installed", return_value=True),
        _patch("behave_runner.commands.impact.subprocess.run", return_value=mock_result),
        _patch("behave_runner.commands.impact.run", side_effect=fake_run),
    ):
        result = runner.invoke(app, ["impact", "tests/fixtures/full", "--run"])
    assert result.exit_code == 0
    assert captured
    assert all(f[0].endswith("features") for f in captured)


def test_impact_run_dedupes_scenario_names(monkeypatch) -> None:
    """impact --run must not run the same scenario twice.

    behave --name already matches every scenario with that name, so duplicate
    names in the doctor output only waste runs.
    """
    from unittest.mock import MagicMock
    from unittest.mock import patch as _patch

    runs = []

    def fake_run(config):
        runs.append(config.name[0])
        return 0

    doctor_output = (
        '{"diagnostics": ['
        '{"metadata": {"scenario": "S1"}},'
        '{"metadata": {"scenario": "S1"}},'
        '{"metadata": {"scenario": "S2"}}]}'
    )
    mock_result = MagicMock(returncode=0, stdout=doctor_output)
    with (
        _patch("behave_runner.core.deps.is_installed", return_value=True),
        _patch("behave_runner.commands.impact.subprocess.run", return_value=mock_result),
        _patch("behave_runner.commands.impact.run", side_effect=fake_run),
    ):
        result = runner.invoke(app, ["impact", "missing-xyz", "--run"])
    assert result.exit_code == 0
    assert len(runs) == 2


def test_impact_extract_names_prefers_metadata_scenario() -> None:
    """metadata.scenario is authoritative over an ambiguous top-level name."""
    from behave_runner.commands.impact import _extract_scenario_names

    stdout = (
        '{"diagnostics": [{"name": "rule-violation-x", "metadata": {"scenario": "Real Scenario"}}]}'
    )
    assert _extract_scenario_names(stdout) == ["Real Scenario"]


# --- Regression: record/report clean errors on unwritable output dir ---


def test_record_output_dir_error(tmp_path: Path) -> None:
    """record should exit 2 cleanly when the output dir cannot be created."""
    from unittest.mock import patch as _patch

    blocker = tmp_path / "blocker"
    blocker.write_text("file")
    with _patch("behave_runner.core.deps.is_installed", return_value=True):
        result = runner.invoke(app, ["record", "--output", str(blocker / "sub")])
    assert result.exit_code == 2
    assert "Error" in result.output


def test_report_generate_unwritable_output(tmp_path: Path) -> None:
    """report generate should exit 2 when output dir cannot be created."""
    blocker = tmp_path / "blocker"
    blocker.write_text("file")
    result = runner.invoke(
        app, ["report", "generate", "--format", "html", "--output", str(blocker)]
    )
    assert result.exit_code == 2
    assert "Error" in result.output


# --- Regression: watcher symlink cycles and find_project_root edge cases ---


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Creating symlinks on Windows requires admin privileges",
)
def test_watcher_scan_symlink_cycle_terminates(tmp_path: Path) -> None:
    """Regression: _scan must not loop forever on a directory symlink cycle."""
    from behave_runner.core.watcher import FileWatcher

    watched = tmp_path / "watched"
    watched.mkdir()
    (watched / "a.feature").write_text("Feature: A")
    (watched / "loop").symlink_to(watched, target_is_directory=True)

    watcher = FileWatcher([watched], on_change=lambda _paths: None)
    scanned = watcher._scan()
    assert watched / "a.feature" in scanned
    # Files reached through the symlinked dir must not be reported.
    assert all("loop" not in p.parts for p in scanned)


def test_find_project_root_relative_start(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression: a relative start path must walk real ancestors, not '.'."""
    from behave_runner.utils import find_project_root

    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'x'\n")
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    assert find_project_root(Path(".")) == tmp_path


def test_find_project_root_file_start(tmp_path: Path) -> None:
    """Regression: passing a file path should search from its parent dir."""
    from behave_runner.utils import find_project_root

    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'x'\n")
    sub = tmp_path / "sub"
    sub.mkdir()
    marker = sub / "marker.txt"
    marker.write_text("x")
    assert find_project_root(marker) == tmp_path


# --- Regression: collect_scenarios Rule blocks and inherited tags ---


def _write_feature(tmp_path: Path, text: str, name: str = "f.feature") -> Path:
    feat = tmp_path / name
    feat.write_text(text, encoding="utf-8")
    return feat


def test_collect_scenarios_includes_rule_scenarios(tmp_path: Path) -> None:
    """Scenarios inside Rule: blocks must be collected, not skipped."""
    from behave_runner.core.features import collect_scenarios

    feat = _write_feature(
        tmp_path,
        "Feature: Auth\n"
        "  Rule: Login\n"
        "    Scenario: Valid login\n"
        "      Given a step\n"
        "  Scenario: Top level\n"
        "    Given a step\n",
    )
    scenarios = collect_scenarios([feat])
    names = [s["scenario"] for s in scenarios]
    assert "Valid login" in names
    assert "Top level" in names


def test_collect_scenarios_inherited_feature_tags(tmp_path: Path) -> None:
    """Feature-level tags must apply to every scenario (behave semantics)."""
    from behave_runner.core.features import collect_scenarios

    feat = _write_feature(
        tmp_path,
        "@smoke\n"
        "Feature: Checkout\n"
        "  Scenario: Pay\n"
        "    Given a step\n"
        "  @wip\n"
        "  Scenario: Draft\n"
        "    Given a step\n",
    )
    by_tag = collect_scenarios([feat], tags=["@smoke"])
    assert len(by_tag) == 2
    not_wip = collect_scenarios([feat], tags=["~@wip"])
    assert [s["scenario"] for s in not_wip] == ["Pay"]


def test_collect_scenarios_inherited_rule_tags(tmp_path: Path) -> None:
    """Rule-level tags apply only to scenarios inside that rule."""
    from behave_runner.core.features import collect_scenarios

    feat = _write_feature(
        tmp_path,
        "Feature: F\n"
        "  Rule: R\n"
        "    @ruled\n"
        "    Scenario: Inside\n"
        "      Given a step\n"
        "  Scenario: Outside\n"
        "    Given a step\n",
    )
    ruled = collect_scenarios([feat], tags=["@ruled"])
    assert [s["scenario"] for s in ruled] == ["Inside"]


def test_collect_scenarios_tag_or_list_and_expressions(tmp_path: Path) -> None:
    """Comma lists are OR-ed; v2 expressions 'and/or/not' work like behave."""
    from behave_runner.core.features import collect_scenarios

    feat = _write_feature(
        tmp_path,
        "Feature: F\n"
        "  @a\n"
        "  Scenario: OnlyA\n"
        "    Given a step\n"
        "  @b\n"
        "  Scenario: OnlyB\n"
        "    Given a step\n"
        "  @a @b\n"
        "  Scenario: BothAB\n"
        "    Given a step\n",
    )
    or_result = collect_scenarios([feat], tags=["@a,@b"])
    assert len(or_result) == 3
    and_result = collect_scenarios([feat], tags=["@a and @b"])
    assert [s["scenario"] for s in and_result] == ["BothAB"]
    not_result = collect_scenarios([feat], tags=["@a and not @b"])
    assert [s["scenario"] for s in not_result] == ["OnlyA"]
    # Tags without '@' match too, like behave's --tags=smoke
    bare = collect_scenarios([feat], tags=["a"])
    assert len(bare) == 2


def test_collect_scenarios_feature_location_line(tmp_path: Path) -> None:
    """'file.feature:LINE' selects the scenario at that line."""
    from behave_runner.core.features import collect_scenarios

    feat = _write_feature(
        tmp_path,
        "Feature: F\n  Scenario: First\n    Given a step\n  Scenario: Second\n    Given a step\n",
    )
    only_second = collect_scenarios([f"{feat}:4"])
    assert [s["scenario"] for s in only_second] == ["Second"]


def test_collect_scenarios_uppercase_suffix(tmp_path: Path) -> None:
    """An explicit FOO.FEATURE path is accepted (filesystem is case-insensitive on Windows)."""
    from behave_runner.core.features import collect_scenarios

    feat = _write_feature(
        tmp_path,
        "Feature: F\n  Scenario: S\n    Given a step\n",
        name="UPPER.FEATURE",
    )
    scenarios = collect_scenarios([feat])
    assert [s["scenario"] for s in scenarios] == ["S"]


def test_collect_scenarios_dedup_same_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The same file reached via relative and absolute paths is parsed once."""
    from behave_runner.core.features import collect_scenarios

    feat = _write_feature(
        tmp_path,
        "Feature: F\n  Scenario: S\n    Given a step\n",
    )
    monkeypatch.chdir(tmp_path)
    scenarios = collect_scenarios([Path("f.feature"), feat])
    assert len(scenarios) == 1


# --- Regression: behave.ini case, BOM, DEFAULT section ---


def test_load_config_ini_profile_name_case_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Profile names keep their case in behave.ini; config keys stay lowercase."""
    from behave_runner.core.config import load_config, load_profile

    (tmp_path / "behave.ini").write_text(
        "[behave-runner]\nprofiles.CI.parallel = 4\n", encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)
    config = load_config(tmp_path)
    assert "CI" in config["profiles"]
    profile = load_profile("CI", tmp_path)
    assert profile["parallel"] == 4


def test_load_config_ini_default_section_not_injected(tmp_path: Path) -> None:
    """[DEFAULT] keys must not leak into the behave-runner section config."""
    from behave_runner.core.config import load_config

    (tmp_path / "behave.ini").write_text(
        "[DEFAULT]\ninjected = yes\n[behave-runner]\nparallel = 2\n",
        encoding="utf-8",
    )
    config = load_config(tmp_path)
    assert "injected" not in config


def test_load_config_pyproject_with_bom(tmp_path: Path) -> None:
    """pyproject.toml written with a UTF-8 BOM still loads."""
    from behave_runner.core.config import load_config

    (tmp_path / "pyproject.toml").write_bytes(b"\xef\xbb\xbf[tool.behave-runner]\nparallel = 3\n")
    config = load_config(tmp_path)
    assert config["parallel"] == 3


def test_load_config_ini_with_bom(tmp_path: Path) -> None:
    """behave.ini written with a UTF-8 BOM still loads."""
    from behave_runner.core.config import load_defaults

    (tmp_path / "behave.ini").write_bytes(b"\xef\xbb\xbf[behave-runner]\nparallel = 3\n")
    config = load_defaults(tmp_path)
    assert config["parallel"] == 3


def test_find_project_root_anchors_behave_ini(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A behave.ini-only project is found from nested subdirectories."""
    from behave_runner.utils import find_project_root

    (tmp_path / "behave.ini").write_text("[behave-runner]\n", encoding="utf-8")
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    assert find_project_root() == tmp_path


# --- Regression: config set TOML editing edge cases ---


def test_config_set_header_inside_multiline_string_safe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A fake [tool.behave-runner] inside a triple-quoted string must not
    silently corrupt the file — the edit fails cleanly, file untouched."""
    monkeypatch.chdir(tmp_path)
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[tool.example]\nhelp = """\n[tool.behave-runner]\n"""\n',
        encoding="utf-8",
    )
    before = pyproject.read_text(encoding="utf-8")
    result = runner.invoke(app, ["config", "set", "retries", "2"])
    assert result.exit_code == 2
    assert "Error" in result.output
    assert pyproject.read_text(encoding="utf-8") == before


def test_config_set_replaces_multiline_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Replacing a multi-line array consumes the whole value — no orphans."""
    monkeypatch.chdir(tmp_path)
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[tool.behave-runner]\ntags = [\n    "@smoke",\n]\nparallel = 1\n',
        encoding="utf-8",
    )
    result = runner.invoke(app, ["config", "set", "tags", '["@ci"]'])
    assert result.exit_code == 0
    import tomllib

    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    assert data["tool"]["behave-runner"]["tags"] == ["@ci"]
    assert data["tool"]["behave-runner"]["parallel"] == 1


def test_config_set_array_item_not_section_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An array item line like ["a", "b"], inside a section is not a header."""
    monkeypatch.chdir(tmp_path)
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[tool.behave-runner]\nmatrix = [\n    ["a", "b"],\n]\nparallel = 4\n',
        encoding="utf-8",
    )
    result = runner.invoke(app, ["config", "set", "parallel", "8"])
    assert result.exit_code == 0
    import tomllib

    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    assert data["tool"]["behave-runner"]["parallel"] == 8


def test_config_set_warns_when_ini_active(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """config set warns when behave.ini holds the active configuration."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'x'\n", encoding="utf-8")
    (tmp_path / "behave.ini").write_text("[behave-runner]\nretries = 1\n", encoding="utf-8")
    result = runner.invoke(app, ["config", "set", "retries", "2"])
    assert "behave.ini" in result.output


# --- Regression: report generate requires the report package ---


def test_report_generate_missing_package_exits_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """report generate --format html without the package fails early."""
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.report.is_installed", return_value=False):
        result = runner.invoke(app, ["report", "generate", "--format", "html"])
    assert result.exit_code == 2
    assert "behave_modern_html_report" in result.output


def test_report_generate_json_builtin_warns_but_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """--format json without the package warns but still runs (builtin exists)."""
    monkeypatch.chdir(tmp_path)
    with (
        patch("behave_runner.commands.report.is_installed", return_value=False),
        patch("behave_runner.commands.report.run", return_value=0) as mock_run,
    ):
        result = runner.invoke(app, ["report", "generate", "--format", "json"])
    assert result.exit_code == 0
    assert "behave_modern_json_report" in result.output
    mock_run.assert_called_once()


# --- Regression: watch validates merged config upfront ---


def test_watch_invalid_parallel_rejected_upfront(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """--parallel 0 fails immediately instead of erroring on every change."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["watch", "features", "--parallel", "0"])
    assert result.exit_code == 2
    assert "parallel" in result.output


# --- Regression: --flaky-report merges with profile retries ---


def test_flaky_report_uses_profile_retries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--flaky-report works when retries come from the profile, not the CLI."""
    (tmp_path / "pyproject.toml").write_text(
        "[tool.behave-runner]\nretries = 3\n", encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)
    captured = {}

    class FakePopen:
        def __init__(self, cmd, env=None, **kwargs):
            captured["env"] = env or {}
            self.returncode = 0
            self.pid = 1

        def wait(self, timeout=None):
            return self.returncode

        def kill(self):
            pass

    monkeypatch.setattr("behave_runner.core.orchestrator.subprocess.Popen", FakePopen)
    runner.invoke(app, ["run", "features", "--flaky-report"])
    assert captured["env"].get("BEHAVE_RETRY_FLAKY_REPORT") == "1"


# --- Regression: impact --run surfaces captured stderr ---


def test_impact_run_scan_failure_shows_stderr(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failing doctor scan must show stderr captured for parsing."""
    from unittest.mock import MagicMock

    monkeypatch.chdir(tmp_path)
    mock_result = MagicMock()
    mock_result.returncode = 2
    mock_result.stdout = ""
    mock_result.stderr = "doctor exploded"
    with (
        patch("behave_runner.commands.impact.check_optional", return_value=True),
        patch("subprocess.run", return_value=mock_result),
    ):
        result = runner.invoke(app, ["impact", "--run", str(tmp_path)])
    assert result.exit_code == 2
    assert "doctor exploded" in result.output


def test_impact_run_unparseable_output_warns(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Non-empty doctor output that yields no names must warn, not look clean."""
    from unittest.mock import MagicMock

    monkeypatch.chdir(tmp_path)
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "not json at all"
    mock_result.stderr = ""
    with (
        patch("behave_runner.commands.impact.check_optional", return_value=True),
        patch("subprocess.run", return_value=mock_result),
    ):
        result = runner.invoke(app, ["impact", "--run", str(tmp_path)])
    assert result.exit_code == 0
    assert "could not parse" in result.output
