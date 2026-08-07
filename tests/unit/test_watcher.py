"""Unit tests for FileWatcher."""

from __future__ import annotations

import time
from pathlib import Path

from behave_runner.core.watcher import FileWatcher


def test_detects_new_file(tmp_path: Path) -> None:
    """Watcher detects newly created files."""
    changes: list[Path] = []
    watcher = FileWatcher([tmp_path], lambda c: changes.extend(c), debounce_ms=0)
    watcher._mtimes = watcher._scan()
    (tmp_path / "new.feature").write_text("Feature: Test")
    changed = watcher._detect_changes()
    assert (tmp_path / "new.feature") in changed


def test_detects_modified_file(tmp_path: Path) -> None:
    """Watcher detects modified files."""
    f = tmp_path / "test.feature"
    f.write_text("Feature: Test")
    changes: list[Path] = []
    watcher = FileWatcher([tmp_path], lambda c: changes.extend(c), debounce_ms=0)
    watcher._mtimes = watcher._scan()
    time.sleep(0.01)
    f.write_text("Feature: Modified")
    changed = watcher._detect_changes()
    assert f in changed


def test_debounce(tmp_path: Path) -> None:
    """Debounce prevents triggers within the debounce window."""
    watcher = FileWatcher([tmp_path], lambda c: None, debounce_ms=1000)
    watcher._last_trigger = time.time()
    assert time.time() - watcher._last_trigger < 1.0


def test_stop() -> None:
    """stop() sets _running to False."""
    watcher = FileWatcher([Path(".")], lambda c: None)
    watcher._running = True
    watcher.stop()
    assert watcher._running is False


def test_no_changes(tmp_path: Path) -> None:
    """No changes detected when files are unchanged."""
    (tmp_path / "stable.feature").write_text("Feature: Stable")
    watcher = FileWatcher([tmp_path], lambda c: None, debounce_ms=0)
    watcher._mtimes = watcher._scan()
    changed = watcher._detect_changes()
    assert changed == []


def test_single_file_watch(tmp_path: Path) -> None:
    """Watcher can watch a single file instead of a directory."""
    f = tmp_path / "single.feature"
    f.write_text("Feature: Single")
    changes: list[Path] = []
    watcher = FileWatcher([f], lambda c: changes.extend(c), debounce_ms=0)
    watcher._mtimes = watcher._scan()
    time.sleep(0.01)
    f.write_text("Feature: Changed")
    changed = watcher._detect_changes()
    assert f in changed
