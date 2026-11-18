"""Orchestrator — builds behave commands from RunConfig."""

from __future__ import annotations

import contextlib
import importlib
import os
import re
import signal
import subprocess  # nosec B404
import sys
import warnings
from dataclasses import dataclass, field

from rich.console import Console

from behave_runner.core.deps import is_installed

console = Console(stderr=True)


def _is_package_functional(package: str) -> bool:
    """Check if a package is installed with real code, not just an empty namespace.

    Some packages (e.g. behave-pool) may be installed as empty namespace
    packages with only a ``py.typed`` marker. This function verifies that
    the package contains at least one ``.py`` file in its path.
    """
    if not is_installed(package):
        return False
    mod = sys.modules.get(package)
    if mod is None:
        try:
            mod = importlib.import_module(package)
        except Exception:
            # A broken optional package (SyntaxError, import-time crash)
            # must degrade to "not functional", not propagate a traceback.
            return False
    paths = list(getattr(mod, "__path__", []))
    if not paths:
        return False
    for p in paths:
        try:
            if os.path.isdir(p) and any(f.endswith(".py") for f in os.listdir(p)):
                return True
        except OSError:
            continue
    return False


# Map report format names to their behave formatter scoped names (module:Class).
# Behave 1.2.6 resolves these via load_formatter_class() — it does NOT load
# entry points from importlib.metadata, so we must use scoped names.
_REPORT_FORMATTERS: dict[str, str] = {
    "console": "behave_modern_console_report.formatters.modern:ModernFormatter",
    "json": "behave_modern_json_report.formatter:ModernJSONFormatter",
    "md": "behave_modern_md_report.formatter:BehaveMarkdownFormatter",
    "html": "behave_modern_html_report.formatter:ModernHTMLFormatter",
    "sheets": "behave_modern_sheets_report.xlsx_formatter:XLSXFormatter",
    "file": "behave_modern_file_report.docx_formatter:DOCXFormatter",
}

# Map report format names to their importable package (for dependency check).
_REPORT_PACKAGES: dict[str, str] = {
    "console": "behave_modern_console_report",
    "json": "behave_modern_json_report",
    "md": "behave_modern_md_report",
    "html": "behave_modern_html_report",
    "sheets": "behave_modern_sheets_report",
    "file": "behave_modern_file_report",
}


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
    parallel_scheme: str | None = None
    parallel_balance: str | None = None
    parallel_timing_file: str | None = None
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

        for field_name in (
            "fmt",
            "outfile",
            "shard",
            "parallel_scheme",
            "parallel_balance",
            "parallel_timing_file",
        ):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, str):
                raise ValueError(f"RunConfig.{field_name} must be a string or None")

        if self.outfile == "":
            raise ValueError("RunConfig.outfile cannot be an empty string")
        if self.fmt == "":
            raise ValueError("RunConfig.fmt cannot be an empty string")
        if self.shard == "":
            raise ValueError("RunConfig.shard cannot be an empty string")
        if self.parallel_scheme == "":
            raise ValueError("RunConfig.parallel_scheme cannot be an empty string")
        if self.parallel_balance == "":
            raise ValueError("RunConfig.parallel_balance cannot be an empty string")
        if self.parallel_timing_file == "":
            raise ValueError("RunConfig.parallel_timing_file cannot be an empty string")
        if self.shard is not None:
            validate_shard(self.shard)


def build_behave_command(config: RunConfig) -> list[str]:
    """Build the behave command as a list of strings for subprocess.

    All optional features (parallel, trace, report formatters) are passed
    directly to behave as flags. Behave handles them natively or via
    installed formatter packages.

    Uses "python -m behave" instead of "behave" to ensure the same Python
    interpreter (and its installed packages) is used.
    """
    cmd: list[str] = [sys.executable, "-m", "behave"]
    cmd.extend(config.features)
    for tag in config.tags:
        cmd.extend(["--tags", tag])
    if config.dry_run:
        cmd.append("--dry-run")
    if config.stop_on_failure:
        cmd.append("--stop")
    if config.max_failures is not None and config.max_failures > 0:
        # behave has no --max-fail flag; it can only stop at the first
        # failure. Any value >= 1 maps to --stop, so warn when the user
        # asked for a higher threshold.
        if config.max_failures > 1:
            warnings.warn(
                f"behave does not support --max-fail={config.max_failures}; "
                f"stopping at the first failure instead.",
                stacklevel=2,
            )
        cmd.extend(["--stop"])
    # Note: config.timeout is NOT a behave flag (behave has no --timeout);
    # it is enforced as a subprocess timeout in run().
    for name in config.name:
        cmd.extend(["--name", name])
    if config.no_color:
        cmd.append("--no-color")
    if config.verbose:
        cmd.append("--verbose")

    # Parallel: pass --parallel and related flags to behave.
    # Behave 1.2.6 does not support --parallel natively; it requires
    # behave-pool to register the flag. Only pass it when behave-pool
    # is actually installed with real code (not just an empty namespace).
    if config.parallel is not None and config.parallel > 1:
        if _is_package_functional("behave_pool"):
            cmd.extend(["--parallel", str(config.parallel)])
            if config.parallel_scheme is not None:
                cmd.extend(["--parallel-scheme", config.parallel_scheme])
            if config.parallel_balance is not None:
                cmd.extend(["--parallel-balance", config.parallel_balance])
            if config.parallel_timing_file is not None:
                cmd.extend(["--parallel-timing-file", config.parallel_timing_file])
        else:
            warnings.warn(
                f"--parallel requires behave-pool to be installed; "
                f"ignoring --parallel={config.parallel}.",
                stacklevel=2,
            )
    elif (
        config.parallel_scheme is not None
        or config.parallel_balance is not None
        or config.parallel_timing_file is not None
    ):
        warnings.warn(
            "--parallel-scheme/--parallel-balance/--parallel-timing-file require "
            "--parallel > 1 with behave-pool installed; ignoring.",
            stacklevel=2,
        )

    # Shard: passed via BEHAVE_POOL_SHARD env var (set in _behave_env_vars),
    # not as a CLI flag — behave does not support --shard natively.
    if config.shard is not None and not _is_package_functional("behave_pool"):
        warnings.warn(
            f"--shard requires behave-pool to be installed; ignoring --shard {config.shard}.",
            stacklevel=2,
        )

    # Format: either a report formatter or a behave built-in
    # Only use the entry point name if the package is installed;
    # otherwise fall back to behave's built-in formats.
    if config.fmt is not None:
        formatter = _resolve_formatter(config.fmt)
        fmt_package = _REPORT_PACKAGES.get(config.fmt)
        if formatter is not None and fmt_package is not None:
            if is_installed(fmt_package):
                cmd.extend(["--format", formatter])
            else:
                # Package not installed — pass the raw name through so
                # behave fails with its own "unknown formatter" error if
                # it does not provide one, and warn that the requested
                # report format will not be produced.
                warnings.warn(
                    f"--format {config.fmt} requires {fmt_package}, which is not "
                    f"installed. Install with: pip install "
                    f"behave-runner[report-{config.fmt}]",
                    stacklevel=2,
                )
                cmd.extend(["--format", config.fmt])
        else:
            # Pass through as-is for behave built-in formats (plain, json, etc.)
            cmd.extend(["--format", config.fmt])

    # Output file for the format
    if config.outfile is not None:
        cmd.extend(["--outfile", config.outfile])

    # Trace formatter: add as a second formatter alongside any report format
    # Only when behave-trace is installed; warn otherwise (same graceful
    # degradation contract as --parallel/behave-pool).
    if config.trace or config.ui or config.debug:
        if is_installed("behave_trace"):
            cmd.extend(["--format", "behave_trace:TraceFormatter"])
        else:
            warnings.warn(
                "--trace/--ui/--debug require behave-trace to be installed; "
                "ignoring. Install with: pip install behave-runner[trace]",
                stacklevel=2,
            )

    return cmd


_SHARD_RE = re.compile(r"^(\d+)/(\d+)$")


def validate_shard(shard: str) -> None:
    """Validate a shard string in the format 'i/n' (e.g. '1/3').

    Raises ValueError if the format is invalid or the shard index is out of range.
    """
    match = _SHARD_RE.match(shard)
    if not match:
        raise ValueError(f"Invalid shard format: '{shard}'. Expected i/n (e.g. 1/3).")
    i, n = int(match.group(1)), int(match.group(2))
    if i < 1 or n < 1 or i > n:
        raise ValueError(f"Invalid shard: {shard}. i must be 1..n.")


def report_formatter_package(fmt: str) -> str | None:
    """Return the package that provides a report format, or None."""
    return _REPORT_PACKAGES.get(fmt)


def _resolve_formatter(fmt: str) -> str | None:
    """Resolve a report format name to its behave formatter class path.

    Returns None if the format is not a known report format (in which case
    it's passed through to behave as-is).
    """
    return _REPORT_FORMATTERS.get(fmt)


def _build_env(config: RunConfig) -> dict[str, str]:
    """Build environment variables for behave from config.

    Returns a full env dict (os.environ + behave-specific vars) for
    passing to subprocess.run(env=...).
    """
    env = dict(os.environ)
    env.update(_behave_env_vars(config))
    # Ensure UTF-8 output encoding for formatters that use Unicode (emojis, etc.)
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return env


def _behave_env_vars(config: RunConfig) -> dict[str, str]:
    """Return only the behave-specific environment variables for a config."""
    env: dict[str, str] = {}
    if config.scenario_timeout is not None:
        env["BEHAVE_SCENARIO_TIMEOUT"] = str(config.scenario_timeout)
    # Note: --stop is passed as a native behave CLI flag and config.timeout
    # is enforced as a subprocess timeout in run(); neither is an env var.
    retry_requested = (config.retries is not None and config.retries > 0) or config.flaky_report
    if retry_requested and not is_installed("behave_retry"):
        warnings.warn(
            "--retries/--flaky-report require behave-retry to be installed; "
            "ignoring. Install with: pip install behave-runner[retry]",
            stacklevel=2,
        )
    if config.retries is not None and config.retries > 0:
        env["BEHAVE_RETRY_MAX_RETRIES"] = str(config.retries)
    if config.flaky_report:
        env["BEHAVE_RETRY_FLAKY_REPORT"] = "1"
    if (config.priority_order or config.fail_fast) and not is_installed("behave_priority"):
        warnings.warn(
            "--priority-order/--fail-fast require behave-priority to be installed; "
            "ignoring. Install with: pip install behave-runner[priority]",
            stacklevel=2,
        )
    if config.priority_order:
        env["BEHAVE_PRIORITY_ORDER"] = "1"
    if config.fail_fast:
        env["BEHAVE_PRIORITY_FAIL_FAST"] = "1"
    if config.shard is not None:
        env["BEHAVE_POOL_SHARD"] = config.shard
    return env


def _kill_process_tree(proc: subprocess.Popen[bytes]) -> None:
    """Kill a behave process and its children (parallel workers)."""
    if sys.platform == "win32":
        subprocess.run(  # noqa: S603  # nosec B603 B607
            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
            check=False,
            capture_output=True,
        )
        return
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        with contextlib.suppress(OSError):
            proc.kill()


def _run_behave_subprocess(cmd: list[str], env: dict[str, str], timeout: int | None = None) -> int:
    """Run a behave subprocess command. Return exit code.

    Handles missing executables, OSError subclasses (e.g. PermissionError),
    and a global timeout that kills the whole behave process tree —
    subprocess.run's timeout only kills the direct child, orphaning
    parallel workers spawned by behave-pool.
    """
    try:
        if sys.platform == "win32":
            # New group so taskkill /T can reach the whole tree.
            proc = subprocess.Popen(  # noqa: S603  # nosec B603
                cmd,
                env=env,
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            )
        else:
            proc = subprocess.Popen(  # noqa: S603  # nosec B603
                cmd, env=env, start_new_session=True
            )
    except FileNotFoundError:
        console.print(f"[red]Error: could not start process {cmd[0]!r}[/red]")
        return 2
    except OSError as e:
        console.print(f"[red]Error running behave: {e}[/red]")
        return 2
    try:
        return proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill_process_tree(proc)
        proc.wait()
        console.print(f"[red]Error: behave run timed out after {timeout} seconds.[/red]")
        return 124


def run(config: RunConfig) -> int:
    """Execute behave with the given config. Return exit code.

    All optional features (parallel, trace, report formatters, retries,
    priority) are passed to behave via command-line flags and environment
    variables. Behave handles them natively or via installed packages.

    ``config.timeout`` is a global timeout in seconds for the whole run;
    ``0`` means no timeout. When it expires the behave process is killed
    and the run exits with code 124.
    """
    cmd = build_behave_command(config)
    env = _build_env(config)
    timeout = config.timeout if config.timeout else None
    return _run_behave_subprocess(cmd, env, timeout)
