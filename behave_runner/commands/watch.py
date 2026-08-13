"""Watch command for behave-runner CLI."""

from __future__ import annotations

import fnmatch
from collections.abc import Callable
from pathlib import Path

import typer
from rich.console import Console

from behave_runner.core.config import load_profile
from behave_runner.core.orchestrator import RunConfig, run, validate_shard
from behave_runner.core.watcher import FileWatcher
from behave_runner.exceptions import ConfigError

console = Console()

_DEFAULT_PATHS = [
    Path("features"),
    Path("features/steps"),
    Path("environment.py"),
    Path("behave.ini"),
    Path("pyproject.toml"),
]


def _make_callback(
    feature_paths: list[str],
    tags: list[str],
    pattern: str | None,
    config_overrides: dict[str, object],
) -> Callable[[list[Path]], None]:
    """Create a callback that re-runs tests on file changes."""

    def on_change(changed: list[Path]) -> None:
        if pattern:
            matched = [p for p in changed if fnmatch.fnmatch(p.name, pattern)]
            if not matched:
                return
        console.print(f"\n[cyan]Change detected: {', '.join(str(p) for p in changed)}[/cyan]")
        console.print("[cyan]Re-running tests...[/cyan]")
        try:
            config = RunConfig(
                features=feature_paths,
                tags=tags,
                **config_overrides,  # type: ignore[arg-type]
            )
        except (ValueError, TypeError) as e:
            console.print(f"[red]Error: {e}[/red]")
            return
        exit_code = run(config)
        if exit_code == 0:
            console.print("[green]All tests passed.[/green]")
        else:
            console.print(f"[red]Tests failed (exit {exit_code}).[/red]")

    return on_change


def watch_command(
    features: list[str] = typer.Argument(
        default=None,
        help="Feature paths to watch and run.",
    ),
    tags: list[str] = typer.Option([], "--tags", "-t", help="Filter by tags."),
    debounce: int = typer.Option(500, "--debounce", help="Debounce time in milliseconds."),
    pattern: str | None = typer.Option(
        None, "--pattern", help="Glob pattern to filter watched files."
    ),
    profile: str | None = typer.Option(
        None, "--profile", help="Load a configuration profile from pyproject.toml."
    ),
    retries: int | None = typer.Option(
        None, "--retries", help="Number of retries for failed scenarios."
    ),
    parallel: int | None = typer.Option(
        None, "--parallel", "-n", help="Number of parallel processes."
    ),
    fmt: str | None = typer.Option(None, "--format", help="Output format."),
    ui: bool = typer.Option(False, "--ui", help="Use behave-trace UI mode if available."),
    debug: bool = typer.Option(False, "--debug", help="Enable debug tracing."),
    trace: bool = typer.Option(False, "--trace", help="Enable trace viewer."),
    priority_order: bool = typer.Option(
        False, "--priority-order", help="Run scenarios in priority order."
    ),
    fail_fast: bool = typer.Option(
        False, "--fail-fast", help="Stop on first failure with priority."
    ),
    scenario_timeout: int | None = typer.Option(
        None, "--scenario-timeout", help="Per-scenario timeout in seconds."
    ),
) -> None:
    """Watch for file changes and re-run tests automatically."""
    if debounce < 0:
        console.print("[red]Error: --debounce must be a non-negative integer.[/red]")
        raise typer.Exit(2)

    profile_config: dict[str, object] = {}
    if profile is not None:
        try:
            profile_config = load_profile(profile)
        except ConfigError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(2) from e

    # Features: CLI takes priority, then profile, then default
    if features:
        feature_paths = list(features)
    else:
        profile_features = profile_config.get("features", [])
        feature_paths = (
            list(profile_features)
            if isinstance(profile_features, list) and profile_features
            else ["features"]
        )

    # Tags: merge CLI tags with profile tags
    profile_tags = profile_config.get("tags", [])
    p_tags_list = profile_tags if isinstance(profile_tags, list) else []
    tags = [*tags, *p_tags_list] if (tags or p_tags_list) else []

    # Smoke from profile adds @smoke tag (same as run command)
    profile_smoke = profile_config.get("smoke", False)
    if profile_smoke and "@smoke" not in tags:
        tags = [*tags, "@smoke"]

    watch_paths = [Path(p) for p in feature_paths]
    watch_paths.extend(p for p in _DEFAULT_PATHS if p not in watch_paths)

    # Build config overrides from CLI options (and optionally profile)
    config_overrides: dict[str, object] = {
        "ui": ui,
        "debug": debug,
        "trace": trace,
        "priority_order": priority_order,
        "fail_fast": fail_fast,
    }
    if retries is not None:
        config_overrides["retries"] = retries
    if parallel is not None:
        config_overrides["parallel"] = parallel
    if fmt is not None:
        config_overrides["fmt"] = fmt
    if scenario_timeout is not None:
        config_overrides["scenario_timeout"] = scenario_timeout

    # Merge profile values (CLI takes priority)
    # Note: "format" in profile maps to "fmt" in RunConfig
    if profile_config:
        for key in (
            "retries",
            "parallel",
            "scenario_timeout",
            "timeout",
            "parallel_scheme",
            "parallel_balance",
            "parallel_timing_file",
            "shard",
        ):
            if key not in config_overrides and key in profile_config:
                config_overrides[key] = profile_config[key]
        if "max_failures" not in config_overrides:
            if "max_failures" in profile_config:
                config_overrides["max_failures"] = profile_config["max_failures"]
            elif "max_fail" in profile_config:
                config_overrides["max_failures"] = profile_config["max_fail"]
        if "fmt" not in config_overrides and "format" in profile_config:
            config_overrides["fmt"] = profile_config["format"]
        if "outfile" not in config_overrides and "output" in profile_config:
            config_overrides["outfile"] = profile_config["output"]
        # name: list filter from profile (no CLI equivalent on watch command)
        p_name = profile_config.get("name", [])
        if isinstance(p_name, list) and p_name:
            config_overrides["name"] = p_name
        for key in ("ui", "debug", "trace", "priority_order", "fail_fast", "flaky_report"):
            if key in profile_config and profile_config[key]:
                config_overrides[key] = True
        # Profile-only settings (no CLI equivalent on watch command)
        for key in ("dry_run", "stop_on_failure", "no_color", "verbose"):
            if key in profile_config and profile_config[key]:
                config_overrides[key] = True

        # Validate flaky_report: requires retries > 0 (same as run.py)
        p_flaky = config_overrides.get("flaky_report", False)
        p_retries = config_overrides.get("retries")
        if p_flaky and (p_retries is None or p_retries == 0):
            console.print("[yellow]--flaky-report requires --retries > 0. Ignoring.[/yellow]")
            config_overrides.pop("flaky_report", None)

        # Validate shard format (same as run.py)
        p_shard = config_overrides.get("shard")
        if p_shard is not None:
            if not isinstance(p_shard, str):
                console.print(
                    f"[red]Invalid shard: must be a string like '1/3', got {p_shard!r}[/red]"
                )
                raise typer.Exit(2)
            try:
                validate_shard(p_shard)
            except ValueError as e:
                console.print(f"[red]{e}[/red]")
                raise typer.Exit(2) from e

    on_change = _make_callback(feature_paths, tags, pattern, config_overrides)
    watcher = FileWatcher(watch_paths, on_change, debounce_ms=debounce)

    console.print("[cyan]Watching for changes... (Ctrl+C to stop)[/cyan]")
    console.print(f"[cyan]Paths: {', '.join(str(p) for p in watch_paths)}[/cyan]")

    try:
        watcher.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Watch stopped.[/yellow]")
        raise typer.Exit(0) from None
