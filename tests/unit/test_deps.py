"""Tests for behave_runner.core.deps."""

from __future__ import annotations

from behave_runner.core.deps import check_optional, is_installed


def test_is_installed_true() -> None:
    assert is_installed("os") is True


def test_is_installed_false() -> None:
    assert is_installed("nonexistent_pkg_xyz") is False


def test_check_optional_present() -> None:
    assert check_optional("os", "os", "os-flag") is True


def test_check_optional_absent() -> None:
    assert check_optional("xyz", "nonexistent_pkg_xyz", "xyz-flag") is False
