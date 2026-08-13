"""Config file parsing for [tool.behave-runner] section."""

from __future__ import annotations

import configparser
import tomllib
from pathlib import Path
from typing import Any, cast

from behave_runner.exceptions import ConfigError

_INT_KEYS = {
    "parallel",
    "retries",
    "max_failures",
    "max_fail",
    "timeout",
    "scenario_timeout",
}

_BOOL_KEYS = {
    "dry_run",
    "stop_on_failure",
    "flaky_report",
    "priority_order",
    "fail_fast",
    "no_color",
    "verbose",
    "smoke",
    "ui",
    "debug",
    "trace",
}

# String keys that pass through without normalization (in addition to
# fmt, outfile, shard, format, output which are handled as raw strings).
# parallel_scheme, parallel_balance, parallel_timing_file are strings.
_LIST_KEYS = {"tags", "features", "name"}


class _BadConfigValueError(ConfigError):
    """Raised when a profile value cannot be normalized."""


class _BadBooleanError(_BadConfigValueError):
    """Raised when a boolean profile value cannot be parsed."""


class _BadIntegerError(_BadConfigValueError):
    """Raised when an integer profile value cannot be parsed."""


def load_config(project_path: Path | None = None) -> dict[str, Any]:
    """Load [tool.behave-runner] config from pyproject.toml or behave.ini."""
    root = project_path or Path.cwd()
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        try:
            with pyproject.open("rb") as f:
                data = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            raise ConfigError(f"Failed to parse {pyproject}: {e}") from e
        except OSError as e:
            raise ConfigError(f"Failed to read {pyproject}: {e}") from e
        tool_section = data.get("tool")
        if tool_section is None:
            config = {}
        elif not isinstance(tool_section, dict):
            raise ConfigError(f"[tool] must be a table in {pyproject}")
        else:
            config = cast(dict[str, Any], tool_section.get("behave-runner", {}))
        if not isinstance(config, dict):
            raise ConfigError(f"[tool.behave-runner] must be a table in {pyproject}")
        if config:
            return config
    behave_ini = root / "behave.ini"
    if behave_ini.exists():
        parser = configparser.ConfigParser()
        try:
            parser.read(behave_ini)
        except (configparser.Error, UnicodeDecodeError) as e:
            raise ConfigError(f"Failed to parse {behave_ini}: {e}") from e
        if parser.has_section("behave-runner"):
            flat = dict(parser.items("behave-runner"))
            return _ini_flat_to_nested(flat)
    return {}


def _ini_flat_to_nested(flat: dict[str, str]) -> dict[str, Any]:
    """Convert behave.ini flat dot-notation keys into nested dictionaries.

    Raises ConfigError if a key conflicts with an existing leaf value
    (e.g., `profiles = x` and `profiles.ci.parallel = 4` cannot coexist).
    """
    nested: dict[str, Any] = {}
    for key, value in flat.items():
        parts = key.split(".")
        current = nested
        for depth, part in enumerate(parts[:-1]):
            prefix = ".".join(parts[: depth + 1])
            if part in current:
                existing = current[part]
                if not isinstance(existing, dict):
                    raise ConfigError(
                        f"Config key conflict: '{key}' cannot be set because "
                        f"'{prefix}' is already a value."
                    )
            else:
                current[part] = {}
            current = current[part]
        leaf = parts[-1]
        if leaf in current and isinstance(current[leaf], dict):
            raise ConfigError(
                f"Config key conflict: '{key}' cannot be set because "
                f"'{key}' is already a parent of other keys."
            )
        current[leaf] = value
    return nested


def load_profile(name: str, project_path: Path | None = None) -> dict[str, Any]:
    """Load a specific profile from config. Raises ConfigError if not found."""
    config = load_config(project_path)
    profiles = config.get("profiles", {})
    if not isinstance(profiles, dict):
        raise ConfigError("Invalid 'profiles' configuration: must be a table.")
    profile = cast(dict[str, Any] | None, profiles.get(name))
    if profile is None:
        raise ConfigError(f"Profile '{name}' not found in configuration.")
    if not isinstance(profile, dict):
        raise ConfigError(f"Profile '{name}' must be a table.")
    return _normalize_profile(profile)


def _normalize_profile(profile: dict[str, Any]) -> dict[str, Any]:
    """Normalize profile values from ini config (strings) to proper types."""
    normalized = dict(profile)
    for key, value in profile.items():
        if key in _LIST_KEYS:
            normalized[key] = _normalize_list(value)
        elif key in _INT_KEYS:
            normalized[key] = _normalize_int(key, value)
        elif key in _BOOL_KEYS:
            normalized[key] = _normalize_bool(key, value)
    return normalized


def _normalize_list(value: Any) -> list[str]:
    """Normalize a list-like value to a list of strings."""
    if isinstance(value, list):
        return [str(item).strip() for item in value]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    raise ConfigError(f"Expected a list or comma-separated string, got {value!r}")


def _normalize_int(key: str, value: Any) -> int:
    """Normalize an integer profile value."""
    if isinstance(value, bool):
        raise _BadIntegerError(f"Config key '{key}' must be an integer, not a boolean")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError as e:
            raise _BadIntegerError(f"Config key '{key}' must be an integer, got {value!r}") from e
    raise _BadIntegerError(f"Config key '{key}' must be an integer, got {value!r}")


def _normalize_bool(key: str, value: Any) -> bool:
    """Normalize a boolean profile value."""
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value != 0
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("true", "yes", "1"):
            return True
        if lowered in ("false", "no", "0"):
            return False
        raise _BadBooleanError(f"Config key '{key}' must be a boolean, got {value!r}")
    raise _BadBooleanError(f"Config key '{key}' must be a boolean, got {value!r}")
