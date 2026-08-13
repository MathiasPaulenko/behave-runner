"""Format command for behave-runner CLI."""

from __future__ import annotations

import typer

from behave_runner.core.deps import check_optional, run_external


def format_command(
    ctx: typer.Context,
    args: list[str] = typer.Argument(None, help="Arguments to pass to behave-format."),
    check: bool = typer.Option(False, "--check", help="Check only, don't modify files."),
    diff: bool = typer.Option(False, "--diff", help="Show diff of changes."),
) -> None:
    """Run behave-format to format feature files."""
    if not check_optional("format", "behave_format", "format"):
        raise typer.Exit(2)

    cmd = ["behave-format"]
    if check:
        cmd.append("--check")
    if diff:
        cmd.append("--diff")
    cmd.extend(args or [])
    cmd.extend(ctx.args)
    raise typer.Exit(run_external(cmd, "behave-format", "behave-format"))
