"""Minimal animation timeline with keyframes."""

from __future__ import annotations

import time
from collections import deque
from typing import TYPE_CHECKING

from ornata.api.exports.definitions import Keyframe

if TYPE_CHECKING:
    from collections.abc import Callable


class BaseTimeline:
    def __init__(self) -> None:
        self._frames: list[Keyframe] = []

    def add(self, t: float, action: Callable[[], None]) -> None:
        self._frames.append(Keyframe(offset=t, action=action))
        self._frames.sort(key=lambda k: k.offset)

    def play(self) -> None:
        start = time.perf_counter()
        idx = 0
        while idx < len(self._frames):
            now = time.perf_counter() - start
            next_t = self._frames[idx].offset
            if now >= next_t:
                try:
                    action_cb = self._frames[idx].action
                    if action_cb is not None:
                        action_cb()
                except Exception:
                    pass
                idx += 1
            else:
                time.sleep(min(0.01, next_t - now))


class FrameCache(BaseTimeline):
    """Cache frames and provide diff information for live rendering."""

    def __init__(self, max_history: int = 120) -> None:
        self.max_history = max_history
        self._history: deque[list[str]] = deque(maxlen=max_history)
        self._current: list[str] | None = None
        self._previous: list[str] | None = None

    def update(self, frame: str) -> bool:
        """Store a frame and return True if it differs from the previous one."""
        lines = frame.splitlines()
        if self._current == lines:
            return False
        self._previous = self._current
        self._current = lines
        self._history.append(lines)
        return True

    def diff(self) -> list[tuple[int, str]]:
        """Return line-level changes relative to the prior cached frame."""
        if self._current is None:
            return []
        if self._previous is None:
            return [(idx, line) for idx, line in enumerate(self._current)]
        # Simple diff implementation
        changes: list[tuple[int, str]] = []
        for i, (a, b) in enumerate(zip(self._previous, self._current, strict=True)):
            if a != b:
                changes.append((i, b))
        for i in range(len(self._previous), len(self._current)):
            changes.append((i, self._current[i]))
        return changes

    def diff_structured(self) -> list[tuple[int, str]]:
        """Return structured line changes using simple diff.

        Consumers can use this to apply partial updates in GUI backends.
        """
        if self._current is None:
            return []
        prev = self._previous or []
        # Simple diff implementation
        changes: list[tuple[int, str]] = []
        for i, (a, b) in enumerate(zip(prev, self._current, strict=True)):
            if a != b:
                changes.append((i, b))
        for i in range(len(prev), len(self._current)):
            changes.append((i, self._current[i]))
        return changes

    def last(self) -> str | None:
        if self._current is None:
            return None
        return "\n".join(self._current)

    def history(self) -> list[str]:
        return ["\n".join(lines) for lines in self._history]

    def clear(self) -> None:
        self._history.clear()
        self._current = None
        self._previous = None
