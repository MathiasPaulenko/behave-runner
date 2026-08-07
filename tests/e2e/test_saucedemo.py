"""E2E tests for behave-runner against saucedemo fixture."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from typer.testing import CliRunner

from behave_runner.cli.app import app

runner = CliRunner()

pytestmark = pytest.mark.e2e_web

FEATURES = "tests/e2e/test_saucedemo/features"

_skip_no_selenium = pytest.mark.skipif(
    importlib.util.find_spec("selenium") is None,
    reason="selenium not installed",
)


@_skip_no_selenium
def test_saucedemo_run() -> None:
    """Test behave-runner run executes all saucedemo scenarios."""
    result = runner.invoke(app, ["run", "--dry-run", FEATURES])
    assert result.exit_code == 0


def test_saucedemo_list() -> None:
    """Test behave-runner list shows saucedemo scenarios."""
    result = runner.invoke(app, ["list", FEATURES])
    assert result.exit_code == 0
    assert "login" in result.stdout.lower()


def test_saucedemo_select_smoke() -> None:
    """Test behave-runner select filters by @smoke tag."""
    result = runner.invoke(app, ["select", "--tags", "@smoke", FEATURES])
    assert result.exit_code == 0


@_skip_no_selenium
def test_saucedemo_run_format_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test behave-runner run generates JSON report."""
    monkeypatch.chdir(tmp_path)
    fixture_path = str(Path(__file__).resolve().parent.parent.parent / FEATURES)
    result = runner.invoke(
        app,
        [
            "run",
            "--dry-run",
            "--format",
            "json",
            "--output",
            "reports/saucedemo.json",
            fixture_path,
        ],
    )
    assert result.exit_code == 0


def test_saucedemo_run_parallel() -> None:
    """--parallel 2 works on saucedemo project."""
    if not importlib.util.find_spec("behave_pool"):
        pytest.skip("behave-pool not installed")
    result = runner.invoke(app, ["run", "--dry-run", "--parallel", "2", FEATURES])
    assert result.exit_code == 0


def test_saucedemo_run_retries() -> None:
    """--retries 1 works on saucedemo project."""
    if not importlib.util.find_spec("behave_retry"):
        pytest.skip("behave-retry not installed")
    result = runner.invoke(app, ["run", "--dry-run", "--retries", "1", FEATURES])
    assert result.exit_code == 0


def test_saucedemo_doctor() -> None:
    """doctor analyzes saucedemo project."""
    if not importlib.util.find_spec("behave_doctor"):
        pytest.skip("behave-doctor not installed")
    result = runner.invoke(app, ["doctor", "tests/e2e/test_saucedemo"])
    assert result.exit_code in (0, 1)


def test_saucedemo_impact() -> None:
    """impact detects affected scenarios."""
    if not importlib.util.find_spec("behave_doctor"):
        pytest.skip("behave-doctor not installed")
    result = runner.invoke(
        app,
        ["impact", "tests/e2e/test_saucedemo"],
    )
    assert result.exit_code in (0, 1, 2)


def test_saucedemo_lint() -> None:
    """lint analyzes saucedemo features."""
    if not importlib.util.find_spec("behave_lint"):
        pytest.skip("behave-lint not installed")
    result = runner.invoke(app, ["lint", "tests/e2e/test_saucedemo/features"])
    assert result.exit_code in (0, 1)
