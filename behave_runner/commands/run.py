"""Run command for behave-runner CLI."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import typer
from rich.console import Console

from behave_runner.core.config import load_config, load_profile
from behave_runner.core.orchestrator import RunConfig, run
from behave_runner.exceptions import ConfigError

_SHARD_RE = re.compile(r"^(\d+)/(\d+)$")


def run_command(
    features: list[Path] = typer.Argument(
        default=None,
        help="Paths to feature files or directories.",
    ),
    tags: list[str] = typer.Option([], "--tags", "-t", help="Filter by tags."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Don't execute steps."),
    stop_on_failure: bool = typer.Option(False, "--stop-on-failure", help="Stop on first failure."),
    max_fail: int | None = typer.Option(
        None, "--max-fail", help="Maximum failures before stopping."
    ),
    timeout: int | None = typer.Option(None, "--timeout", help="Global timeout in seconds."),
    fmt: str | None = typer.Option(None, "--format", help="Output format."),
    output: str | None = typer.Option(None, "--output", help="Output file path."),
    parallel: int | None = typer.Option(
        None, "--parallel", "-n", help="Number of parallel processes (uses behave-pool)."
    ),
    shard: str | None = typer.Option(
        None, "--shard", help="Shard to run in CI (format: i/n, e.g. 1/3)."
    ),
    retries: int | None = typer.Option(
        None, "--retries", help="Number of retries for failed scenarios (uses behave-retry)."
    ),
    flaky_report: bool = typer.Option(
        False, "--flaky-report", help="Generate flakiness report (requires --retries)."
    ),
    priority_order: bool = typer.Option(
        False, "--priority-order", help="Run scenarios in priority order (uses behave-priority)."
    ),
    smoke: bool = typer.Option(
        False, "--smoke", help="Run only @smoke scenarios (uses behave-priority)."
    ),
    fail_fast: bool = typer.Option(
        False, "--fail-fast", help="Stop on first failure with priority (uses behave-priority)."
    ),
    profile: str | None = typer.Option(
        None, "--profile", help="Load a configuration profile from pyproject.toml."
    ),
    scenario_timeout: int | None = typer.Option(
        None, "--scenario-timeout", help="Per-scenario timeout in seconds (uses behave-kit)."
    ),
    ui: bool = typer.Option(False, "--ui", help="Launch behave-trace web dashboard."),
    debug: bool = typer.Option(
        False, "--debug", help="Enable interactive debugging (uses behave-trace)."
    ),
    trace: bool = typer.Option(
        False, "--trace", help="Enable trace viewer for post-run analysis (uses behave-trace)."
    ),
) -> None:
    """Run behave tests with native and optional flags."""
    if smoke:
        tags = [*tags, "@smoke"]

    if flaky_report and (retries is None or retries == 0):
        console_err = Console()
        console_err.print("[yellow]--flaky-report requires --retries > 0. Ignoring.[/yellow]")
        flaky_report = False

    if shard is not None:
        match = _SHARD_RE.match(shard)
        if not match:
            console_err = Console()
            console_err.print(
                f"[red]Invalid shard format: '{shard}'. Expected i/n (e.g. 1/3).[/red]"
            )
            raise typer.Exit(2)
        i, n = int(match.group(1)), int(match.group(2))
        if i < 1 or n < 1 or i > n:
            console_err = Console()
            console_err.print(f"[red]Invalid shard: {shard}. i must be 1..n.[/red]")
            raise typer.Exit(2)

    feature_paths = [str(f) for f in features] if features else ["features"]
    load_config()

    profile_config: dict[str, Any] = {}
    if profile is not None:
        try:
            profile_config = load_profile(profile)
        except ConfigError as e:
            console_err = Console()
            console_err.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(2) from e

    p_fmt = fmt if fmt is not None else profile_config.get("format")
    p_output = output if output is not None else profile_config.get("output")
    p_timeout = timeout if timeout is not None else profile_config.get("timeout")
    p_tags = tags if tags else profile_config.get("tags", [])

    run_config = RunConfig(
        features=feature_paths,
        tags=p_tags,
        dry_run=dry_run,
        stop_on_failure=stop_on_failure,
        max_failures=max_fail,
        timeout=p_timeout,
        fmt=p_fmt,
        outfile=p_output,
        parallel=parallel,
        shard=shard,
        retries=retries,
        flaky_report=flaky_report,
        priority_order=priority_order,
        smoke=smoke,
        fail_fast=fail_fast,
        profile=profile,
        scenario_timeout=scenario_timeout,
        ui=ui,
        debug=debug,
        trace=trace,
    )
    exit_code = run(run_config)
    raise typer.Exit(exit_code)
