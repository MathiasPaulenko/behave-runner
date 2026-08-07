"""Integration tests for behave-runner config command."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from typer.testing import CliRunner

from behave_runner.cli.app import app

runner = CliRunner()


def test_config_show_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test config show with no configuration."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0


def test_config_show_with_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test config show with existing configuration."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner]
            default_parallel = 4
        """)
    )
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0
    assert "4" in result.stdout


def test_config_init(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test config init creates the section."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "init"])
    assert result.exit_code == 0
    content = (tmp_path / "pyproject.toml").read_text()
    assert "[tool.behave-runner]" in content


def test_config_init_already_exists(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test config init does not overwrite existing section."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [project]
            name = 'test'

            [tool.behave-runner]
            default_parallel = 4
        """)
    )
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "init"])
    assert result.exit_code == 0
    content = (tmp_path / "pyproject.toml").read_text()
    assert content.count("[tool.behave-runner]") == 1


def test_config_set(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test config set writes a value."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [project]
            name = 'test'

            [tool.behave-runner]
        """)
    )
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "set", "default_parallel", "4"])
    assert result.exit_code == 0
    content = (tmp_path / "pyproject.toml").read_text()
    assert "default_parallel = 4" in content


def test_config_set_creates_section(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test config set creates section if missing."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "set", "default_parallel", "4"])
    assert result.exit_code == 0
    content = (tmp_path / "pyproject.toml").read_text()
    assert "[tool.behave-runner]" in content
    assert "default_parallel = 4" in content


def test_config_help() -> None:
    """Test config --help."""
    result = runner.invoke(app, ["config", "--help"])
    assert result.exit_code == 0
    assert "config" in result.stdout.lower()
