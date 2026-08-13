"""Init command for behave-runner CLI."""

from __future__ import annotations

import typer

from behave_runner.core.deps import check_optional, run_external


def init_command(
    ctx: typer.Context,
    name: str = typer.Option(..., "--name", help="Project name for the generated structure."),
    args: list[str] = typer.Argument(None, help="Additional arguments for behave-gen."),
) -> None:
    """Initialize a new behave project structure using behave-gen."""
    if not check_optional("gen", "behave_gen", "init"):
        raise typer.Exit(2)

    cmd = ["behave-gen", "init", name]
    cmd.extend(args or [])
    cmd.extend(ctx.args)
    raise typer.Exit(run_external(cmd, "behave-gen", "behave-gen"))
