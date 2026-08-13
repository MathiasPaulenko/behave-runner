"""Watch command for behave-runner CLI."""

from __future__ import annotations

import fnmatch
from collections.abc import Callable
from pathlib import Path

import typer
from rich.console import Console

from behave_runner.core.orchestrator import RunConfig, run
from behave_runner.core.watcher import FileWatcher

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
        config = RunConfig(
            features=feature_paths,
            tags=tags,
            **config_overrides,  # type: ignore[arg-type]
        )
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

    feature_paths = features if features else ["features"]
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

    if profile is not None:
        from behave_runner.core.config import load_profile
        from behave_runner.exceptions import ConfigError

        try:
            profile_config = load_profile(profile)
        except ConfigError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(2) from e

        # Merge profile values (CLI takes priority)
        for key in ("retries", "parallel", "fmt", "scenario_timeout"):
            if key not in config_overrides and key in profile_config:
                config_overrides[key] = profile_config[key]
        for key in ("ui", "debug", "trace", "priority_order", "fail_fast"):
            if key in profile_config and profile_config[key]:
                config_overrides[key] = True

    on_change = _make_callback(feature_paths, tags, pattern, config_overrides)
    watcher = FileWatcher(watch_paths, on_change, debounce_ms=debounce)

    console.print("[cyan]Watching for changes... (Ctrl+C to stop)[/cyan]")
    console.print(f"[cyan]Paths: {', '.join(str(p) for p in watch_paths)}[/cyan]")

    try:
        watcher.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Watch stopped.[/yellow]")
        raise typer.Exit(0) from None
