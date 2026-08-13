"""Lint command for behave-runner CLI."""

from __future__ import annotations

import typer

from behave_runner.core.deps import check_optional, run_external


def lint_command(
    ctx: typer.Context,
    args: list[str] = typer.Argument(None, help="Arguments to pass to behave-lint."),
) -> None:
    """Run behave-lint static analysis on features."""
    if not check_optional("lint", "behave_lint", "lint"):
        raise typer.Exit(2)

    cmd = [*args] if args else []
    cmd.extend(ctx.args)
    raise typer.Exit(run_external(["behave-lint", *cmd], "behave-lint", "behave-lint"))
