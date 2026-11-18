"""Config command for behave-runner CLI."""

from __future__ import annotations

import contextlib
import json
import os
import re
import tomllib
from pathlib import Path

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from behave_runner.core.config import load_config
from behave_runner.exceptions import ConfigError
from behave_runner.utils import find_project_root

console = Console()
err_console = Console(stderr=True)

config_app = typer.Typer(
    name="config",
    help="Manage behave-runner configuration.",
    no_args_is_help=True,
)

_KEY_RE = re.compile(r"^[A-Za-z0-9_.-]+$")

_ROOT_HEADER = "[tool.behave-runner]"


def _find_pyproject() -> Path | None:
    """Find the pyproject.toml at the project root."""
    pyproject = find_project_root() / "pyproject.toml"
    return pyproject if pyproject.exists() else None


def _normalize_header_line(line: str) -> str:
    """Reduce a line to its canonical header form for comparison.

    TOML allows whitespace inside brackets and trailing comments, so
    ``[ tool.behave-runner ] # comment`` is the same section as
    ``[tool.behave-runner]``.
    """
    return re.sub(r"\s+", "", line.split("#", 1)[0])


# A table header must be a bare-key (optionally dotted) path in brackets,
# optionally followed by a comment. Array items like ``["a", "b"],`` inside
# a multi-line value must NOT be mistaken for a section end.
_HEADER_RE = re.compile(r"^\[\s*[A-Za-z0-9_-]+(?:\s*\.\s*[A-Za-z0-9_-]+)*\s*\](?:\s*#.*)?$")


def _is_header_line(stripped: str) -> bool:
    """Check if a stripped line starts a TOML table (tolerates comments)."""
    return bool(_HEADER_RE.match(stripped))


def _has_header(lines: list[str], header: str) -> bool:
    """Check for a TOML section header line (ignores comments and spacing)."""
    return any(_normalize_header_line(line) == header for line in lines)


def _read_toml_text(path: Path) -> str:
    """Read a TOML file as UTF-8 text, raising ConfigError on bad encoding."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise ConfigError(f"Failed to decode {path} as UTF-8: {e}") from e


def _write_toml_section(path: Path, data: dict[str, object]) -> None:
    """Write a [tool.behave-runner] section to pyproject.toml if missing."""
    content = _read_toml_text(path)
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


def _validate_new_content(key: str, expected: object, new_content: str) -> None:
    """Validate edited TOML before it touches disk.

    Besides checking that the result parses, verify the key actually landed
    in ``[tool.behave-runner]`` with the expected value — a table header
    hidden inside a multi-line string could otherwise redirect the write
    into the wrong table while still producing valid TOML.
    """
    try:
        data = tomllib.loads(new_content)
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(
            f"Setting '{key}' would produce invalid TOML: {e}. The file was not modified."
        ) from e
    node: object = data.get("tool")
    if not isinstance(node, dict):
        node = {}
    node = node.get("behave-runner")
    if not isinstance(node, dict):
        raise ConfigError(
            f"Setting '{key}' did not land in [tool.behave-runner]. The file was not modified."
        )
    current: object = node
    for part in key.split("."):
        if not isinstance(current, dict) or part not in current:
            raise ConfigError(
                f"Setting '{key}' did not land in [tool.behave-runner]. The file was not modified."
            )
        current = current[part]
    if current != expected:
        raise ConfigError(
            f"Setting '{key}' produced an unexpected value. The file was not modified."
        )


def _atomic_write(path: Path, content: str) -> None:
    """Write content to path via a temp file + rename so a crash mid-write
    cannot leave a truncated pyproject.toml."""
    tmp = path.with_name(path.name + ".tmp")
    try:
        tmp.write_text(content, encoding="utf-8")
        os.replace(tmp, path)
    except OSError:
        with contextlib.suppress(OSError):
            tmp.unlink(missing_ok=True)
        raise


def _set_config_value(path: Path, key: str, value: object) -> None:
    """Set or add a key in [tool.behave-runner].

    This is a simple text-based edit. It handles the common case where the
    section and key exist, and routes dotted keys into existing subtables.
    More complex TOML is out of scope. The file is only written after the
    complete result validates as TOML.
    """
    content = _read_toml_text(path)
    lines = content.splitlines(keepends=True)

    section_header, leaf_key = _resolve_section(lines, key)
    formatted = _format_value(value)

    section_start = -1
    for i, line in enumerate(lines):
        if _normalize_header_line(line) == section_header:
            section_start = i
            break

    if section_start == -1:
        # Only the root section can be missing here: _resolve_section only
        # returns subtable headers verified to exist. Append section + key
        # in memory so a validation failure never leaves a partial edit.
        new_content = content
        if new_content and not new_content.endswith("\n"):
            new_content += "\n"
        new_content += f"\n{_ROOT_HEADER}\n{leaf_key} = {formatted}\n"
        _validate_new_content(key, value, new_content)
        _atomic_write(path, new_content)
        return

    # Try to replace an existing key within the section
    key_start = -1
    for i in range(section_start + 1, len(lines)):
        stripped = lines[i].strip()
        if _is_header_line(stripped):
            break
        if (
            stripped
            and not stripped.startswith("#")
            and (stripped.startswith(f"{leaf_key} ") or stripped.startswith(f"{leaf_key}="))
        ):
            key_start = i
            break

    if key_start != -1:
        # Preserve leading indentation and any trailing comment
        original = lines[key_start].rstrip("\n")
        match = re.match(r"(\s*)" + re.escape(leaf_key) + r"\s*=\s*(.*)$", original)
        if match:
            indent, rest = match.group(1), match.group(2)
            _, comment = _split_comment(rest)
            gap = " " if comment else ""
            # Multi-line values (e.g. an array spanning several lines) extend
            # until the assignment parses as TOML — consume the whole range
            # so no orphaned lines are left behind.
            end = key_start
            value_text = rest
            while end + 1 < len(lines):
                try:
                    tomllib.loads(f"{leaf_key} = {value_text}")
                    break
                except tomllib.TOMLDecodeError:
                    end += 1
                    value_text += lines[end]
            lines[key_start : end + 1] = [f"{indent}{leaf_key} = {formatted}{gap}{comment}\n"]
        else:
            lines[key_start] = f"{leaf_key} = {formatted}\n"
    else:
        # Insert at end of section (or end of file if no section end)
        insert_pos = len(lines)
        for i in range(section_start + 1, len(lines)):
            if _is_header_line(lines[i].strip()):
                insert_pos = i
                break
        new_line = f"{leaf_key} = {formatted}\n"
        if lines and not lines[insert_pos - 1].endswith("\n"):
            new_line = "\n" + new_line
        lines.insert(insert_pos, new_line)

    new_content = "".join(lines)
    _validate_new_content(key, value, new_content)
    _atomic_write(path, new_content)


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
        err_console.print(f"[red]Error: {e}[/red]")
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


def _warn_if_ini_active(pyproject: Path) -> None:
    """Warn when behave.ini is the active config file.

    Writing ``[tool.behave-runner]`` to ``pyproject.toml`` shadows an
    existing ``behave.ini`` because pyproject.toml takes precedence —
    the INI's values would silently stop applying.
    """
    if not (pyproject.parent / "behave.ini").exists():
        return
    has_section = False
    try:
        data = tomllib.loads(_read_toml_text(pyproject))
        section = data.get("tool", {}).get("behave-runner")
        has_section = isinstance(section, dict) and bool(section)
    except (tomllib.TOMLDecodeError, ConfigError):
        has_section = False
    if not has_section:
        err_console.print(
            "[yellow]Warning: behave.ini holds the active config; writing to "
            "pyproject.toml will take precedence over it.[/yellow]"
        )


@config_app.command("init")
def config_init() -> None:
    """Initialize a default [tool.behave-runner] section."""
    pyproject = _find_pyproject()
    if pyproject is None:
        err_console.print(
            "[red]Error: no pyproject.toml found. Run this from a project root.[/red]"
        )
        raise typer.Exit(2)

    try:
        content = _read_toml_text(pyproject)
        if _has_header(content.splitlines(), _ROOT_HEADER):
            console.print("[yellow][tool.behave-runner] already exists.[/yellow]")
            return
        _warn_if_ini_active(pyproject)
        _write_toml_section(pyproject, {})
    except ConfigError as e:
        err_console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(2) from e
    except OSError as e:
        err_console.print(f"[red]Error writing {pyproject}: {e}[/red]")
        raise typer.Exit(2) from e
    console.print("[green]Created [tool.behave-runner] section.[/green]")


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Configuration key to set."),
    value: str = typer.Argument(..., help="Value to set."),
) -> None:
    """Set a value in [tool.behave-runner]."""
    if not _KEY_RE.match(key):
        err_console.print(
            "[red]Error: key must contain only letters, numbers, "
            "underscores, dots, or hyphens.[/red]"
        )
        raise typer.Exit(2)

    pyproject = _find_pyproject()
    if pyproject is None:
        err_console.print(
            "[red]Error: no pyproject.toml found. Run this from a project root.[/red]"
        )
        raise typer.Exit(2)

    parsed = _parse_value(value)
    try:
        _warn_if_ini_active(pyproject)
        _set_config_value(pyproject, key, parsed)
    except ConfigError as e:
        err_console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(2) from e
    except OSError as e:
        err_console.print(f"[red]Error writing {pyproject}: {e}[/red]")
        raise typer.Exit(2) from e
    console.print(f"[green]Set {escape(key)} = {escape(value)}[/green]")
