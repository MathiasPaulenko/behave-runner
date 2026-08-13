"""Tests for behave_runner CLI."""

from __future__ import annotations

from typer.testing import CliRunner

from behave_runner import __version__
from behave_runner.cli.app import app

runner = CliRunner()


def test_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "behave-runner" in result.stdout


def test_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_no_args_shows_help() -> None:
    result = runner.invoke(app, [])
    assert result.exit_code in (0, 2)
    assert "Usage:" in result.output
