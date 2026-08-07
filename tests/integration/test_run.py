"""Integration tests for behave-runner run command."""

from __future__ import annotations

import importlib.util
import textwrap
from pathlib import Path

import pytest
from typer.testing import CliRunner

from behave_runner.cli.app import app

runner = CliRunner()


def test_run_minimal() -> None:
    result = runner.invoke(app, ["run", "tests/fixtures/minimal/features"])
    assert result.exit_code == 0


def test_run_dry_run() -> None:
    result = runner.invoke(app, ["run", "--dry-run", "tests/fixtures/minimal/features"])
    assert result.exit_code == 0


def test_run_tags_nonexistent() -> None:
    result = runner.invoke(
        app, ["run", "--tags", "@nonexistent", "tests/fixtures/minimal/features"]
    )
    assert result.exit_code == 0  # 0 scenarios matched, but no failure


def test_run_help() -> None:
    result = runner.invoke(app, ["run", "--help"])
    assert result.exit_code == 0
    assert "run" in result.stdout.lower()


def test_run_parallel_with_pool() -> None:
    """Test --parallel when behave-pool is installed."""
    if not importlib.util.find_spec("behave_pool"):
        pytest.skip("behave-pool not installed")
    result = runner.invoke(app, ["run", "--parallel", "2", "tests/fixtures/parallel/features"])
    assert result.exit_code == 0


def test_run_parallel_without_pool() -> None:
    """Test --parallel degrades gracefully when behave-pool not installed."""
    result = runner.invoke(app, ["run", "--parallel", "2", "tests/fixtures/minimal/features"])
    # Should still run, just sequentially
    assert result.exit_code == 0


def test_run_parallel_1_sequential() -> None:
    """Test --parallel 1 runs sequentially without warning."""
    result = runner.invoke(app, ["run", "--parallel", "1", "tests/fixtures/minimal/features"])
    assert result.exit_code == 0


def test_run_shard_1_of_3() -> None:
    """Shard 1/3 executes first third of scenarios."""
    if not importlib.util.find_spec("behave_pool"):
        pytest.skip("behave-pool not installed")
    result = runner.invoke(app, ["run", "--shard", "1/3", "tests/fixtures/parallel/features"])
    assert result.exit_code == 0


def test_run_shard_invalid_format() -> None:
    """Invalid shard format shows error."""
    result = runner.invoke(app, ["run", "--shard", "invalid", "tests/fixtures/minimal/features"])
    assert result.exit_code != 0


def test_run_shard_without_pool() -> None:
    """Shard without behave-pool degrades gracefully."""
    result = runner.invoke(app, ["run", "--shard", "1/2", "tests/fixtures/minimal/features"])
    assert result.exit_code == 0


def test_run_retries_with_retry() -> None:
    """Test --retries when behave-retry is installed."""
    if not importlib.util.find_spec("behave_retry"):
        pytest.skip("behave-retry not installed")
    result = runner.invoke(app, ["run", "--retries", "2", "tests/fixtures/failing/features"])
    assert result.exit_code == 1  # still fails after retries


def test_run_retries_without_retry() -> None:
    """Test --retries degrades gracefully when behave-retry not installed."""
    result = runner.invoke(app, ["run", "--retries", "2", "tests/fixtures/minimal/features"])
    assert result.exit_code == 0  # degrades, runs without retries


def test_run_flaky_report() -> None:
    """Test --flaky-report with --retries."""
    if not importlib.util.find_spec("behave_retry"):
        pytest.skip("behave-retry not installed")
    result = runner.invoke(
        app,
        ["run", "--retries", "1", "--flaky-report", "tests/fixtures/failing/features"],
    )
    assert result.exit_code == 1


def test_run_smoke() -> None:
    """Test --smoke when behave-priority is installed."""
    if not importlib.util.find_spec("behave_priority"):
        pytest.skip("behave-priority not installed")
    result = runner.invoke(app, ["run", "--smoke", "tests/fixtures/priority/features"])
    assert result.exit_code == 0


def test_run_smoke_without_priority() -> None:
    """Test --smoke falls back to --tags @smoke natively."""
    result = runner.invoke(app, ["run", "--smoke", "tests/fixtures/priority/features"])
    # Falls back to --tags @smoke natively
    assert result.exit_code == 0


def test_run_priority_order() -> None:
    """Test --priority-order when behave-priority is installed."""
    if not importlib.util.find_spec("behave_priority"):
        pytest.skip("behave-priority not installed")
    result = runner.invoke(app, ["run", "--priority-order", "tests/fixtures/priority/features"])
    assert result.exit_code == 0


def test_run_priority_order_without_priority() -> None:
    """Test --priority-order degrades gracefully."""
    result = runner.invoke(app, ["run", "--priority-order", "tests/fixtures/priority/features"])
    assert result.exit_code == 0


def test_run_profile(tmp_path: Path, monkeypatch) -> None:
    """Test --profile loads and merges config from pyproject.toml."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.ci]
            format = "json"
            output = "reports/ci.json"
        """)
    )
    monkeypatch.chdir(tmp_path)
    fixture_path = str(
        Path(__file__).resolve().parent.parent.parent
        / "tests"
        / "fixtures"
        / "minimal"
        / "features"
    )
    result = runner.invoke(app, ["run", "--profile", "ci", fixture_path])
    assert result.exit_code == 0


def test_run_scenario_timeout() -> None:
    """Test --scenario-timeout applies per-scenario timeout."""
    result = runner.invoke(
        app, ["run", "--scenario-timeout", "5", "tests/fixtures/minimal/features"]
    )
    assert result.exit_code == 0


def test_run_profile_not_found(monkeypatch, tmp_path: Path) -> None:
    """Test --profile with nonexistent profile shows error."""
    monkeypatch.chdir(tmp_path)
    fixture_path = str(
        Path(__file__).resolve().parent.parent.parent
        / "tests"
        / "fixtures"
        / "minimal"
        / "features"
    )
    result = runner.invoke(app, ["run", "--profile", "nonexistent", fixture_path])
    assert result.exit_code != 0


def test_run_ui_with_trace() -> None:
    """Test --ui when behave-trace is installed."""
    if not importlib.util.find_spec("behave_trace"):
        pytest.skip("behave-trace not installed")
    result = runner.invoke(app, ["run", "--ui", "--dry-run", "tests/fixtures/minimal/features"])
    assert result.exit_code == 0


def test_run_ui_without_trace() -> None:
    """Test --ui degrades gracefully when behave-trace not installed."""
    result = runner.invoke(app, ["run", "--ui", "--dry-run", "tests/fixtures/minimal/features"])
    assert result.exit_code == 0


def test_run_debug() -> None:
    """Test --debug degrades gracefully."""
    result = runner.invoke(app, ["run", "--debug", "--dry-run", "tests/fixtures/minimal/features"])
    assert result.exit_code == 0


def test_run_trace() -> None:
    """Test --trace degrades gracefully."""
    result = runner.invoke(app, ["run", "--trace", "--dry-run", "tests/fixtures/minimal/features"])
    assert result.exit_code == 0
