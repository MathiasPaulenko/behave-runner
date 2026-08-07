"""Tests for behave_runner.core.orchestrator."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

import pytest

from behave_runner.core.orchestrator import RunConfig, build_behave_command
from behave_runner.core.orchestrator import run as run_behave


def test_empty_config() -> None:
    config = RunConfig()
    cmd = build_behave_command(config)
    assert cmd == ["behave", "features"]


def test_custom_features() -> None:
    config = RunConfig(features=["tests/fixtures/minimal/features"])
    cmd = build_behave_command(config)
    assert cmd == ["behave", "tests/fixtures/minimal/features"]


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
    assert "json" in cmd
    assert "--outfile" in cmd
    assert "reports/output.json" in cmd


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


def test_try_optional_import_error_falls_back(monkeypatch) -> None:
    """Ensure _try_optional falls back when the optional module is missing."""
    from behave_runner.core.orchestrator import _try_optional

    monkeypatch.setattr("behave_runner.core.orchestrator.check_optional", lambda *a, **k: True)
    called = False

    def fallback() -> int:
        nonlocal called
        called = True
        return 7

    def api_call() -> int:
        raise ModuleNotFoundError("nonexistent_module_12345")

    assert _try_optional("x", "nonexistent_module_12345", "x", "msg", fallback, api_call) == 7
    assert called is True


def test_try_optional_attribute_error_falls_back(monkeypatch) -> None:
    """Ensure _try_optional falls back on API mismatch."""
    from behave_runner.core.orchestrator import _try_optional

    monkeypatch.setattr("behave_runner.core.orchestrator.check_optional", lambda *a, **k: True)
    called = False

    def fallback() -> int:
        nonlocal called
        called = True
        return 7

    def api_call() -> int:
        raise AttributeError("missing")

    assert _try_optional("x", "pkg", "x", "msg", fallback, api_call) == 7
    assert called is True


def test_try_optional_file_not_found(monkeypatch) -> None:
    """Ensure _try_optional reports a helpful error when CLI is missing."""
    from behave_runner.core.orchestrator import _try_optional

    monkeypatch.setattr("behave_runner.core.orchestrator.check_optional", lambda *a, **k: True)

    def api_call() -> int:
        raise FileNotFoundError("behave-pool")

    assert _try_optional("x", "behave_pool", "x", "msg", lambda: 0, api_call) == 2


def test_run_parallel_with_optional_package(monkeypatch) -> None:
    """Ensure _run_parallel uses behave-pool when available."""

    from behave_runner.core.orchestrator import _run_parallel

    fake_pool = MagicMock()
    fake_pool.run_parallel.return_value = 0
    monkeypatch.setitem(sys.modules, "behave_pool", fake_pool)
    monkeypatch.setattr("behave_runner.core.orchestrator.check_optional", lambda *a, **k: True)

    config = RunConfig(features=["tests/fixtures/minimal/features"], parallel=2)
    assert _run_parallel(config) == 0
    fake_pool.run_parallel.assert_called_once()


def test_run_with_retries_with_optional_package(monkeypatch) -> None:
    """Ensure _run_with_retries uses behave-retry when available."""

    from behave_runner.core.orchestrator import _run_with_retries

    fake_retry = MagicMock()
    fake_retry.run_with_retries.return_value = 0
    monkeypatch.setitem(sys.modules, "behave_retry", fake_retry)
    monkeypatch.setattr("behave_runner.core.orchestrator.check_optional", lambda *a, **k: True)

    config = RunConfig(features=["tests/fixtures/minimal/features"], retries=2)
    assert _run_with_retries(config) == 0
    fake_retry.run_with_retries.assert_called_once()


def test_run_with_priority_with_optional_package(monkeypatch) -> None:
    """Ensure _run_with_priority uses behave-priority when available."""

    from behave_runner.core.orchestrator import _run_with_priority

    fake_priority = MagicMock()
    fake_priority.run_with_priority.return_value = 0
    monkeypatch.setitem(sys.modules, "behave_priority", fake_priority)
    monkeypatch.setattr("behave_runner.core.orchestrator.check_optional", lambda *a, **k: True)

    config = RunConfig(features=["tests/fixtures/minimal/features"], priority_order=True)
    assert _run_with_priority(config) == 0
    fake_priority.run_with_priority.assert_called_once()


def test_run_with_trace_with_optional_package(monkeypatch) -> None:
    """Ensure _run_with_trace uses behave-trace when available."""

    from behave_runner.core.orchestrator import _run_with_trace

    fake_trace = MagicMock()
    fake_trace.run_with_trace.return_value = 0
    monkeypatch.setitem(sys.modules, "behave_trace", fake_trace)
    monkeypatch.setattr("behave_runner.core.orchestrator.check_optional", lambda *a, **k: True)

    config = RunConfig(features=["tests/fixtures/minimal/features"], trace=True)
    assert _run_with_trace(config) == 0
    fake_trace.run_with_trace.assert_called_once()


def test_run_shard_with_optional_package(monkeypatch) -> None:
    """Ensure _run_shard uses behave-pool sharding when available."""

    from behave_runner.core.orchestrator import _run_shard

    fake_pool = MagicMock()
    fake_pool.run_shard.return_value = 0
    monkeypatch.setitem(sys.modules, "behave_pool", fake_pool)
    monkeypatch.setattr("behave_runner.core.orchestrator.check_optional", lambda *a, **k: True)

    config = RunConfig(features=["tests/fixtures/minimal/features"], shard="1/2")
    assert _run_shard(config) == 0
    fake_pool.run_shard.assert_called_once()
