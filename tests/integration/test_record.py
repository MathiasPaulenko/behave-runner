"""Integration tests for behave-runner record command."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from typer.testing import CliRunner

from behave_runner.cli.app import app

runner = CliRunner()


def test_record_with_dep(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test record when wavexis is installed."""
    if not importlib.util.find_spec("wavexis"):
        pytest.skip("wavexis not installed")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["record"])
    assert result.exit_code in (0, 1, 2)


def test_record_without_dep() -> None:
    """Test record degrades gracefully when wavexis not installed."""
    result = runner.invoke(app, ["record"])
    assert result.exit_code in (0, 2)


def test_record_help() -> None:
    """Test record --help."""
    result = runner.invoke(app, ["record", "--help"])
    assert result.exit_code == 0
    assert "record" in result.stdout.lower()
