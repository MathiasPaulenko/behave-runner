"""Shared test fixtures."""

from __future__ import annotations

import os

# Disable Typer's Rich help rendering and set wide terminal.
# Rich 15.0.0 renders empty panels in CI (no terminal), causing help
# text assertions to fail. Plain Click output is deterministic and testable.
os.environ.setdefault("TYPER_USE_RICH", "0")
os.environ.setdefault("COLUMNS", "200")

import pytest  # noqa: E402
from typer.testing import CliRunner as _CliRunner  # noqa: E402

# Patch CliRunner.invoke to always pass terminal_width=200 so that
# Click help output is not truncated in narrow CI terminals.
_orig_invoke = _CliRunner.invoke


def _patched_invoke(
    self, cli, args=None, input=None, env=None, catch_exceptions=True, color=False, **extra
):
    extra.setdefault("terminal_width", 200)
    return _orig_invoke(self, cli, args, input, env, catch_exceptions, color, **extra)


_CliRunner.invoke = _patched_invoke


@pytest.fixture(autouse=True)
def disable_browser(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent behave-runner from opening a browser during tests."""
    monkeypatch.setenv("BEHAVE_RUNNER_NO_BROWSER", "1")
