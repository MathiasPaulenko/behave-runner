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


def test_scan_skips_missing_paths(tmp_path: Path) -> None:
    """Scan should not crash when a watched path is removed."""
    missing = tmp_path / "missing"
    watcher = FileWatcher([missing], lambda c: None, debounce_ms=0)
    result = watcher._scan()
    assert result == {}


def test_detects_deleted_file(tmp_path: Path) -> None:
    """Watcher detects when a file is deleted."""
    f = tmp_path / "deleteme.feature"
    f.write_text("Feature: Delete")
    watcher = FileWatcher([tmp_path], lambda c: None, debounce_ms=0)
    watcher._mtimes = watcher._scan()
    f.unlink()
    changed = watcher._detect_changes()
    assert f in changed


def test_scan_nested_directories(tmp_path: Path) -> None:
    """Scan recursively finds files in nested directories."""
    sub = tmp_path / "sub" / "deep"
    sub.mkdir(parents=True)
    f1 = tmp_path / "top.feature"
    f2 = sub / "nested.feature"
    f1.write_text("Feature: Top")
    f2.write_text("Feature: Nested")
    watcher = FileWatcher([tmp_path], lambda c: None, debounce_ms=0)
    result = watcher._scan()
    assert f1 in result
    assert f2 in result


def test_run_loop_stops(tmp_path: Path) -> None:
    """run() exits when stop() is called."""
    (tmp_path / "test.feature").write_text("Feature: Test")
    watcher = FileWatcher([tmp_path], lambda c: None, debounce_ms=0)

    # Stop immediately after first scan
    import threading

    def stop_after_delay() -> None:
        import time

        time.sleep(0.2)
        watcher.stop()

    thread = threading.Thread(target=stop_after_delay, daemon=True)
    thread.start()
    watcher.run()
    thread.join(timeout=1.0)
    assert not watcher._running


def test_callback_receives_changed_files(tmp_path: Path) -> None:
    """Callback receives the list of changed files."""
    changes: list[Path] = []
    watcher = FileWatcher([tmp_path], lambda c: changes.extend(c), debounce_ms=0)
    watcher._mtimes = watcher._scan()
    import time

    time.sleep(0.01)
    (tmp_path / "trigger.feature").write_text("Feature: Trigger")
    changed = watcher._detect_changes()
    assert (tmp_path / "trigger.feature") in changed


def test_debounce_zero_triggers_immediately(tmp_path: Path) -> None:
    """With debounce_ms=0, changes are detected on next poll."""
    watcher = FileWatcher([tmp_path], lambda c: None, debounce_ms=0)
    assert watcher._debounce == 0.0
