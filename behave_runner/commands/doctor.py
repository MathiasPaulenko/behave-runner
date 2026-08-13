"""Doctor command for behave-runner CLI."""

from __future__ import annotations

import typer

from behave_runner.core.deps import check_optional, run_external


def doctor_command(
    ctx: typer.Context,
    args: list[str] = typer.Argument(None, help="Arguments to pass to behave-doctor."),
) -> None:
    """Run behave-doctor to diagnose and fix common issues."""
    if not check_optional("doctor", "behave_doctor", "doctor"):
        raise typer.Exit(2)

    all_args = (args or []) + ctx.args
    raise typer.Exit(run_external(["behave-doctor", *all_args], "behave-doctor", "behave-doctor"))
