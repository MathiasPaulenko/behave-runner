"""Tests for behave_runner.utils."""

from __future__ import annotations

from pathlib import Path

from behave_runner.utils import find_project_root


def test_find_project_root_finds_pyproject(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")
    assert find_project_root(tmp_path) == tmp_path


def test_find_project_root_returns_cwd_if_no_pyproject(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    result = find_project_root(tmp_path)
    assert isinstance(result, Path)
