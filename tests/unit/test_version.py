"""Tests for behave_runner version."""

from __future__ import annotations

from behave_runner import __version__


def test_version_is_string() -> None:
    assert isinstance(__version__, str)


def test_version_format() -> None:
    """Version follows semver: X.Y.Z."""
    parts = __version__.split(".")
    assert len(parts) == 3
    for part in parts:
        assert part.isdigit()
