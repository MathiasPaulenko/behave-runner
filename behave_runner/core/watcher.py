"""Polling-based file watcher with debounce."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from pathlib import Path

logger = logging.getLogger(__name__)


class FileWatcher:
    """Polling-based file watcher with debounce."""

    def __init__(
        self,
        paths: list[Path],
        on_change: Callable[[list[Path]], None],
        debounce_ms: int = 500,
    ) -> None:
        self._paths = paths
        self._on_change = on_change
        self._debounce = debounce_ms / 1000.0
        self._mtimes: dict[Path, float] = {}
        self._last_trigger = 0.0
        self._running = False

    def _scan(self) -> dict[Path, float]:
        """Scan all watched paths and return current mtimes."""
        result: dict[Path, float] = {}
        for path in self._paths:
            try:
                if path.is_file():
                    result[path] = path.stat().st_mtime
                elif path.is_dir():
                    for f in path.rglob("*"):
                        try:
                            if f.is_file():
                                result[f] = f.stat().st_mtime
                        except OSError:
                            logger.debug("Could not stat %s during scan", f)
            except OSError:
                logger.debug("Could not scan %s", path)
        return result

    def _detect_changes(self) -> list[Path]:
        """Detect changed, added, or deleted files since last scan. Update internal state."""
        current = self._scan()
        changed: list[Path] = []
        for path, mtime in current.items():
            if path not in self._mtimes or self._mtimes[path] != mtime:
                changed.append(path)
        for path in self._mtimes:
            if path not in current:
                changed.append(path)
        self._mtimes = current
        return changed

    def run(self) -> None:
        """Run the watcher loop. Blocks until stopped."""
        self._running = True
        self._mtimes = self._scan()
        while self._running:
            time.sleep(0.1)
            now = time.time()
            if now - self._last_trigger < self._debounce:
                continue
            changed = self._detect_changes()
            if changed:
                self._last_trigger = now
                try:
                    self._on_change(changed)
                except Exception:
                    logger.exception("Watcher callback failed for %s", changed)

    def stop(self) -> None:
        """Stop the watcher loop."""
        self._running = False
