"""Orchestrator — builds behave commands from RunConfig."""

from __future__ import annotations

import os
import subprocess  # nosec B404
from collections.abc import Callable
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
    fail_fast: bool = False
    scenario_timeout: int | None = None
    ui: bool = False
    debug: bool = False
    trace: bool = False

    def __post_init__(self) -> None:
        """Validate field types and values."""
        for field_name in ("features", "tags", "name"):
            value = getattr(self, field_name)
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                raise ValueError(f"RunConfig.{field_name} must be a list of strings")

        for field_name in ("parallel", "retries", "max_failures", "timeout", "scenario_timeout"):
            value = getattr(self, field_name)
            if value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"RunConfig.{field_name} must be an integer or None")
            if value < 0:
                raise ValueError(f"RunConfig.{field_name} must be a non-negative integer")

        # parallel must be >= 1 if set (0 is meaningless — it silently falls back)
        if self.parallel is not None and self.parallel < 1:
            raise ValueError("RunConfig.parallel must be >= 1")

        for field_name in (
            "dry_run",
            "stop_on_failure",
            "flaky_report",
            "priority_order",
            "fail_fast",
            "no_color",
            "verbose",
            "ui",
            "debug",
            "trace",
        ):
            if not isinstance(getattr(self, field_name), bool):
                raise ValueError(f"RunConfig.{field_name} must be a boolean")

        for field_name in ("fmt", "outfile", "shard"):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, str):
                raise ValueError(f"RunConfig.{field_name} must be a string or None")

        if self.outfile == "":
            raise ValueError("RunConfig.outfile cannot be an empty string")
        if self.fmt == "":
            raise ValueError("RunConfig.fmt cannot be an empty string")
        if self.shard == "":
            raise ValueError("RunConfig.shard cannot be an empty string")


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


def _build_env(config: RunConfig) -> dict[str, str]:
    """Build environment variables for behave from config.

    Returns a full env dict (os.environ + behave-specific vars) for
    passing to subprocess.run(env=...).
    """
    env = dict(os.environ)
    env.update(_behave_env_vars(config))
    return env


def _behave_env_vars(config: RunConfig) -> dict[str, str]:
    """Return only the behave-specific environment variables for a config."""
    env: dict[str, str] = {}
    if config.scenario_timeout is not None:
        env["BEHAVE_SCENARIO_TIMEOUT"] = str(config.scenario_timeout)
    if config.timeout is not None:
        env["BEHAVE_TIMEOUT"] = str(config.timeout)
    if config.max_failures is not None:
        env["BEHAVE_MAX_FAILURES"] = str(config.max_failures)
    return env


def _run_behave_subprocess(cmd: list[str], env: dict[str, str]) -> int:
    """Run a behave subprocess command. Return exit code.

    Handles FileNotFoundError when behave is not installed and other
    OSError subclasses (e.g. PermissionError) gracefully.
    """
    try:
        result = subprocess.run(cmd, check=False, env=env)  # noqa: S603  # nosec B603
        return result.returncode
    except FileNotFoundError:
        console.print("[red]Error: behave not found. Install with: pip install behave[/red]")
        return 2
    except OSError as e:
        console.print(f"[red]Error running behave: {e}[/red]")
        return 2


def _try_optional(
    feature: str,
    package: str,
    flag: str,
    fallback_msg: str,
    fallback: Callable[[], int],
    api_call: Callable[[], int],
) -> int:
    """Try an optional dependency API with graceful fallback.

    Args:
        feature: Extra name for install hint.
        package: Importable module name.
        flag: CLI flag name for warning message.
        fallback_msg: Message shown when the dependency is unavailable.
        fallback: Function to call when the dependency is unavailable.
        api_call: Function that calls the optional API.

    Returns:
        Exit code from the API call or fallback.
    """
    if not check_optional(feature, package, flag):
        console.print(f"[yellow]{fallback_msg}[/yellow]")
        return fallback()
    try:
        return api_call()
    except ImportError:
        console.print(f"[yellow]{fallback_msg}[/yellow]")
        return fallback()
    except AttributeError:
        console.print(f"[yellow]{package} installed but API mismatch. Using fallback.[/yellow]")
        return fallback()
    except FileNotFoundError:
        console.print(
            f"[red]Error: {package.replace('_', '-')} not found. "
            f"Install with: pip install behave-runner[{feature}][/red]"
        )
        return 2
    except Exception as e:  # noqa: BLE001
        console.print(f"[yellow]{package} raised {type(e).__name__}: {e}. Using fallback.[/yellow]")
        return fallback()


def run(config: RunConfig) -> int:
    """Execute behave with the given config. Return exit code."""
    behave_vars = _behave_env_vars(config)
    saved = {k: os.environ.get(k) for k in behave_vars}
    os.environ.update(behave_vars)
    try:
        if config.ui or config.debug or config.trace:
            return _run_with_trace(config)
        if config.shard is not None:
            return _run_shard(config)
        if config.parallel is not None and config.parallel > 1:
            return _run_parallel(config)
        if config.priority_order or config.fail_fast:
            return _run_with_priority(config)
        return _run_sequential(config)
    finally:
        for key, old_value in saved.items():
            if old_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old_value


def _run_sequential(config: RunConfig) -> int:
    """Execute behave sequentially."""
    if config.retries is not None and config.retries > 0:
        return _run_with_retries(config)
    cmd = build_behave_command(config)
    env = _build_env(config)
    return _run_behave_subprocess(cmd, env)


def _run_parallel(config: RunConfig) -> int:
    """Execute behave in parallel using behave-pool. Degrades to sequential."""
    cmd = build_behave_command(config)

    def _api() -> int:
        import behave_pool

        result = behave_pool.run_parallel(cmd, workers=config.parallel)
        return int(result)

    return _try_optional(
        "parallel",
        "behave_pool",
        "parallel",
        "Falling back to sequential execution.",
        lambda: _run_sequential(config),
        _api,
    )


def _run_with_retries(config: RunConfig) -> int:
    """Execute behave with retries using behave-retry. Degrades to no retries."""
    cmd = build_behave_command(config)
    env = _build_env(config)

    def _fallback() -> int:
        return _run_behave_subprocess(cmd, env)

    def _api() -> int:
        import behave_retry

        result = behave_retry.run_with_retries(
            cmd, retries=config.retries, flaky_report=config.flaky_report
        )
        return int(result)

    return _try_optional(
        "retry",
        "behave_retry",
        "retries",
        "Running without retries (behave-retry not installed).",
        _fallback,
        _api,
    )


def _run_with_priority(config: RunConfig) -> int:
    """Execute behave with priority ordering using behave-priority.

    Degrades to sequential if behave-priority not installed.
    """
    cmd = build_behave_command(config)

    def _api() -> int:
        import behave_priority

        result = behave_priority.run_with_priority(
            cmd,
            priority_order=config.priority_order,
            fail_fast=config.fail_fast,
        )
        return int(result)

    return _try_optional(
        "priority",
        "behave_priority",
        "priority-order",
        "Running without priority ordering (behave-priority not installed).",
        lambda: _run_sequential(config),
        _api,
    )


def _run_with_trace(config: RunConfig) -> int:
    """Execute behave with trace/debug/ui using behave-trace.

    Degrades to sequential if behave-trace not installed.
    """
    cmd = build_behave_command(config)

    def _api() -> int:
        import behave_trace

        result = behave_trace.run_with_trace(
            cmd,
            ui=config.ui,
            debug=config.debug,
            trace=config.trace,
        )
        return int(result)

    return _try_optional(
        "trace",
        "behave_trace",
        "ui",
        "Running without trace/ui/debug (behave-trace not installed).",
        lambda: _run_sequential(config),
        _api,
    )


def _run_shard(config: RunConfig) -> int:
    """Execute a shard of tests using behave-pool. Degrades to full run."""
    cmd = build_behave_command(config)

    def _api() -> int:
        import behave_pool

        result = behave_pool.run_shard(cmd, shard=config.shard)
        return int(result)

    return _try_optional(
        "parallel",
        "behave_pool",
        "shard",
        "Running all scenarios (no sharding).",
        lambda: _run_sequential(config),
        _api,
    )
