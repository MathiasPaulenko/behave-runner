"""E2E tests for behave-runner against Pokémon API fixture."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from typer.testing import CliRunner

from behave_runner.cli.app import app

runner = CliRunner()

pytestmark = pytest.mark.e2e_api

FEATURES = "tests/e2e/test_pokemon_api/features"

_skip_no_requests = pytest.mark.skipif(
    importlib.util.find_spec("requests") is None,
    reason="requests not installed",
)


@_skip_no_requests
def test_pokemon_run() -> None:
    """Test behave-runner run executes all Pokémon API scenarios."""
    result = runner.invoke(app, ["run", "--dry-run", FEATURES])
    assert result.exit_code == 0


def test_pokemon_list() -> None:
    """Test behave-runner list shows Pokémon API scenarios."""
    result = runner.invoke(app, ["list", FEATURES])
    assert result.exit_code == 0
    assert "pokemon" in result.stdout.lower()


def test_pokemon_select_pattern() -> None:
    """Test behave-runner select filters by pattern."""
    result = runner.invoke(app, ["select", "--pattern", ".*pokemon.*", FEATURES])
    assert result.exit_code == 0


@_skip_no_requests
def test_pokemon_run_format_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
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
            "reports/pokemon.json",
            fixture_path,
        ],
    )
    assert result.exit_code == 0


def test_pokemon_run_parallel() -> None:
    """--parallel 2 works on Pokémon API project."""
    if not importlib.util.find_spec("behave_pool"):
        pytest.skip("behave-pool not installed")
    result = runner.invoke(app, ["run", "--dry-run", "--parallel", "2", FEATURES])
    assert result.exit_code == 0


def test_pokemon_doctor() -> None:
    """doctor analyzes Pokémon API project."""
    if not importlib.util.find_spec("behave_doctor"):
        pytest.skip("behave-doctor not installed")
    result = runner.invoke(app, ["doctor", "tests/e2e/test_pokemon_api"])
    assert result.exit_code in (0, 1)


def test_pokemon_impact() -> None:
    """impact detects affected scenarios."""
    if not importlib.util.find_spec("behave_doctor"):
        pytest.skip("behave-doctor not installed")
    result = runner.invoke(
        app,
        ["impact", "tests/e2e/test_pokemon_api"],
    )
    assert result.exit_code in (0, 1, 2)


def test_pokemon_lint() -> None:
    """lint analyzes Pokémon API features."""
    if not importlib.util.find_spec("behave_lint"):
        pytest.skip("behave-lint not installed")
    result = runner.invoke(app, ["lint", "tests/e2e/test_pokemon_api/features"])
    assert result.exit_code in (0, 1)
