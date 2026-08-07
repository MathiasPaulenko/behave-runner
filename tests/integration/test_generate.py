"""Integration tests for behave-runner generate command."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from typer.testing import CliRunner

from behave_runner.cli.app import app

runner = CliRunner()


def test_generate_step(tmp_path: Path, monkeypatch) -> None:
    """Test generate step when behave-gen is installed."""
    if not importlib.util.find_spec("behave_gen"):
        pytest.skip("behave-gen not installed")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["generate", "step", "--lib", "http"])
    assert result.exit_code == 0


def test_generate_feature(tmp_path: Path, monkeypatch) -> None:
    """Test generate feature when behave-gen is installed."""
    if not importlib.util.find_spec("behave_gen"):
        pytest.skip("behave-gen not installed")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["generate", "feature", "Login"])
    assert result.exit_code == 0


def test_generate_without_dep(tmp_path: Path, monkeypatch) -> None:
    """Test generate degrades gracefully when behave-gen not installed."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["generate", "step", "--lib", "http"])
    assert result.exit_code in (0, 2)


def test_generate_help() -> None:
    """Test generate --help."""
    result = runner.invoke(app, ["generate", "--help"])
    assert result.exit_code == 0
    assert "generate" in result.stdout.lower()
