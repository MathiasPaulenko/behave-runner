"""Trace command for behave-runner CLI."""

from __future__ import annotations

import typer
from rich.console import Console

from behave_runner.core.deps import check_optional, run_external

console = Console()

trace_app = typer.Typer(
    name="trace",
    help="Trace viewer using behave-trace.",
    no_args_is_help=True,
)


def _run_behave_trace(subcommand: str, args: list[str]) -> None:
    """Delegate to behave-trace <subcommand> via subprocess."""
    if not check_optional("trace", "behave_trace", "trace"):
        raise typer.Exit(2)
    cmd = ["behave-trace", subcommand, *args]
    raise typer.Exit(run_external(cmd, "behave-trace", "behave-trace"))


@trace_app.command(name="show")
def trace_show(
    args: list[str] = typer.Argument(None, help="Arguments to pass to behave-trace show."),
) -> None:
    """Show trace viewer for post-run analysis."""
    _run_behave_trace("show", args or [])


@trace_app.command(name="serve")
def trace_serve(
    args: list[str] = typer.Argument(None, help="Arguments to pass to behave-trace serve."),
) -> None:
    """Serve trace viewer as a web dashboard."""
    _run_behave_trace("serve", args or [])
