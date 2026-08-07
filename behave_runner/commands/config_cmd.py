"""Config command for behave-runner CLI."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from behave_runner.core.config import load_config

console = Console()

config_app = typer.Typer(
    name="config",
    help="Manage behave-runner configuration.",
    no_args_is_help=True,
)


def _find_pyproject() -> Path:
    """Find pyproject.toml in the current directory."""
    pyproject = Path.cwd() / "pyproject.toml"
    if not pyproject.exists():
        console.print("[red]Error: pyproject.toml not found in current directory.[/red]")
        raise typer.Exit(1)
    return pyproject


def _read_toml(path: Path) -> dict[str, Any]:
    """Read a TOML file and return its contents."""
    with path.open("rb") as f:
        return tomllib.load(f)


def _write_toml_section(path: Path, data: dict[str, Any]) -> None:
    """Append or update [tool.behave-runner] section preserving the rest."""
    content = path.read_text(encoding="utf-8")
    section_header = "[tool.behave-runner]"

    if section_header in content:
        console.print("[yellow]Section [tool.behave-runner] already exists.[/yellow]")
        return

    lines = content.splitlines(keepends=True)
    new_lines: list[str] = []
    inserted = False

    for line in lines:
        new_lines.append(line)
        if not inserted and line.strip().startswith("[tool."):
            new_lines.append(f"\n{section_header}\n")
            for key, value in data.items():
                new_lines.append(f"{key} = {_format_value(value)}\n")
            inserted = True

    if not inserted:
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines[-1] += "\n"
        new_lines.append(f"\n{section_header}\n")
        for key, value in data.items():
            new_lines.append(f"{key} = {_format_value(value)}\n")

    path.write_text("".join(new_lines), encoding="utf-8")


def _set_config_value(path: Path, key: str, value: str) -> None:
    """Set a key in the [tool.behave-runner] section."""
    content = path.read_text(encoding="utf-8")
    section_header = "[tool.behave-runner]"

    if section_header not in content:
        _write_toml_section(path, {key: _parse_value(value)})
        return

    lines = content.splitlines(keepends=True)
    new_lines: list[str] = []
    in_section = False
    key_found = False

    for line in lines:
        stripped = line.strip()

        if stripped == section_header:
            in_section = True
            new_lines.append(line)
            continue

        if in_section and stripped.startswith("[") and stripped != section_header:
            if not key_found:
                new_lines.append(f"{key} = {_format_value(_parse_value(value))}\n")
                key_found = True
            in_section = False

        if (
            in_section
            and stripped.startswith(f"{key} ")
            or (in_section and stripped.startswith(f"{key}="))
        ):
            new_lines.append(f"{key} = {_format_value(_parse_value(value))}\n")
            key_found = True
            continue

        new_lines.append(line)

    if in_section and not key_found:
        new_lines.append(f"{key} = {_format_value(_parse_value(value))}\n")

    path.write_text("".join(new_lines), encoding="utf-8")


def _format_value(value: Any) -> str:
    """Format a Python value as a TOML literal."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(value)
    return f'"{value}"'


def _parse_value(value: str) -> Any:
    """Parse a string value into a Python type for TOML."""
    if value.lower() in ("true", "false"):
        return value.lower() == "true"
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value.strip("\"'")


@config_app.command(name="show")
def config_show() -> None:
    """Show current behave-runner configuration."""
    config = load_config()
    if not config:
        console.print("[yellow]No [tool.behave-runner] configuration found.[/yellow]")
        return

    table = Table(title="behave-runner configuration")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")
    for key, value in sorted(config.items()):
        table.add_row(key, str(value))
    console.print(table)


@config_app.command(name="init")
def config_init() -> None:
    """Create [tool.behave-runner] section in pyproject.toml."""
    pyproject = _find_pyproject()
    _write_toml_section(pyproject, {})
    console.print("[green]Created [tool.behave-runner] section in pyproject.toml[/green]")


@config_app.command(name="set")
def config_set(
    key: str = typer.Argument(..., help="Configuration key to set."),
    value: str = typer.Argument(..., help="Value to assign."),
) -> None:
    """Set a configuration value in [tool.behave-runner]."""
    pyproject = _find_pyproject()
    _set_config_value(pyproject, key, value)
    console.print(f"[green]Set {key} = {value}[/green]")
