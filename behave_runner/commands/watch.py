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
    use_ui: bool,
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
            ui=use_ui,
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
    ui: bool = typer.Option(False, "--ui", help="Use behave-trace UI mode if available."),
) -> None:
    """Watch for file changes and re-run tests automatically."""
    if debounce < 0:
        console.print("[red]Error: --debounce must be a non-negative integer.[/red]")
        raise typer.Exit(2)

    feature_paths = features if features else ["features"]
    watch_paths = [Path(p) for p in feature_paths]
    watch_paths.extend(p for p in _DEFAULT_PATHS if p not in watch_paths)

    on_change = _make_callback(feature_paths, tags, pattern, ui)
    watcher = FileWatcher(watch_paths, on_change, debounce_ms=debounce)

    console.print("[cyan]Watching for changes... (Ctrl+C to stop)[/cyan]")
    console.print(f"[cyan]Paths: {', '.join(str(p) for p in watch_paths)}[/cyan]")

    try:
        watcher.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Watch stopped.[/yellow]")
        raise typer.Exit(0) from None
