"""Orchestrator — builds behave commands from RunConfig."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field

from rich.console import Console

from behave_runner.core.deps import check_optional

console = Console()


@dataclass(frozen=True)
class RunConfig:
    """Configuration for a behave run."""

    features: list[str] = field(default_factory=lambda: ["features"])
    tags: list[str] = field(default_factory=list)
    dry_run: bool = False
    stop_on_failure: bool = False
    max_failures: int | None = None
    timeout: int | None = None
    fmt: str | None = None
    outfile: str | None = None
    name: list[str] = field(default_factory=list)
    no_color: bool = False
    verbose: bool = False
    parallel: int | None = None
    shard: str | None = None
    retries: int | None = None
    flaky_report: bool = False
    priority_order: bool = False
    smoke: bool = False
    fail_fast: bool = False
    profile: str | None = None
    scenario_timeout: int | None = None
    ui: bool = False
    debug: bool = False
    trace: bool = False


def build_behave_command(config: RunConfig) -> list[str]:
    """Build the behave command as a list of strings for subprocess."""
    cmd: list[str] = ["behave"]
    cmd.extend(config.features)
    for tag in config.tags:
        cmd.extend(["--tags", tag])
    if config.dry_run:
        cmd.append("--dry-run")
    if config.stop_on_failure:
        cmd.append("--stop")
    if config.max_failures is not None:
        cmd.extend(["--max-failures", str(config.max_failures)])
    if config.timeout is not None:
        cmd.extend(["--timeout", str(config.timeout)])
    if config.fmt is not None:
        cmd.extend(["--format", config.fmt])
    if config.outfile is not None:
        cmd.extend(["--outfile", config.outfile])
    for name in config.name:
        cmd.extend(["--name", name])
    if config.no_color:
        cmd.append("--no-color")
    if config.verbose:
        cmd.append("--verbose")
    return cmd


def run(config: RunConfig) -> int:
    """Execute behave with the given config. Return exit code."""
    if config.ui or config.debug or config.trace:
        return _run_with_trace(config)
    if config.shard is not None:
        return _run_shard(config)
    if config.parallel is not None and config.parallel > 1:
        return _run_parallel(config)
    if config.priority_order or config.fail_fast:
        return _run_with_priority(config)
    return _run_sequential(config)


def _run_sequential(config: RunConfig) -> int:
    """Execute behave sequentially."""
    if config.retries is not None and config.retries > 0:
        return _run_with_retries(config)
    cmd = build_behave_command(config)
    try:
        result = subprocess.run(cmd, check=False)  # noqa: S603
        return result.returncode
    except FileNotFoundError:
        console.print("[red]Error: behave not found. Install with: pip install behave[/red]")
        return 2


def _run_parallel(config: RunConfig) -> int:
    """Execute behave in parallel using behave-pool. Degrades to sequential."""
    if not check_optional("parallel", "behave_pool", "parallel"):
        console.print("[yellow]Falling back to sequential execution.[/yellow]")
        return _run_sequential(config)
    try:
        import behave_pool
    except ImportError:
        console.print("[yellow]Falling back to sequential execution.[/yellow]")
        return _run_sequential(config)
    cmd = build_behave_command(config)
    try:
        result = behave_pool.run_parallel(cmd, workers=config.parallel)
        return int(result)
    except AttributeError:
        console.print(
            "[yellow]behave-pool installed but no run_parallel API. "
            "Falling back to sequential.[/yellow]"
        )
        return _run_sequential(config)
    except FileNotFoundError:
        console.print("[red]Error: behave not found. Install with: pip install behave[/red]")
        return 2


def _run_with_retries(config: RunConfig) -> int:
    """Execute behave with retries using behave-retry. Degrades to no retries."""
    if not check_optional("retry", "behave_retry", "retries"):
        console.print("[yellow]Running without retries (behave-retry not installed).[/yellow]")
        cmd = build_behave_command(config)
        try:
            result = subprocess.run(cmd, check=False)  # noqa: S603
            return result.returncode
        except FileNotFoundError:
            console.print("[red]Error: behave not found. Install with: pip install behave[/red]")
            return 2
    try:
        import behave_retry
    except ImportError:
        console.print("[yellow]Running without retries (behave-retry not installed).[/yellow]")
        cmd = build_behave_command(config)
        try:
            result = subprocess.run(cmd, check=False)  # noqa: S603
            return result.returncode
        except FileNotFoundError:
            console.print("[red]Error: behave not found. Install with: pip install behave[/red]")
            return 2
    cmd = build_behave_command(config)
    try:
        result = behave_retry.run_with_retries(
            cmd, retries=config.retries, flaky_report=config.flaky_report
        )
        return int(result)
    except AttributeError:
        console.print(
            "[yellow]behave-retry installed but no run_with_retries API. "
            "Running without retries.[/yellow]"
        )
        try:
            result = subprocess.run(cmd, check=False)  # noqa: S603
            return result.returncode
        except FileNotFoundError:
            console.print("[red]Error: behave not found. Install with: pip install behave[/red]")
            return 2
    except FileNotFoundError:
        console.print("[red]Error: behave not found. Install with: pip install behave[/red]")
        return 2


def _run_with_priority(config: RunConfig) -> int:
    """Execute behave with priority ordering using behave-priority.

    Degrades to sequential if behave-priority not installed.
    """
    if not check_optional("priority", "behave_priority", "priority-order"):
        console.print(
            "[yellow]Running without priority ordering (behave-priority not installed).[/yellow]"
        )
        return _run_sequential(config)
    try:
        import behave_priority
    except ImportError:
        console.print(
            "[yellow]Running without priority ordering (behave-priority not installed).[/yellow]"
        )
        return _run_sequential(config)
    cmd = build_behave_command(config)
    try:
        result = behave_priority.run_with_priority(
            cmd,
            priority_order=config.priority_order,
            fail_fast=config.fail_fast,
        )
        return int(result)
    except AttributeError:
        console.print(
            "[yellow]behave-priority installed but no run_with_priority API. "
            "Running sequentially.[/yellow]"
        )
        return _run_sequential(config)
    except FileNotFoundError:
        console.print("[red]Error: behave not found. Install with: pip install behave[/red]")
        return 2


def _run_with_trace(config: RunConfig) -> int:
    """Execute behave with trace/debug/ui using behave-trace.

    Degrades to sequential if behave-trace not installed.
    """
    if not check_optional("trace", "behave_trace", "ui"):
        console.print(
            "[yellow]Running without trace/ui/debug (behave-trace not installed).[/yellow]"
        )
        return _run_sequential(config)
    try:
        import behave_trace
    except ImportError:
        console.print(
            "[yellow]Running without trace/ui/debug (behave-trace not installed).[/yellow]"
        )
        return _run_sequential(config)
    cmd = build_behave_command(config)
    try:
        result = behave_trace.run_with_trace(
            cmd,
            ui=config.ui,
            debug=config.debug,
            trace=config.trace,
        )
        return int(result)
    except AttributeError:
        console.print(
            "[yellow]behave-trace installed but no run_with_trace API. "
            "Running sequentially.[/yellow]"
        )
        return _run_sequential(config)
    except FileNotFoundError:
        console.print("[red]Error: behave not found. Install with: pip install behave[/red]")
        return 2


def _run_shard(config: RunConfig) -> int:
    """Execute a shard of tests using behave-pool. Degrades to full run."""
    if not check_optional("parallel", "behave_pool", "shard"):
        console.print("[yellow]Running all scenarios (no sharding).[/yellow]")
        return _run_sequential(config)
    try:
        import behave_pool
    except ImportError:
        console.print("[yellow]Running all scenarios (no sharding).[/yellow]")
        return _run_sequential(config)
    cmd = build_behave_command(config)
    try:
        result = behave_pool.run_shard(cmd, shard=config.shard)
        return int(result)
    except AttributeError:
        console.print(
            "[yellow]behave-pool installed but no run_shard API. Running all scenarios.[/yellow]"
        )
        return _run_sequential(config)
    except FileNotFoundError:
        console.print("[red]Error: behave not found. Install with: pip install behave[/red]")
        return 2
