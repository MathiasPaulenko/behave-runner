"""Tests for behave_runner.core.config."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from behave_runner.core.config import load_config, load_profile
from behave_runner.exceptions import ConfigError


def test_no_config_returns_empty(tmp_path: Path) -> None:
    assert load_config(tmp_path) == {}


def test_pyproject_config(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
        [tool.behave-runner]
        default_parallel = 4
        output_dir = "reports"
    """)
    )
    config = load_config(tmp_path)
    assert config["default_parallel"] == 4
    assert config["output_dir"] == "reports"


def test_profiles(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
        [tool.behave-runner.profiles.ci]
        parallel = 8
        format = "json"
    """)
    )
    profile = load_profile("ci", tmp_path)
    assert profile["parallel"] == 8


def test_profile_not_found(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.behave-runner]\n")
    with pytest.raises(ConfigError, match="Profile 'nonexistent' not found"):
        load_profile("nonexistent", tmp_path)


def test_behave_ini_fallback(tmp_path: Path) -> None:
    (tmp_path / "behave.ini").write_text(
        textwrap.dedent("""
        [behave-runner]
        default_parallel = 2
    """)
    )
    config = load_config(tmp_path)
    assert config["default_parallel"] == "2"


def test_behave_ini_nested_profile(tmp_path: Path) -> None:
    (tmp_path / "behave.ini").write_text(
        textwrap.dedent("""
        [behave-runner]
        profiles.default.parallel = 4
        profiles.default.dry_run = false
        profiles.default.tags = @smoke, @fast
    """)
    )
    profile = load_profile("default", tmp_path)
    assert profile["parallel"] == 4
    assert profile["dry_run"] is False
    assert profile["tags"] == ["@smoke", "@fast"]


def test_malformed_pyproject_raises_config_error(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.behave-runner\nparallel = 4")
    with pytest.raises(ConfigError, match="Failed to parse"):
        load_config(tmp_path)


def test_profile_string_values_are_normalized(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
        [tool.behave-runner.profiles.ci]
        parallel = "4"
        dry_run = "true"
        retries = "2"
        tags = "@smoke, @fast"
    """)
    )
    profile = load_profile("ci", tmp_path)
    assert profile["parallel"] == 4
    assert profile["dry_run"] is True
    assert profile["retries"] == 2
    assert profile["tags"] == ["@smoke", "@fast"]


def test_profile_invalid_integer_raises(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
        [tool.behave-runner.profiles.ci]
        parallel = "not-a-number"
    """)
    )
    with pytest.raises(ConfigError, match="parallel"):
        load_profile("ci", tmp_path)


def test_profile_invalid_boolean_raises(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
        [tool.behave-runner.profiles.ci]
        dry_run = "maybe"
    """)
    )
    with pytest.raises(ConfigError, match="dry_run"):
        load_profile("ci", tmp_path)
