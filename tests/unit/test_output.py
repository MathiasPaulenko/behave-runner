"""Tests for behave_runner.core.output."""

from __future__ import annotations

import time
from pathlib import Path

from behave_runner.core.output import clean_output_dir, ensure_output_dir, find_latest_report


def test_ensure_output_dir_creates(tmp_path: Path) -> None:
    out = tmp_path / "reports"
    result = ensure_output_dir(out)
    assert result == out
    assert out.exists()
    assert out.is_dir()


def test_ensure_output_dir_idempotent(tmp_path: Path) -> None:
    out = tmp_path / "reports"
    out.mkdir()
    ensure_output_dir(out)  # should not raise


def test_find_latest_report(tmp_path: Path) -> None:
    out = tmp_path / "reports"
    out.mkdir()
    old = out / "old.json"
    new = out / "new.json"
    old.write_text("{}")
    time.sleep(0.01)
    new.write_text("{}")
    assert find_latest_report(out) == new


def test_find_latest_report_empty(tmp_path: Path) -> None:
    out = tmp_path / "reports"
    out.mkdir()
    assert find_latest_report(out) is None


def test_find_latest_report_no_dir(tmp_path: Path) -> None:
    assert find_latest_report(tmp_path / "nonexistent") is None


def test_clean_output_dir(tmp_path: Path) -> None:
    out = tmp_path / "reports"
    out.mkdir()
    (out / "a.json").write_text("{}")
    (out / "b.json").write_text("{}")
    clean_output_dir(out)
    assert not any(out.iterdir())


def test_clean_output_dir_no_dir(tmp_path: Path) -> None:
    clean_output_dir(tmp_path / "nonexistent")  # should not raise
