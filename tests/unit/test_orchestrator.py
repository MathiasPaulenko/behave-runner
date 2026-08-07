"""Tests for behave_runner.core.orchestrator."""

from __future__ import annotations

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
    config = RunConfig(max_failures=3)
    cmd = build_behave_command(config)
    assert "--max-failures" in cmd
    assert "3" in cmd


def test_timeout() -> None:
    config = RunConfig(timeout=30)
    cmd = build_behave_command(config)
    assert "--timeout" in cmd
    assert "30" in cmd


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
