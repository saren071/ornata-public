"""Coverage for the core effects timeline helpers."""

from __future__ import annotations

import itertools

import pytest

from ornata.api.exports.effects import BaseTimeline, FrameCache, _lerp, ease_in_out

import ornata.effects.timeline as timeline_module
from ornata.effects import transitions as transitions_module


def test_base_timeline_executes_actions(monkeypatch: pytest.MonkeyPatch) -> None:
    """BaseTimeline.play should execute queued callbacks in order."""

    timeline = BaseTimeline()
    executed: list[str] = []

    timeline.add(0.0, lambda: executed.append("first"))
    timeline.add(1.0, lambda: executed.append("second"))

    counter = itertools.chain([0.0], itertools.repeat(10.0))
    counter_iter = iter(counter)

    monkeypatch.setattr(timeline_module.time, "perf_counter", lambda: next(counter_iter))
    monkeypatch.setattr(timeline_module.time, "sleep", lambda _seconds: None)

    timeline.play()

    assert executed == ["first", "second"]


def test_frame_cache_diff_behavior() -> None:
    """FrameCache should detect content changes and track history."""

    cache = FrameCache(max_history=3)
    assert cache.update("alpha") is True
    assert cache.update("alpha") is False
    assert cache.update("beta") is True

    assert cache.diff() == [(0, "beta")]
    assert cache.diff_structured() == [(0, "beta")]
    assert cache.last() == "beta"
    assert cache.history() == ["alpha", "beta"]

    cache.clear()
    assert cache.last() is None
    assert cache.history() == []


def test_transition_helpers_behavior() -> None:
    """Transition helper utilities should provide deterministic output."""

    assert _lerp(0.0, 10.0, 0.5) == pytest.approx(5.0)
    assert ease_in_out(0.25) == pytest.approx(0.15625)

    transitions_module.Transition.color_fade("hello", "red", "blue", duration=0.1, fps=1)
    transitions_module.Transition.blink("hello", color="cyan", cycles=1, fps=10)
