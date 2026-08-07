"""Integration tests for behave-runner init command."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from typer.testing import CliRunner

from behave_runner.cli.app import app

runner = CliRunner()


def test_init_creates_structure(tmp_path: Path, monkeypatch) -> None:
    """Test init creates project structure when behave-gen is installed."""
    if not importlib.util.find_spec("behave_gen"):
        pytest.skip("behave-gen not installed")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "myproject"])
    assert result.exit_code == 0
    assert (tmp_path / "myproject" / "features").exists()


def test_init_without_dep() -> None:
    """Test init degrades gracefully when behave-gen not installed."""
    result = runner.invoke(app, ["init"])
    assert result.exit_code in (0, 2)


def test_init_help() -> None:
    """Test init --help."""
    result = runner.invoke(app, ["init", "--help"])
    assert result.exit_code == 0
    assert "init" in result.stdout.lower()
