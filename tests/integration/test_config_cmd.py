"""Integration tests for behave-runner config command."""

from __future__ import annotations

import textwrap
import tomllib
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


def test_config_set_boolean(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test config set writes a boolean as TOML true/false."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [project]
            name = 'test'

            [tool.behave-runner]
        """)
    )
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "set", "dry_run", "true"])
    assert result.exit_code == 0
    content = (tmp_path / "pyproject.toml").read_text()
    assert "dry_run = true" in content
    assert 'dry_run = "true"' not in content

    result_false = runner.invoke(app, ["config", "set", "dry_run", "false"])
    assert result_false.exit_code == 0
    content = (tmp_path / "pyproject.toml").read_text()
    assert "dry_run = false" in content


def test_config_set_float(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test config set writes a float value."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [project]
            name = 'test'

            [tool.behave-runner]
        """)
    )
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "set", "timeout", "3.14"])
    assert result.exit_code == 0
    content = (tmp_path / "pyproject.toml").read_text()
    assert "timeout = 3.14" in content


def test_config_set_string_with_quotes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test config set writes a string value with proper TOML quoting."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [project]
            name = 'test'

            [tool.behave-runner]
        """)
    )
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "set", "tags", "@smoke"])
    assert result.exit_code == 0
    content = (tmp_path / "pyproject.toml").read_text()
    assert 'tags = "@smoke"' in content


def test_config_set_nested_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test config set with a dotted key creates a nested structure."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [project]
            name = 'test'

            [tool.behave-runner]
        """)
    )
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "set", "profiles.ci.tags", "@smoke"])
    assert result.exit_code == 0
    content = (tmp_path / "pyproject.toml").read_text()
    assert 'profiles.ci.tags = "@smoke"' in content

    with (tmp_path / "pyproject.toml").open("rb") as f:
        data = tomllib.load(f)
    br = data.get("tool", {}).get("behave-runner", {})
    assert br.get("profiles", {}).get("ci", {}).get("tags") == "@smoke"


def test_config_set_invalid_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test config set rejects keys with invalid characters."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "set", "key with spaces", "value"])
    assert result.exit_code == 2


def test_config_set_update_existing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test config set replaces an existing value."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [project]
            name = 'test'

            [tool.behave-runner]
            parallel = 2
        """)
    )
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "set", "parallel", "8"])
    assert result.exit_code == 0
    content = (tmp_path / "pyproject.toml").read_text()
    assert "parallel = 8" in content
    assert "parallel = 2" not in content
    assert content.count("parallel =") == 1


def test_config_init_no_pyproject(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test config init fails without pyproject.toml."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "init"])
    assert result.exit_code == 2


def test_config_set_no_pyproject(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test config set fails without pyproject.toml."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "set", "parallel", "4"])
    assert result.exit_code == 2


def test_config_show_malformed_pyproject(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test config show handles malformed pyproject.toml."""
    (tmp_path / "pyproject.toml").write_text("this is not valid toml = = =\n")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 2


def test_config_set_dotted_key_conflict_with_subtable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test config set rejects dotted key when a subtable already exists."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [project]
            name = 'test'

            [tool.behave-runner]
            other = 1

            [tool.behave-runner.profiles.ci]
            tags = "@smoke"
        """)
    )
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "set", "profiles.ci.tags", "@regression"])
    assert result.exit_code == 2


def test_config_help() -> None:
    """Test config --help."""
    result = runner.invoke(app, ["config", "--help"])
    assert result.exit_code == 0
    assert "config" in result.stdout.lower()
