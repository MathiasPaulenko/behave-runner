"""Config command for behave-runner CLI."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from behave_runner.core.config import load_config
from behave_runner.exceptions import ConfigError

console = Console()

config_app = typer.Typer()

_KEY_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def _find_pyproject() -> Path | None:
    """Find the pyproject.toml in the current working directory."""
    pyproject = Path.cwd() / "pyproject.toml"
    return pyproject if pyproject.exists() else None


def _write_toml_section(path: Path, data: dict[str, object]) -> None:
    """Write a [tool.behave-runner] section to pyproject.toml if missing."""
    content = path.read_text()
    if "[tool.behave-runner]" in content:
        return
    with path.open("a") as f:
        f.write("\n[tool.behave-runner]\n")
        for key, value in data.items():
            f.write(f"{key} = {_format_value(value)}\n")


def _set_config_value(path: Path, key: str, value: object) -> None:
    """Set or add a key in [tool.behave-runner].

    This is a simple text-based edit. It handles the common case where the
    section and key exist. More complex TOML is out of scope.
    """
    _write_toml_section(path, {})
    content = path.read_text()
    lines = content.splitlines(keepends=True)

    # Find [tool.behave-runner] section
    section_start = -1
    for i, line in enumerate(lines):
        if line.strip() == "[tool.behave-runner]":
            section_start = i
            break

    if section_start == -1:
        raise ConfigError("Could not find [tool.behave-runner] section.")

    # Check for dotted keys that would conflict with existing subtables.
    # Check every parent prefix, not just the immediate one.
    if "." in key:
        parts = key.split(".")
        for depth in range(1, len(parts)):
            prefix = ".".join(parts[:depth])
            if f"[tool.behave-runner.{prefix}]" in content:
                raise ConfigError(
                    f"Cannot set dotted key '{key}' because "
                    f"[tool.behave-runner.{prefix}] subtable already exists. "
                    f"Edit the subtable directly instead."
                )

    # Try to replace an existing key within the section
    key_start = -1
    for i in range(section_start + 1, len(lines)):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            break
        if (
            stripped
            and not stripped.startswith("#")
            and (stripped.startswith(f"{key} ") or stripped.startswith(f"{key}="))
        ):
            key_start = i
            break

    formatted = _format_value(value)
    if key_start != -1:
        # Preserve leading indentation and trailing comment if any
        original = lines[key_start]
        match = re.match(r"(\s*)" + re.escape(key) + r"\s*=\s*", original)
        if match:
            lines[key_start] = f"{match.group(1)}{key} = {formatted}\n"
        else:
            lines[key_start] = f"{key} = {formatted}\n"
    else:
        # Insert at end of section (or end of file if no section end)
        insert_pos = len(lines)
        for i in range(section_start + 1, len(lines)):
            line = lines[i].strip()
            if line.startswith("[") and line.endswith("]"):
                insert_pos = i
                break
        lines.insert(insert_pos, f"{key} = {formatted}\n")

    new_content = "".join(lines)

    # Validate the result is parseable TOML before writing
    try:
        tomllib.loads(new_content)
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(
            f"Setting '{key}' would produce invalid TOML: {e}. The file was not modified."
        ) from e

    path.write_text(new_content)


def _parse_value(value: str) -> object:
    """Parse a config value from CLI into a Python object."""
    lowered = value.lower().strip()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value.strip().strip("\"'")


def _escape_toml_string(value: str) -> str:
    """Escape a string for a TOML basic string."""
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
        .replace("\b", "\\b")
        .replace("\f", "\\f")
    )


def _format_value(value: object) -> str:
    """Format a value for writing to pyproject.toml."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(_format_value(v) for v in value) + "]"
    if isinstance(value, str):
        return f'"{_escape_toml_string(value)}"'
    return f'"{_escape_toml_string(str(value))}"'


@config_app.callback(invoke_without_command=True)
def default_callback() -> None:
    """Default callback to make the config command a Typer app."""


@config_app.command("show")
def config_show() -> None:
    """Show the current [tool.behave-runner] configuration."""
    try:
        config = load_config()
    except ConfigError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(2) from e

    if not config:
        console.print("[yellow]No configuration found.[/yellow]")
        return

    table = Table(title="behave-runner configuration")
    table.add_column("Key")
    table.add_column("Value")
    for key, value in config.items():
        table.add_row(key, str(value))
    console.print(table)


@config_app.command("init")
def config_init() -> None:
    """Initialize a default [tool.behave-runner] section."""
    pyproject = _find_pyproject()
    if pyproject is None:
        console.print("[red]Error: no pyproject.toml found. Run this from a project root.[/red]")
        raise typer.Exit(2)

    content = pyproject.read_text()
    if "[tool.behave-runner]" in content:
        console.print("[yellow][tool.behave-runner] already exists.[/yellow]")
        return

    _write_toml_section(pyproject, {})
    console.print("[green]Created [tool.behave-runner] section.[/green]")


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Configuration key to set."),
    value: str = typer.Argument(..., help="Value to set."),
) -> None:
    """Set a value in [tool.behave-runner]."""
    if not _KEY_RE.match(key):
        console.print(
            "[red]Error: key must contain only letters, numbers, "
            "underscores, dots, or hyphens.[/red]"
        )
        raise typer.Exit(2)

    pyproject = _find_pyproject()
    if pyproject is None:
        console.print("[red]Error: no pyproject.toml found. Run this from a project root.[/red]")
        raise typer.Exit(2)

    parsed = _parse_value(value)
    try:
        _set_config_value(pyproject, key, parsed)
    except ConfigError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(2) from e
    console.print(f"[green]Set {key} = {value}[/green]")
