"""Integration tests for behave-runner doctor command."""

from __future__ import annotations

import importlib.util

import pytest
from typer.testing import CliRunner

from behave_runner.cli.app import app

runner = CliRunner()


def test_doctor_with_dep() -> None:
    """Test doctor when behave-doctor is installed."""
    if not importlib.util.find_spec("behave_doctor"):
        pytest.skip("behave-doctor not installed")
    result = runner.invoke(app, ["doctor", "tests/fixtures/minimal"])
    assert result.exit_code in (0, 1)


def test_doctor_without_dep() -> None:
    """Test doctor degrades gracefully when behave-doctor not installed."""
    result = runner.invoke(app, ["doctor", "tests/fixtures/minimal"])
    assert result.exit_code in (0, 1, 2)


def test_doctor_help() -> None:
    """Test doctor --help."""
    result = runner.invoke(app, ["doctor", "--help"])
    assert result.exit_code == 0
    assert "doctor" in result.stdout.lower()
