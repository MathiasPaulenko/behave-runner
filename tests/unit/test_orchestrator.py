"""Tests for behave_runner.core.orchestrator."""

from __future__ import annotations

import sys

import pytest

from behave_runner.core.orchestrator import RunConfig, build_behave_command
from behave_runner.core.orchestrator import run as run_behave


def test_empty_config() -> None:
    config = RunConfig()
    cmd = build_behave_command(config)
    assert cmd[:3] == [sys.executable, "-m", "behave"]
    assert cmd[3:] == ["features"]


def test_custom_features() -> None:
    config = RunConfig(features=["tests/fixtures/minimal/features"])
    cmd = build_behave_command(config)
    assert cmd[:3] == [sys.executable, "-m", "behave"]
    assert cmd[3:] == ["tests/fixtures/minimal/features"]


def test_tags() -> None:
    config = RunConfig(tags=["@smoke", "~@slow"])
    cmd = build_behave_command(config)
    assert "--tags" in cmd
    assert "@smoke" in cmd
    assert "~@slow" in cmd


def test_dry_run() -> None:
    config = RunConfig(dry_run=True)
    assert "--dry-run" in build_behave_command(config)


def test_stop_on_failure() -> None:
    config = RunConfig(stop_on_failure=True)
    assert "--stop" in build_behave_command(config)


def test_max_failures() -> None:
    """max_failures is passed as env var, not as invalid CLI flag."""
    from behave_runner.core.orchestrator import _build_env

    config = RunConfig(max_failures=3)
    cmd = build_behave_command(config)
    assert "--max-failures" not in cmd
    env = _build_env(config)
    assert env["BEHAVE_MAX_FAILURES"] == "3"


def test_timeout() -> None:
    """timeout is passed as env var, not as invalid CLI flag."""
    from behave_runner.core.orchestrator import _build_env

    config = RunConfig(timeout=30)
    cmd = build_behave_command(config)
    assert "--timeout" not in cmd
    env = _build_env(config)
    assert env["BEHAVE_TIMEOUT"] == "30"


def test_format_and_outfile() -> None:
    config = RunConfig(fmt="json", outfile="reports/output.json")
    cmd = build_behave_command(config)
    assert "--format" in cmd
    assert "behave_modern_json_report:ModernJSONFormatter" in cmd
    assert "--outfile" in cmd
    assert "reports/output.json" in cmd


def test_format_builtin_passthrough() -> None:
    """Non-report formats (plain, json, etc.) are passed through to behave."""
    config = RunConfig(fmt="plain")
    cmd = build_behave_command(config)
    assert "--format" in cmd
    assert "plain" in cmd


def test_name() -> None:
    config = RunConfig(name=["Test login"])
    cmd = build_behave_command(config)
    assert "--name" in cmd
    assert "Test login" in cmd


def test_frozen() -> None:
    config = RunConfig()
    try:
        config.dry_run = True  # type: ignore[misc]
        raise AssertionError("Should have raised FrozenInstanceError")
    except AttributeError:
        pass


def test_run_success() -> None:
    config = RunConfig(features=["tests/fixtures/minimal/features"])
    assert run_behave(config) == 0


def test_run_dry_run() -> None:
    config = RunConfig(
        features=["tests/fixtures/minimal/features"],
        dry_run=True,
    )
    assert run_behave(config) == 0


def test_run_config_rejects_string_parallel() -> None:
    with pytest.raises(ValueError, match="parallel"):
        RunConfig(parallel="4")  # type: ignore[arg-type]


def test_run_config_rejects_bool_as_int() -> None:
    with pytest.raises(ValueError, match="parallel"):
        RunConfig(parallel=True)  # type: ignore[arg-type]


def test_run_config_rejects_negative_timeout() -> None:
    with pytest.raises(ValueError, match="timeout"):
        RunConfig(timeout=-1)


def test_run_config_rejects_string_features() -> None:
    with pytest.raises(ValueError, match="features"):
        RunConfig(features="tests/fixtures")  # type: ignore[arg-type]


def test_run_config_rejects_string_dry_run() -> None:
    with pytest.raises(ValueError, match="dry_run"):
        RunConfig(dry_run="true")  # type: ignore[arg-type]


def test_run_config_rejects_non_string_outfile() -> None:
    with pytest.raises(ValueError, match="outfile"):
        RunConfig(outfile=123)  # type: ignore[arg-type]


def test_no_color_and_verbose() -> None:
    config = RunConfig(no_color=True, verbose=True)
    cmd = build_behave_command(config)
    assert "--no-color" in cmd
    assert "--verbose" in cmd


def test_run_behave_subprocess_handles_not_found(monkeypatch) -> None:
    """Ensure FileNotFoundError for behave is handled gracefully."""
    from behave_runner.core.orchestrator import _run_behave_subprocess

    def raise_not_found(*args, **kwargs):
        raise FileNotFoundError()

    monkeypatch.setattr("behave_runner.core.orchestrator.subprocess.run", raise_not_found)
    assert _run_behave_subprocess(["behave"], {}) == 2


def test_run_config_rejects_empty_strings() -> None:
    with pytest.raises(ValueError, match="outfile"):
        RunConfig(outfile="")
    with pytest.raises(ValueError, match="fmt"):
        RunConfig(fmt="")
    with pytest.raises(ValueError, match="shard"):
        RunConfig(shard="")


def test_run_behave_subprocess_handles_os_error(monkeypatch) -> None:
    """Ensure OSError (e.g. PermissionError) is handled gracefully."""
    from behave_runner.core.orchestrator import _run_behave_subprocess

    def raise_permission(*args, **kwargs):
        raise PermissionError("denied")

    monkeypatch.setattr("behave_runner.core.orchestrator.subprocess.run", raise_permission)
    assert _run_behave_subprocess(["behave"], {}) == 2


def test_parallel_passed_to_behave() -> None:
    """--parallel is passed directly to behave."""
    config = RunConfig(parallel=4)
    cmd = build_behave_command(config)
    assert "--parallel" in cmd
    assert "4" in cmd


def test_trace_formatter_added() -> None:
    """trace=True adds behave_trace:TraceFormatter to the command."""
    config = RunConfig(trace=True)
    cmd = build_behave_command(config)
    assert "behave_trace:TraceFormatter" in cmd


def test_ui_formatter_added() -> None:
    """ui=True adds behave_trace:TraceFormatter to the command."""
    config = RunConfig(ui=True)
    cmd = build_behave_command(config)
    assert "behave_trace:TraceFormatter" in cmd


def test_retries_env_var() -> None:
    """retries is passed as env var."""
    from behave_runner.core.orchestrator import _build_env

    config = RunConfig(retries=3)
    env = _build_env(config)
    assert env["BEHAVE_RETRY_MAX_RETRIES"] == "3"


def test_priority_env_var() -> None:
    """priority_order is passed as env var."""
    from behave_runner.core.orchestrator import _build_env

    config = RunConfig(priority_order=True)
    env = _build_env(config)
    assert env["BEHAVE_PRIORITY_ORDER"] == "1"


def test_fail_fast_env_var() -> None:
    """fail_fast is passed as env var."""
    from behave_runner.core.orchestrator import _build_env

    config = RunConfig(fail_fast=True)
    env = _build_env(config)
    assert env["BEHAVE_PRIORITY_FAIL_FAST"] == "1"


def test_shard_env_var() -> None:
    """shard is passed as env var."""
    from behave_runner.core.orchestrator import _build_env

    config = RunConfig(shard="1/3")
    env = _build_env(config)
    assert env["BEHAVE_POOL_SHARD"] == "1/3"


def test_flaky_report_env_var() -> None:
    """flaky_report is passed as env var."""
    from behave_runner.core.orchestrator import _build_env

    config = RunConfig(flaky_report=True)
    env = _build_env(config)
    assert env["BEHAVE_RETRY_FLAKY_REPORT"] == "1"


def test_report_format_resolved() -> None:
    """Report format names are resolved to their formatter class paths."""
    config = RunConfig(fmt="console")
    cmd = build_behave_command(config)
    assert "behave_modern_console_report:ModernFormatter" in cmd

    config = RunConfig(fmt="md")
    cmd = build_behave_command(config)
    assert "behave_modern_md_report:BehaveMarkdownFormatter" in cmd

    config = RunConfig(fmt="sheets")
    cmd = build_behave_command(config)
    assert "behave_modern_sheets_report:XLSXFormatter" in cmd
