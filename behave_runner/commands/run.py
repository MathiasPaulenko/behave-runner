"""Run command for behave-runner CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer
from rich.console import Console

from behave_runner.core.config import load_profile
from behave_runner.core.orchestrator import RunConfig, run, validate_shard
from behave_runner.exceptions import ConfigError

console_err = Console()


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
    parallel_scheme: str | None = typer.Option(
        None, "--parallel-scheme", help="Parallel distribution scheme (e.g. scenario, feature)."
    ),
    parallel_balance: str | None = typer.Option(
        None, "--parallel-balance", help="Load balancing strategy (e.g. lpt, round)."
    ),
    parallel_timing_file: str | None = typer.Option(
        None, "--parallel-timing-file", help="Timing file for LPT load balancing."
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
        False, "--smoke", help="Run only @smoke scenarios (adds @smoke tag filter)."
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
        console_err.print("[yellow]--flaky-report requires --retries > 0. Ignoring.[/yellow]")
        flaky_report = False

    profile_config: dict[str, Any] = {}
    if profile is not None:
        try:
            profile_config = load_profile(profile)
        except ConfigError as e:
            console_err.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(2) from e

    # Merge shard from profile, validate it
    p_shard = shard if shard is not None else profile_config.get("shard")
    if p_shard is not None:
        if not isinstance(p_shard, str):
            console_err.print(
                f"[red]Invalid shard: must be a string like '1/3', got {p_shard!r}[/red]"
            )
            raise typer.Exit(2)
        try:
            validate_shard(p_shard)
        except ValueError as e:
            console_err.print(f"[red]{e}[/red]")
            raise typer.Exit(2) from e

    # Features: CLI takes priority, then profile, then default
    if features:
        feature_paths = [str(f) for f in features]
    else:
        profile_features = profile_config.get("features", [])
        feature_paths = profile_features if profile_features else ["features"]

    # Smoke from profile adds @smoke tag (same as CLI --smoke)
    profile_smoke = profile_config.get("smoke", False)
    if profile_smoke and "@smoke" not in tags:
        tags = [*tags, "@smoke"]

    # Tags: merge CLI tags (including --smoke) with profile tags
    profile_tags = profile_config.get("tags", [])
    p_tags = [*tags, *profile_tags] if (tags or profile_tags) else []

    # Name: only from profile (no CLI --name option on run command)
    p_name = profile_config.get("name", [])

    p_fmt = fmt if fmt is not None else profile_config.get("format")
    p_output = output if output is not None else profile_config.get("output")
    p_timeout = timeout if timeout is not None else profile_config.get("timeout")
    p_parallel = parallel if parallel is not None else profile_config.get("parallel")
    p_parallel_scheme = (
        parallel_scheme if parallel_scheme is not None else profile_config.get("parallel_scheme")
    )
    p_parallel_balance = (
        parallel_balance if parallel_balance is not None else profile_config.get("parallel_balance")
    )
    p_parallel_timing_file = (
        parallel_timing_file
        if parallel_timing_file is not None
        else profile_config.get("parallel_timing_file")
    )
    p_retries = retries if retries is not None else profile_config.get("retries")
    p_dry_run = dry_run or profile_config.get("dry_run", False)
    p_stop = stop_on_failure or profile_config.get("stop_on_failure", False)
    p_scenario_timeout = (
        scenario_timeout if scenario_timeout is not None else profile_config.get("scenario_timeout")
    )
    p_priority = priority_order or profile_config.get("priority_order", False)
    p_fail_fast = fail_fast or profile_config.get("fail_fast", False)
    p_flaky = flaky_report or profile_config.get("flaky_report", False)
    p_max_fail = (
        max_fail
        if max_fail is not None
        else profile_config.get("max_failures", profile_config.get("max_fail"))
    )

    # Re-check flaky_report after profile merge: profile may set retries=0
    if p_flaky and (p_retries is None or p_retries == 0):
        console_err.print("[yellow]--flaky-report requires --retries > 0. Ignoring.[/yellow]")
        p_flaky = False
    p_no_color = profile_config.get("no_color", False)
    p_verbose = profile_config.get("verbose", False)
    p_ui = ui or profile_config.get("ui", False)
    p_debug = debug or profile_config.get("debug", False)
    p_trace = trace or profile_config.get("trace", False)

    try:
        run_config = RunConfig(
            features=feature_paths,
            tags=p_tags,
            dry_run=p_dry_run,
            stop_on_failure=p_stop,
            max_failures=p_max_fail,
            timeout=p_timeout,
            fmt=p_fmt,
            outfile=p_output,
            name=p_name,
            no_color=p_no_color,
            verbose=p_verbose,
            parallel=p_parallel,
            shard=p_shard,
            parallel_scheme=p_parallel_scheme,
            parallel_balance=p_parallel_balance,
            parallel_timing_file=p_parallel_timing_file,
            retries=p_retries,
            flaky_report=p_flaky,
            priority_order=p_priority,
            fail_fast=p_fail_fast,
            scenario_timeout=p_scenario_timeout,
            ui=p_ui,
            debug=p_debug,
            trace=p_trace,
        )
    except (ValueError, TypeError) as e:
        console_err.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(2) from e

    exit_code = run(run_config)
    raise typer.Exit(exit_code)
