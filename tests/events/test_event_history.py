"""Event replay buffer, replayer, and analyzer coverage."""

from __future__ import annotations

from unittest.mock import patch

from ornata.definitions.dataclasses.events import Event
from ornata.definitions.enums import EventType
from ornata.events.history.replay import (
    EventReplayAnalyzer,
    EventReplayBuffer,
    EventReplayer,
)


def _make_event(timestamp: float = 0.0, event_type: EventType = EventType.TICK) -> Event:
    return Event(type=event_type, timestamp=timestamp)


def test_event_replay_buffer_session_management() -> None:
    """Recording sessions should enforce limits, trimming overflow and stopping cleanly."""

    buffer = EventReplayBuffer(max_events=2)
    buffer.start_recording("alpha")
    buffer.record_event(_make_event(), session_id="alpha")
    buffer.record_event(_make_event(timestamp=1.0), session_id="alpha")
    buffer.record_event(_make_event(timestamp=2.0), session_id="alpha")

    assert buffer.get_session_event_count("alpha") == 2
    events = buffer.stop_recording("alpha")
    assert len(events) == 2

    buffer.start_recording("one")
    buffer.start_recording("two")
    buffer.record_event(_make_event(timestamp=3.0))
    merged = buffer.stop_recording()
    assert merged
    assert buffer.is_recording() is False


def test_event_replayer_handles_errors_and_sync() -> None:
    """EventReplayer should continue on handler errors and support synchronous playback."""

    replayer = EventReplayer()
    events = [_make_event(timestamp=0.0), _make_event(timestamp=0.1)]
    calls: list[str] = []

    def flaky_handler(event: Event) -> None:
        calls.append(event.type.value)
        if len(calls) == 1:
            raise RuntimeError("boom")

    with patch("ornata.events.history.replay.time.sleep", autospec=True) as sleep_mock:
        replayer.replay_events(events, flaky_handler, speed_multiplier=2.0, real_time=True)
        assert sleep_mock.called

    assert calls == [EventType.TICK.value, EventType.TICK.value]

    sync_calls: list[str] = []
    replayer.replay_events_sync(events, lambda event: sync_calls.append(event.type.value))
    assert sync_calls == [EventType.TICK.value, EventType.TICK.value]


def test_event_replay_analyzer_reports_metrics_and_patterns() -> None:
    """Analyzer should return aggregate metrics and detect repeated patterns."""

    analyzer = EventReplayAnalyzer()
    events = [
        _make_event(timestamp=0.0, event_type=EventType.TICK),
        _make_event(timestamp=0.1, event_type=EventType.TICK),
        _make_event(timestamp=0.2, event_type=EventType.TICK),
        _make_event(timestamp=1.2, event_type=EventType.LAYOUT_INVALIDATED),
        _make_event(timestamp=1.4, event_type=EventType.LAYOUT_INVALIDATED),
        _make_event(timestamp=1.6, event_type=EventType.LAYOUT_INVALIDATED),
    ]

    metrics = analyzer.analyze_events(events)
    assert metrics["total_events"] == len(events)
    assert metrics["event_types"][EventType.TICK.value] == 3
    assert metrics["time_span"] >= 1.6 - 0.0

    patterns = analyzer.find_event_patterns(events)
    pattern_types = {pattern["pattern"] for pattern in patterns}
    assert {"consecutive_run", "burst"}.issubset(pattern_types)
