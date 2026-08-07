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
