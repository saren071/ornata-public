"""Event replay functionality for Ornata."""

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable

    from ornata.api.exports.definitions import Event

logger = get_logger(__name__)


# === REPLACE inside EventReplayBuffer ===

class EventReplayBuffer:
    """Buffer for recording and replaying events."""

    def __init__(self, max_events: int = 10000) -> None:
        self.max_events = max_events
        self._events: dict[str, list[EventEntry]] = {}
        self._lock = threading.RLock()
        self._recording_sessions: set[str] = set()
        # NEW: fast flag, read on hot path without taking _lock
        self._recording_active: bool = False

    # NEW: O(1) check with no lock for hot path
    def is_recording(self) -> bool:
        return self._recording_active

    def start_recording(self, session_id: str) -> None:
        with self._lock:
            if session_id in self._recording_sessions:
                logger.warning(f"Session {session_id} is already recording")
                return
            self._recording_sessions.add(session_id)
            self._events[session_id] = []
            # flip fast flag
            self._recording_active = True
            logger.debug(f"Started recording session {session_id}")

    def stop_recording(self, session_id: str | None = None) -> list[Event]:
        with self._lock:
            if session_id is None:
                all_events: list[Event] = []
                for sid in list(self._recording_sessions):
                    if sid in self._events:
                        all_events.extend(entry.event for entry in self._events[sid])
                        del self._events[sid]
                    self._recording_sessions.discard(sid)
                # flip fast flag
                self._recording_active = False
                logger.debug(f"Stopped all recording sessions, captured {len(all_events)} events")
                return all_events
            if session_id not in self._recording_sessions:
                logger.warning(f"Session {session_id} is not recording")
                return []
            self._recording_sessions.discard(session_id)
            session_events = self._events.pop(session_id, [])
            # update fast flag
            self._recording_active = bool(self._recording_sessions)
            events = [entry.event for entry in session_events]
            logger.debug(f"Stopped recording session {session_id}, captured {len(events)} events")
            return events

    def record_event(self, event: Event, session_id: str | None = None) -> None:
        with self._lock:
            if not self._recording_sessions:
                return
            if session_id and session_id not in self._recording_sessions:
                return
            sessions_to_record = [session_id] if session_id else list(self._recording_sessions)
            for sid in sessions_to_record:
                if sid not in self._events:
                    continue
                entry = EventEntry(event, time.time())
                self._events[sid].append(entry)
                if len(self._events[sid]) > self.max_events:
                    remove_count = len(self._events[sid]) - self.max_events
                    self._events[sid] = self._events[sid][remove_count:]
                    logger.warning(f"Event buffer overflow for session {sid}, removed {remove_count} events")

    def get_recording_sessions(self) -> list[str]:
        """Get list of active recording sessions.

        Returns:
            list[str]: Identifiers for active sessions.
        """
        with self._lock:
            return list(self._recording_sessions)

    def get_session_event_count(self, session_id: str) -> int:
        """Get the number of events recorded for a session.

        Args:
            session_id: Identifier for the session to inspect.

        Returns:
            int: Number of recorded events.
        """
        with self._lock:
            return len(self._events.get(session_id, []))


class EventEntry:
    """Entry containing an event and metadata."""

    def __init__(self, event: Event, recorded_at: float) -> None:
        """Initialize event entry.

        Args:
            event: Event instance captured during recording.
            recorded_at: Timestamp when the event was recorded.
        """
        self.event = event
        self.recorded_at = recorded_at
        self.sequence_number = threading.get_native_id()  # Thread ID for ordering


class EventReplayer:
    """Replays recorded events for testing and debugging."""

    def __init__(self) -> None:
        """Initialize event replayer."""
        self._lock = threading.RLock()

    def replay_events(
        self,
        events: list[Event],
        handler: Callable[[Event], None],
        speed_multiplier: float = 1.0,
        real_time: bool = True,
    ) -> None:
        """Replay events with timing control.

        Args:
            events: Events to replay.
            handler: Callable invoked for each event.
            speed_multiplier: Playback speed multiplier.
            real_time: When ``True`` respects original timing gaps.

        Returns:
            None
        """
        if not events:
            return

        with self._lock:
            logger.debug(f"Starting replay of {len(events)} events with speed {speed_multiplier}x")

            # Sort events by timestamp
            sorted_events = sorted(events, key=lambda e: e.timestamp)

            last_timestamp = sorted_events[0].timestamp

            for event in sorted_events:
                if real_time:
                    # Calculate delay based on original timing
                    delay = (event.timestamp - last_timestamp) / speed_multiplier
                    if delay > 0:
                        time.sleep(delay)
                    last_timestamp = event.timestamp

                try:
                    logger.log(5, f"Replaying event {event.type.value}")
                    handler(event)
                except Exception as e:
                    logger.error(f"Event replay failed for {event.type.value}: {e}")
                    if not self._should_continue_on_error():
                        break

            logger.debug("Event replay completed")

    def replay_events_sync(self, events: list[Event], handler: Callable[[Event], None]) -> None:
        """Replay events synchronously without timing.

        Args:
            events: Events to replay.
            handler: Callable invoked for each event.

        Returns:
            None
        """
        with self._lock:
            logger.debug(f"Starting synchronous replay of {len(events)} events")

            for event in events:
                try:
                    logger.log(5, f"Replaying event {event.type.value}")
                    handler(event)
                except Exception as e:
                    logger.error(f"Event replay failed for {event.type.value}: {e}")
                    if not self._should_continue_on_error():
                        break

            logger.debug("Synchronous event replay completed")

    def _should_continue_on_error(self) -> bool:
        """Return whether replay should continue on handler errors.

        Returns:
            bool: ``True`` when replay should continue.
        """

        return True


class EventReplayAnalyzer:
    """Analyzes recorded events for debugging and performance insights."""

    def __init__(self) -> None:
        """Initialize event replay analyzer."""
        self._lock = threading.RLock()

    def analyze_events(self, events: list[Event]) -> dict[str, Any]:
        """Analyze a list of events and return statistics.

        Args:
            events: Events to analyze.

        Returns:
            dict[str, Any]: Aggregate metrics calculated for the events.
        """
        with self._lock:
            if not events:
                return {}

            analysis: dict[str, Any] = {
                "total_events": len(events),
                "event_types": {},
                "time_span": 0.0,
                "events_per_second": 0.0,
                "peak_event_rate": 0.0,
            }

            if len(events) > 1:
                # Sort by timestamp
                sorted_events = sorted(events, key=lambda e: e.timestamp)
                analysis["time_span"] = sorted_events[-1].timestamp - sorted_events[0].timestamp

                if analysis["time_span"] > 0:
                    analysis["events_per_second"] = len(events) / analysis["time_span"]

            # Count event types
            for event in events:
                event_type = event.type.value
                analysis["event_types"][event_type] = analysis["event_types"].get(event_type, 0) + 1

            # Calculate peak event rate (simplified)
            if len(events) >= 2:
                # Group events by second
                event_times = [e.timestamp for e in events]
                min_time = min(event_times)
                max_time = max(event_times)

                if max_time > min_time:
                    # Simple peak rate calculation
                    time_buckets: dict[int, int] = {}
                    for event in events:
                        bucket = int(event.timestamp - min_time)
                        time_buckets[bucket] = time_buckets.get(bucket, 0) + 1

                    analysis["peak_event_rate"] = max(time_buckets.values())

            return analysis

    def find_event_patterns(self, events: list[Event]) -> list[dict[str, Any]]:
        """Find patterns in event sequences."""
        if not events:
            return []

        patterns: list[dict[str, Any]] = []

        # Detect consecutive runs of the same event type.
        run_event_type = events[0].type.value
        run_start = 0
        for index in range(1, len(events)):
            current_type = events[index].type.value
            if current_type != run_event_type:
                run_length = index - run_start
                if run_length >= 3:
                    patterns.append(
                        {
                            "pattern": "consecutive_run",
                            "event_type": run_event_type,
                            "start_index": run_start,
                            "length": run_length,
                        }
                    )
                run_event_type = current_type
                run_start = index

        # Handle run ending at the final event.
        final_run_length = len(events) - run_start
        if final_run_length >= 3:
            patterns.append(
                {
                    "pattern": "consecutive_run",
                    "event_type": run_event_type,
                    "start_index": run_start,
                    "length": final_run_length,
                }
            )

        # Detect bursts of activity within a one second window.
        sorted_indices = sorted(enumerate(events), key=lambda item: item[1].timestamp)
        window: list[tuple[int, Event]] = []
        last_reported_end: int | None = None
        burst_min_count = 3
        burst_window_seconds = 1.0

        for index, event in sorted_indices:
            window.append((index, event))
            window_start_time = window[0][1].timestamp

            while window and event.timestamp - window_start_time > burst_window_seconds:
                window.pop(0)
                if window:
                    window_start_time = window[0][1].timestamp

            if len(window) >= burst_min_count:
                burst_start_index = window[0][0]
                burst_end_index = window[-1][0]

                if last_reported_end is not None and burst_start_index <= last_reported_end:
                    continue

                event_types = {item[1].type.value for item in window}
                patterns.append(
                    {
                        "pattern": "burst",
                        "event_type": event_types.pop() if len(event_types) == 1 else "mixed",
                        "start_index": burst_start_index,
                        "end_index": burst_end_index,
                        "count": len(window),
                        "time_span": window[-1][1].timestamp - window[0][1].timestamp,
                    }
                )
                last_reported_end = burst_end_index

        return patterns


# Utility functions
def create_replay_buffer(max_events: int = 10000) -> EventReplayBuffer:
    """Create an event replay buffer."""
    return EventReplayBuffer(max_events)


def create_event_replayer() -> EventReplayer:
    """Create an event replayer.

    Returns:
        EventReplayer: New replayer instance.
    """
    return EventReplayer()


def create_replay_analyzer() -> EventReplayAnalyzer:
    """Create an event replay analyzer.

    Returns:
        EventReplayAnalyzer: New analyzer instance.
    """
    return EventReplayAnalyzer()
