"""Config file parsing for [tool.behave-runner] section."""

from __future__ import annotations

import configparser
import tomllib
from pathlib import Path
from typing import Any, cast

from behave_runner.exceptions import ConfigError


def load_config(project_path: Path | None = None) -> dict[str, Any]:
    """Load [tool.behave-runner] config from pyproject.toml or behave.ini."""
    root = project_path or Path.cwd()
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        with pyproject.open("rb") as f:
            data = tomllib.load(f)
        return cast(dict[str, Any], data.get("tool", {}).get("behave-runner", {}))
    behave_ini = root / "behave.ini"
    if behave_ini.exists():
        parser = configparser.ConfigParser()
        parser.read(behave_ini)
        if parser.has_section("behave-runner"):
            return dict(parser.items("behave-runner"))
    return {}


def load_profile(name: str, project_path: Path | None = None) -> dict[str, Any]:
    """Load a specific profile from config. Raises ConfigError if not found."""
    config = load_config(project_path)
    profiles = config.get("profiles", {})
    if isinstance(profiles, dict):
        profile = cast(dict[str, Any], profiles.get(name))
        if profile is None:
            raise ConfigError(f"Profile '{name}' not found in configuration.")
        return profile
    raise ConfigError(f"Profile '{name}' not found in configuration.")
