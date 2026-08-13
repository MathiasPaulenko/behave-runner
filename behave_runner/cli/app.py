"""CLI app for behave-runner."""

from __future__ import annotations

import typer

from behave_runner import __version__
from behave_runner.commands.config_cmd import config_app
from behave_runner.commands.doctor import doctor_command
from behave_runner.commands.format_cmd import format_command
from behave_runner.commands.generate import generate_app
from behave_runner.commands.impact import impact_command
from behave_runner.commands.init import init_command
from behave_runner.commands.lint import lint_command
from behave_runner.commands.list_cmd import list_command
from behave_runner.commands.open_cmd import open_command
from behave_runner.commands.record import record_command
from behave_runner.commands.report import report_app
from behave_runner.commands.run import run_command
from behave_runner.commands.select import select_command
from behave_runner.commands.steps import steps_app
from behave_runner.commands.trace import trace_app
from behave_runner.commands.watch import watch_command

app = typer.Typer(
    name="behave-runner",
    help="A unified CLI for the Behave BDD ecosystem.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


def version_callback(value: bool) -> None:
    if value:
        print(__version__)
        raise typer.Exit


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """behave-runner — A unified CLI for the Behave BDD ecosystem."""
    pass


_PASSTHROUGH_CTX = {"allow_extra_args": True, "ignore_unknown_options": True}

app.command(name="run")(run_command)
app.command(name="select")(select_command)
app.command(name="list")(list_command)
app.command(name="format", context_settings=_PASSTHROUGH_CTX)(format_command)
app.command(name="lint", context_settings=_PASSTHROUGH_CTX)(lint_command)
app.command(name="doctor", context_settings=_PASSTHROUGH_CTX)(doctor_command)
app.command(name="init", context_settings=_PASSTHROUGH_CTX)(init_command)
app.add_typer(report_app, name="report")
app.add_typer(generate_app, name="generate")
app.add_typer(trace_app, name="trace")
app.command(name="watch")(watch_command)
app.command(name="impact")(impact_command)
app.add_typer(steps_app, name="steps")
app.command(name="record")(record_command)
app.command(name="open")(open_command)
app.add_typer(config_app, name="config")
