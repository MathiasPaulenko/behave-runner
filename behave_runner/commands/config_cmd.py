"""Config command for behave-runner CLI."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from behave_runner.core.config import load_config
from behave_runner.exceptions import ConfigError

console = Console()

config_app = typer.Typer(
    name="config",
    help="Manage behave-runner configuration.",
    no_args_is_help=True,
)

_KEY_RE = re.compile(r"^[A-Za-z0-9_.-]+$")

_ROOT_HEADER = "[tool.behave-runner]"


def _find_pyproject() -> Path | None:
    """Find the pyproject.toml in the current working directory."""
    pyproject = Path.cwd() / "pyproject.toml"
    return pyproject if pyproject.exists() else None


def _has_header(lines: list[str], header: str) -> bool:
    """Check for an exact TOML section header line (ignores comments)."""
    return any(line.strip() == header for line in lines)


def _write_toml_section(path: Path, data: dict[str, object]) -> None:
    """Write a [tool.behave-runner] section to pyproject.toml if missing."""
    content = path.read_text(encoding="utf-8")
    if _has_header(content.splitlines(), _ROOT_HEADER):
        return
    with path.open("a", encoding="utf-8") as f:
        f.write(f"\n{_ROOT_HEADER}\n")
        for key, value in data.items():
            f.write(f"{key} = {_format_value(value)}\n")


def _resolve_section(lines: list[str], key: str) -> tuple[str, str]:
    """Resolve a dotted key to (section header, key within that section).

    If a ``[tool.behave-runner.<prefix>]`` subtable exists for a prefix of a
    dotted key, the leaf is written inside that subtable — writing the dotted
    key in the parent section would conflict with the subtable definition.
    """
    parts = key.split(".")
    for depth in range(len(parts) - 1, 0, -1):
        header = f"[tool.behave-runner.{'.'.join(parts[:depth])}]"
        if _has_header(lines, header):
            return header, ".".join(parts[depth:])
    return _ROOT_HEADER, key


def _split_comment(text: str) -> tuple[str, str]:
    """Split a TOML value string into (value, comment), respecting quotes."""
    quote = ""
    i = 0
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == "\\" and quote == '"':
                i += 1  # skip escaped char inside basic strings
            elif ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
        elif ch == "#":
            return text[:i], text[i:]
        i += 1
    return text, ""


def _set_config_value(path: Path, key: str, value: object) -> None:
    """Set or add a key in [tool.behave-runner].

    This is a simple text-based edit. It handles the common case where the
    section and key exist, and routes dotted keys into existing subtables.
    More complex TOML is out of scope.
    """
    _write_toml_section(path, {})
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)

    section_header, leaf_key = _resolve_section(lines, key)

    section_start = -1
    for i, line in enumerate(lines):
        if line.strip() == section_header:
            section_start = i
            break

    if section_start == -1:
        raise ConfigError(f"Could not find {section_header} section.")

    # Try to replace an existing key within the section
    key_start = -1
    for i in range(section_start + 1, len(lines)):
        stripped = lines[i].strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            break
        if (
            stripped
            and not stripped.startswith("#")
            and (stripped.startswith(f"{leaf_key} ") or stripped.startswith(f"{leaf_key}="))
        ):
            key_start = i
            break

    formatted = _format_value(value)
    if key_start != -1:
        # Preserve leading indentation and any trailing comment
        original = lines[key_start].rstrip("\n")
        match = re.match(r"(\s*)" + re.escape(leaf_key) + r"\s*=\s*(.*)$", original)
        if match:
            indent, rest = match.group(1), match.group(2)
            _, comment = _split_comment(rest)
            gap = " " if comment else ""
            lines[key_start] = f"{indent}{leaf_key} = {formatted}{gap}{comment}\n"
        else:
            lines[key_start] = f"{leaf_key} = {formatted}\n"
    else:
        # Insert at end of section (or end of file if no section end)
        insert_pos = len(lines)
        for i in range(section_start + 1, len(lines)):
            line = lines[i].strip()
            if line.startswith("[") and line.endswith("]"):
                insert_pos = i
                break
        lines.insert(insert_pos, f"{leaf_key} = {formatted}\n")

    new_content = "".join(lines)

    # Validate the result is parseable TOML before writing
    try:
        tomllib.loads(new_content)
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(
            f"Setting '{key}' would produce invalid TOML: {e}. The file was not modified."
        ) from e

    path.write_text(new_content, encoding="utf-8")


def _parse_value(value: str) -> object:
    """Parse a config value from CLI into a Python object.

    TOML syntax is supported for lists, quoted strings, numbers, and
    booleans (e.g. ``["@smoke", "@fast"]``). Bare values fall back to
    comma-split lists in brackets, then bool/int/float/string.
    """
    raw = value.strip()
    try:
        return tomllib.loads(f"k = {raw}")["k"]
    except tomllib.TOMLDecodeError:
        pass
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [_parse_value(item) for item in inner.split(",")]
    lowered = raw.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    return raw.strip("\"'")


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
        if isinstance(value, (dict, list)):
            table.add_row(key, json.dumps(value, default=str))
        else:
            table.add_row(key, str(value))
    console.print(table)


@config_app.command("init")
def config_init() -> None:
    """Initialize a default [tool.behave-runner] section."""
    pyproject = _find_pyproject()
    if pyproject is None:
        console.print("[red]Error: no pyproject.toml found. Run this from a project root.[/red]")
        raise typer.Exit(2)

    content = pyproject.read_text(encoding="utf-8")
    if _has_header(content.splitlines(), _ROOT_HEADER):
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
    console.print(f"[green]Set {escape(key)} = {escape(value)}[/green]")
