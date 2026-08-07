"""Shared test fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def disable_browser(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent behave-runner from opening a browser during tests."""
    monkeypatch.setenv("BEHAVE_RUNNER_NO_BROWSER", "1")
