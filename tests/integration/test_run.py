"""Integration tests for behave-runner run command."""

from __future__ import annotations

import importlib.util
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from behave_runner.cli.app import app

runner = CliRunner()

FIXTURE = "tests/fixtures/minimal/features"
PRIORITY_FIXTURE = "tests/fixtures/priority/features"


def _has_formatter(pkg: str) -> bool:
    """Check if a formatter package is installed."""
    return importlib.util.find_spec(pkg) is not None


# ---------------------------------------------------------------------------
# Real execution tests
# ---------------------------------------------------------------------------


def test_run_minimal() -> None:
    """Run minimal fixture and verify exit code 0."""
    result = runner.invoke(app, ["run", FIXTURE])
    assert result.exit_code == 0


def test_run_dry_run() -> None:
    """--dry-run executes without running steps."""
    result = runner.invoke(app, ["run", "--dry-run", FIXTURE])
    assert result.exit_code == 0


def test_run_tags_nonexistent() -> None:
    """--tags with nonexistent tag matches 0 scenarios (not a failure)."""
    result = runner.invoke(app, ["run", "--tags", "@nonexistent", FIXTURE])
    assert result.exit_code == 0


def test_run_tags_smoke() -> None:
    """--tags=@smoke filters to only smoke scenarios."""
    result = runner.invoke(app, ["run", "--tags=@smoke", PRIORITY_FIXTURE])
    assert result.exit_code == 0


def test_run_smoke_flag() -> None:
    """--smoke adds @smoke tag filter."""
    result = runner.invoke(app, ["run", "--smoke", PRIORITY_FIXTURE])
    assert result.exit_code == 0


def test_run_stop_on_failure() -> None:
    """--stop-on-failure flag is accepted."""
    result = runner.invoke(app, ["run", "--stop-on-failure", FIXTURE])
    assert result.exit_code == 0


def test_run_scenario_timeout() -> None:
    """--scenario-timeout is accepted."""
    result = runner.invoke(app, ["run", "--scenario-timeout", "5", FIXTURE])
    assert result.exit_code == 0


def test_run_timeout() -> None:
    """--timeout is accepted and sets timeout in RunConfig."""
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["run", "--timeout", "10", FIXTURE])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert config.timeout == 10


def test_run_max_fail() -> None:
    """--max-fail is accepted."""
    result = runner.invoke(app, ["run", "--max-fail", "3", FIXTURE])
    assert result.exit_code == 0


def test_run_format_json() -> None:
    """--format json produces a JSON report."""
    result = runner.invoke(
        app, ["run", "--format", "json", "--output", "reports/test_run.json", FIXTURE]
    )
    assert result.exit_code == 0


@pytest.mark.skipif(
    not _has_formatter("behave_modern_console_report"),
    reason="behave-modern-console-report not installed",
)
def test_run_format_console() -> None:
    """--format console produces modern console output."""
    result = runner.invoke(app, ["run", "--format", "console", FIXTURE])
    assert result.exit_code == 0


@pytest.mark.skipif(
    not _has_formatter("behave_modern_html_report"),
    reason="behave-modern-html-report not installed",
)
def test_run_format_html(tmp_path: Path) -> None:
    """--format html produces an HTML report."""
    outfile = str(tmp_path / "report.html")
    result = runner.invoke(app, ["run", "--format", "html", "--output", outfile, FIXTURE])
    assert result.exit_code == 0


@pytest.mark.skipif(
    not _has_formatter("behave_modern_md_report"),
    reason="behave-modern-md-report not installed",
)
def test_run_format_md() -> None:
    """--format md produces a Markdown report."""
    result = runner.invoke(app, ["run", "--format", "md", FIXTURE])
    assert result.exit_code == 0


@pytest.mark.skipif(
    not _has_formatter("behave_modern_sheets_report"),
    reason="behave-modern-sheets-report not installed",
)
def test_run_format_sheets(tmp_path: Path) -> None:
    """--format sheets produces an XLSX report."""
    outfile = str(tmp_path / "report.xlsx")
    result = runner.invoke(app, ["run", "--format", "sheets", "--output", outfile, FIXTURE])
    assert result.exit_code == 0


@pytest.mark.skipif(
    not _has_formatter("behave_trace"),
    reason="behave-trace not installed",
)
def test_run_trace() -> None:
    """--trace enables behave-trace formatter."""
    result = runner.invoke(app, ["run", "--trace", FIXTURE])
    assert result.exit_code == 0


def test_run_retries() -> None:
    """--retries sets BEHAVE_RETRY_MAX_RETRIES env var."""
    result = runner.invoke(app, ["run", "--retries", "2", FIXTURE])
    assert result.exit_code == 0


def test_run_retries_with_flaky_report() -> None:
    """--retries with --flaky-report sets both env vars."""
    result = runner.invoke(app, ["run", "--retries", "2", "--flaky-report", FIXTURE])
    assert result.exit_code == 0


def test_run_priority_order() -> None:
    """--priority-order sets BEHAVE_PRIORITY_ORDER env var."""
    result = runner.invoke(app, ["run", "--priority-order", PRIORITY_FIXTURE])
    assert result.exit_code == 0


def test_run_fail_fast() -> None:
    """--fail-fast sets BEHAVE_PRIORITY_FAIL_FAST env var."""
    result = runner.invoke(app, ["run", "--fail-fast", PRIORITY_FIXTURE])
    assert result.exit_code == 0


def test_run_shard_env_var() -> None:
    """--shard sets BEHAVE_POOL_SHARD env var (not CLI flag)."""
    result = runner.invoke(app, ["run", "--shard", "1/3", FIXTURE])
    assert result.exit_code == 0


def test_run_default_features() -> None:
    """run with no features uses 'features' default."""
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["run"])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert config.features == ["features"]


# ---------------------------------------------------------------------------
# RunConfig construction via mocked run()
# ---------------------------------------------------------------------------


def test_run_config_dry_run() -> None:
    """--dry-run sets dry_run=True in RunConfig."""
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        runner.invoke(app, ["run", "--dry-run", FIXTURE])
    config = mock_run.call_args[0][0]
    assert config.dry_run is True


def test_run_config_stop_on_failure() -> None:
    """--stop-on-failure sets stop_on_failure=True."""
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        runner.invoke(app, ["run", "--stop-on-failure", FIXTURE])
    config = mock_run.call_args[0][0]
    assert config.stop_on_failure is True


def test_run_config_max_fail() -> None:
    """--max-fail sets max_failures."""
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        runner.invoke(app, ["run", "--max-fail", "3", FIXTURE])
    config = mock_run.call_args[0][0]
    assert config.max_failures == 3


def test_run_config_timeout() -> None:
    """--timeout sets timeout."""
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        runner.invoke(app, ["run", "--timeout", "30", FIXTURE])
    config = mock_run.call_args[0][0]
    assert config.timeout == 30


def test_run_config_format() -> None:
    """--format sets fmt."""
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        runner.invoke(app, ["run", "--format", "json", FIXTURE])
    config = mock_run.call_args[0][0]
    assert config.fmt == "json"


def test_run_config_output() -> None:
    """--output sets outfile."""
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        runner.invoke(app, ["run", "--output", "reports/out.json", FIXTURE])
    config = mock_run.call_args[0][0]
    assert config.outfile == "reports/out.json"


def test_run_config_parallel() -> None:
    """--parallel sets parallel."""
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        runner.invoke(app, ["run", "--parallel", "4", FIXTURE])
    config = mock_run.call_args[0][0]
    assert config.parallel == 4


def test_run_config_parallel_short_flag() -> None:
    """-n is alias for --parallel."""
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        runner.invoke(app, ["run", "-n", "4", FIXTURE])
    config = mock_run.call_args[0][0]
    assert config.parallel == 4


def test_run_config_parallel_scheme() -> None:
    """--parallel-scheme sets parallel_scheme."""
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        runner.invoke(app, ["run", "--parallel-scheme", "scenario", FIXTURE])
    config = mock_run.call_args[0][0]
    assert config.parallel_scheme == "scenario"


def test_run_config_parallel_balance() -> None:
    """--parallel-balance sets parallel_balance."""
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        runner.invoke(app, ["run", "--parallel-balance", "lpt", FIXTURE])
    config = mock_run.call_args[0][0]
    assert config.parallel_balance == "lpt"


def test_run_config_parallel_timing_file() -> None:
    """--parallel-timing-file sets parallel_timing_file."""
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        runner.invoke(app, ["run", "--parallel-timing-file", "timing.json", FIXTURE])
    config = mock_run.call_args[0][0]
    assert config.parallel_timing_file == "timing.json"


def test_run_config_retries() -> None:
    """--retries sets retries."""
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        runner.invoke(app, ["run", "--retries", "3", FIXTURE])
    config = mock_run.call_args[0][0]
    assert config.retries == 3


def test_run_config_flaky_report_with_retries() -> None:
    """--flaky-report with --retries sets flaky_report=True."""
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        runner.invoke(app, ["run", "--retries", "2", "--flaky-report", FIXTURE])
    config = mock_run.call_args[0][0]
    assert config.flaky_report is True


def test_run_config_flaky_report_without_retries() -> None:
    """--flaky-report without --retries is ignored."""
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        runner.invoke(app, ["run", "--flaky-report", FIXTURE])
    config = mock_run.call_args[0][0]
    assert config.flaky_report is False


def test_run_config_priority_order() -> None:
    """--priority-order sets priority_order=True."""
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        runner.invoke(app, ["run", "--priority-order", FIXTURE])
    config = mock_run.call_args[0][0]
    assert config.priority_order is True


def test_run_config_smoke_adds_tag() -> None:
    """--smoke adds @smoke to tags."""
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        runner.invoke(app, ["run", "--smoke", FIXTURE])
    config = mock_run.call_args[0][0]
    assert "@smoke" in config.tags


def test_run_config_fail_fast() -> None:
    """--fail-fast sets fail_fast=True."""
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        runner.invoke(app, ["run", "--fail-fast", FIXTURE])
    config = mock_run.call_args[0][0]
    assert config.fail_fast is True


def test_run_config_scenario_timeout() -> None:
    """--scenario-timeout sets scenario_timeout."""
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        runner.invoke(app, ["run", "--scenario-timeout", "10", FIXTURE])
    config = mock_run.call_args[0][0]
    assert config.scenario_timeout == 10


def test_run_config_ui() -> None:
    """--ui sets ui=True."""
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        runner.invoke(app, ["run", "--ui", FIXTURE])
    config = mock_run.call_args[0][0]
    assert config.ui is True


def test_run_config_debug() -> None:
    """--debug sets debug=True."""
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        runner.invoke(app, ["run", "--debug", FIXTURE])
    config = mock_run.call_args[0][0]
    assert config.debug is True


def test_run_config_trace() -> None:
    """--trace sets trace=True."""
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        runner.invoke(app, ["run", "--trace", FIXTURE])
    config = mock_run.call_args[0][0]
    assert config.trace is True


def test_run_config_tags() -> None:
    """--tags sets tags list."""
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        runner.invoke(app, ["run", "--tags=@smoke", "--tags=@fast", FIXTURE])
    config = mock_run.call_args[0][0]
    assert "@smoke" in config.tags
    assert "@fast" in config.tags


def test_run_config_tags_short_flag() -> None:
    """-t is alias for --tags."""
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        runner.invoke(app, ["run", "-t", "@smoke", FIXTURE])
    config = mock_run.call_args[0][0]
    assert "@smoke" in config.tags


def test_run_config_features() -> None:
    """Feature paths are passed through."""
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        runner.invoke(app, ["run", "features/login.feature", "features/logout.feature"])
    config = mock_run.call_args[0][0]
    assert len(config.features) == 2


def test_run_config_exit_code_propagation() -> None:
    """Non-zero exit code from run() is propagated."""
    with patch("behave_runner.commands.run.run", return_value=1):
        result = runner.invoke(app, ["run", FIXTURE])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# Shard validation
# ---------------------------------------------------------------------------


def test_run_shard_invalid_format() -> None:
    """Invalid shard format shows error."""
    result = runner.invoke(app, ["run", "--shard", "invalid", FIXTURE])
    assert result.exit_code == 2
    assert "Invalid shard format" in result.output


def test_run_shard_i_greater_than_n() -> None:
    """Shard 3/2 is invalid (i > n)."""
    result = runner.invoke(app, ["run", "--shard", "3/2", FIXTURE])
    assert result.exit_code == 2
    assert "i must be 1..n" in result.output


def test_run_shard_zero_i() -> None:
    """Shard 0/3 is invalid (i < 1)."""
    result = runner.invoke(app, ["run", "--shard", "0/3", FIXTURE])
    assert result.exit_code == 2
    assert "i must be 1..n" in result.output


def test_run_shard_valid_format() -> None:
    """Valid shard format is accepted (1/3)."""
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["run", "--shard", "1/3", FIXTURE])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert config.shard == "1/3"


def test_run_shard_valid_last() -> None:
    """Valid shard 3/3 is accepted."""
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["run", "--shard", "3/3", FIXTURE])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert config.shard == "3/3"


# ---------------------------------------------------------------------------
# Profile loading
# ---------------------------------------------------------------------------


def test_run_profile_format_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--profile loads format and output from pyproject.toml."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.ci]
            format = "json"
            output = "reports/ci.json"
        """)
    )
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["run", "--profile", "ci", FIXTURE])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert config.fmt == "json"
    assert config.outfile == "reports/ci.json"


def test_run_profile_tags(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--profile loads tags."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.smoke]
            tags = ["@smoke"]
        """)
    )
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["run", "--profile", "smoke", FIXTURE])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert "@smoke" in config.tags


def test_run_profile_parallel(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--profile loads parallel setting."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.par]
            parallel = 4
        """)
    )
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["run", "--profile", "par", FIXTURE])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert config.parallel == 4


def test_run_profile_dry_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--profile loads dry_run."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.dry]
            dry_run = true
        """)
    )
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["run", "--profile", "dry", FIXTURE])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert config.dry_run is True


def test_run_profile_retries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--profile loads retries."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.retry]
            retries = 3
        """)
    )
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["run", "--profile", "retry", FIXTURE])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert config.retries == 3


def test_run_profile_smoke(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--profile smoke=True adds @smoke tag."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.sm]
            smoke = true
        """)
    )
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["run", "--profile", "sm", FIXTURE])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert "@smoke" in config.tags


def test_run_profile_features(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--profile features are used when no CLI features given."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.ci]
            features = ["my_features/"]
        """)
    )
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["run", "--profile", "ci"])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert config.features == ["my_features/"]


def test_run_profile_cli_overrides_features(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CLI features take priority over profile features."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.ci]
            features = ["profile_features/"]
        """)
    )
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["run", "--profile", "ci", "cli_features/"])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert len(config.features) == 1
    assert Path(config.features[0]).as_posix() == "cli_features"


def test_run_profile_cli_overrides_format(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """CLI --format takes priority over profile format."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.ci]
            format = "json"
        """)
    )
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["run", "--profile", "ci", "--format", "html", FIXTURE])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert config.fmt == "html"


def test_run_profile_cli_tags_merged(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """CLI tags and profile tags are merged."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.ci]
            tags = ["@ci"]
        """)
    )
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["run", "--profile", "ci", "--tags=@smoke", FIXTURE])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert "@smoke" in config.tags
    assert "@ci" in config.tags


def test_run_profile_cli_smoke_and_profile_tags_merged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """--smoke and profile tags are both added."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.ci]
            tags = ["@ci"]
        """)
    )
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["run", "--profile", "ci", "--smoke", FIXTURE])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert "@smoke" in config.tags
    assert "@ci" in config.tags


def test_run_profile_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--profile with nonexistent profile shows error."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.ci]
            format = "json"
        """)
    )
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["run", "--profile", "nonexistent", FIXTURE])
    assert result.exit_code == 2
    assert "not found" in result.output.lower()


def test_run_profile_shard(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--profile can set shard."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.ci]
            shard = "1/3"
        """)
    )
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["run", "--profile", "ci", FIXTURE])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert config.shard == "1/3"


def test_run_profile_invalid_shard(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--profile with invalid shard shows error."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.ci]
            shard = "bad"
        """)
    )
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["run", "--profile", "ci", FIXTURE])
    assert result.exit_code == 2
    assert "Invalid shard" in result.output


def test_run_profile_flaky_with_retries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--profile flaky_report=True with retries sets flaky_report."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.ci]
            retries = 2
            flaky_report = true
        """)
    )
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["run", "--profile", "ci", FIXTURE])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert config.flaky_report is True


def test_run_profile_flaky_without_retries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--profile flaky_report=True without retries is ignored."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.ci]
            flaky_report = true
        """)
    )
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["run", "--profile", "ci", FIXTURE])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert config.flaky_report is False


def test_run_profile_priority_order(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--profile priority_order=True."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.ci]
            priority_order = true
        """)
    )
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["run", "--profile", "ci", FIXTURE])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert config.priority_order is True


def test_run_profile_trace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--profile trace=True."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.ci]
            trace = true
        """)
    )
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["run", "--profile", "ci", FIXTURE])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert config.trace is True


def test_run_profile_no_color_verbose(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--profile no_color and verbose."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.ci]
            no_color = true
            verbose = true
        """)
    )
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["run", "--profile", "ci", FIXTURE])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert config.no_color is True
    assert config.verbose is True


def test_run_profile_scenario_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--profile scenario_timeout."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.ci]
            scenario_timeout = 10
        """)
    )
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["run", "--profile", "ci", FIXTURE])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert config.scenario_timeout == 10


def test_run_profile_name(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--profile name list."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.ci]
            name = ["Login", "Logout"]
        """)
    )
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["run", "--profile", "ci", FIXTURE])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert "Login" in config.name
    assert "Logout" in config.name


def test_run_profile_max_failures(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--profile max_failures."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.ci]
            max_failures = 3
        """)
    )
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["run", "--profile", "ci", FIXTURE])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert config.max_failures == 3


def test_run_profile_stop_on_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--profile stop_on_failure."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.ci]
            stop_on_failure = true
        """)
    )
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["run", "--profile", "ci", FIXTURE])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert config.stop_on_failure is True


def test_run_profile_fail_fast(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--profile fail_fast."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [tool.behave-runner.profiles.ci]
            fail_fast = true
        """)
    )
    monkeypatch.chdir(tmp_path)
    with patch("behave_runner.commands.run.run", return_value=0) as mock_run:
        result = runner.invoke(app, ["run", "--profile", "ci", FIXTURE])
    assert result.exit_code == 0
    config = mock_run.call_args[0][0]
    assert config.fail_fast is True


# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------


def test_run_help() -> None:
    """run --help shows all options."""
    result = runner.invoke(app, ["run", "--help"])
    assert result.exit_code == 0
    assert "run" in result.stdout.lower()
    assert "--tags" in result.stdout
    assert "--dry-run" in result.stdout
    assert "--stop-on-failure" in result.stdout
    assert "--max-fail" in result.stdout
    assert "--timeout" in result.stdout
    assert "--format" in result.stdout
    assert "--output" in result.stdout
    assert "--parallel" in result.stdout
    assert "--shard" in result.stdout
    assert "--retries" in result.stdout
    assert "--flaky-report" in result.stdout
    assert "--priority-order" in result.stdout
    assert "--smoke" in result.stdout
    assert "--fail-fast" in result.stdout
    assert "--profile" in result.stdout
    assert "--scenario-timeout" in result.stdout
    assert "--ui" in result.stdout
    assert "--debug" in result.stdout
    assert "--trace" in result.stdout
