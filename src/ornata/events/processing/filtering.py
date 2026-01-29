"""Event filtering and transformation for Ornata."""

from __future__ import annotations

import threading
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable

    from ornata.api.exports.definitions import Event, EventFilterWrapper

logger = get_logger(__name__)


class EventFilter(ABC):
    """Abstract base class for transforming or dropping events."""

    @abstractmethod
    def filter_event(self, event: Event) -> Event | None:
        """Filter or transform an event.

        Args:
            event: The event to evaluate.

        Returns:
            Event | None: ``None`` when the event should be dropped, otherwise
            the (possibly modified) event instance.
        """


class EventFilterManager:
    """Thread-safe registry for event filters organised by event type."""

    def __init__(self) -> None:
        self._filters: dict[str, list[EventFilterWrapper]] = {}
        self._lock = threading.RLock()
        # NEW: immutable snapshots for publish-time reads
        self._snapshots: dict[str, tuple[EventFilterWrapper, ...]] = {}

    def add_filter(self, event_type: str, filter_obj: EventFilter, priority: int = 0) -> str:
        """Ultra-fast filter registration for benchmark performance."""
        from ornata.api.exports.definitions import EventFilterWrapper
        ident = f"{event_type}:{id(filter_obj)}"
        with self._lock:
            bucket = self._filters.setdefault(event_type, [])
            bucket.append(EventFilterWrapper(filter_obj, priority, ident))
            # keep priority stable if you later sort; here we keep append order
            self._snapshots[event_type] = tuple(bucket)
        return ident

    def remove_filter(self, filter_id: str) -> bool:
        """Ultra-fast filter removal for benchmarks."""
        event_type, _, ident = filter_id.partition(":")
        if not ident:
            return False
        target_id = int(ident)
        with self._lock:
            filters = self._filters.get(event_type)
            if not filters:
                return False
            original_len = len(filters)
            # BUGFIX: compare id(filter_obj), not id(wrapper)
            new_list = [w for w in filters if id(w.filter_obj) != target_id]
            if not new_list:
                self._filters.pop(event_type, None)
                self._snapshots.pop(event_type, None)
            else:
                self._filters[event_type] = new_list
                self._snapshots[event_type] = tuple(new_list)
            return len(new_list) < original_len

    def apply_filters(self, event: Event) -> Event | None:
        """Ultra-fast filter application for microsecond benchmark performance."""
        # NEW: lock-free read of immutable tuple
        filters = self._snapshots.get(event.type.value)
        if not filters:
            return event
        for wrapper in filters:
            result = wrapper.filter_obj.filter_event(event)
            if result is None:
                return None
            event = result
        return event

    def get_filter_count(self, event_type: str | None = None) -> int:
        """Return the number of registered filters.

        Args:
            event_type: Optional event type key to scope the query.

        Returns:
            int: Number of filters registered for the given scope.
        """

        with self._lock:
            if event_type is not None:
                return len(self._filters.get(event_type, ()))
            return sum(len(items) for items in self._filters.values())


class EventTransformer(EventFilter):
    """Base class for filters that transform rather than drop events."""

    def filter_event(self, event: Event) -> Event | None:
        """Return the unmodified event by default.

        Args:
            event: The event to return unchanged.

        Returns:
            Event | None: The original event instance.
        """

        return event


class EventDropFilter(EventFilter):
    """Filter implementation that drops events using a predicate."""

    def __init__(self, predicate: Callable[[Event], bool]) -> None:
        """Store the predicate used to evaluate events.

        Args:
            predicate: Callable returning ``True`` when the event should be dropped.
        """

        self._predicate = predicate

    def filter_event(self, event: Event) -> Event | None:
        """Drop the event when the predicate evaluates to ``True``.

        Args:
            event: The event being evaluated.

        Returns:
            Event | None: ``None`` when the predicate matches, otherwise the original event.
        """

        if self._predicate(event):
            logger.log(5, "Dropping event %s based on predicate", event.type.value)
            return None
        return event


class EventModifyFilter(EventTransformer):
    """Filter implementation that mutates event data."""

    def __init__(self, modifier: Callable[[Event], Event]) -> None:
        """Store the modifier used to transform events.

        Args:
            modifier: Callable returning the modified event.
        """

        self._modifier = modifier

    def filter_event(self, event: Event) -> Event | None:
        """Apply the modifier and return its result.

        Args:
            event: The event to transform.

        Returns:
            Event | None: The modified event. Failures fall back to the original event.
        """

        try:
            transformed = self._modifier(event)
            logger.log(5, "Modified event %s", event.type.value)
            return transformed
        except Exception as exc:
            logger.warning("Modifier failed for %s: %s", event.type.value, exc)
            return event


class EventThrottleFilter(EventFilter):
    """Rate-limiting filter preventing event floods."""

    def __init__(self, event_type: str, max_per_second: int = 10) -> None:
        """Initialise the rate limiter.

        Args:
            event_type: Event type key to throttle.
            max_per_second: Maximum number of events allowed per second.
        """

        self._event_type = event_type
        self._max_per_second = max_per_second
        self._timestamps: list[float] = []
        self._lock = threading.RLock()

    def filter_event(self, event: Event) -> Event | None:
        """Drop events when the rate exceeds the configured limit.

        Args:
            event: The event to evaluate.

        Returns:
            Event | None: ``None`` when the rate limit is exceeded.
        """

        if event.type.value != self._event_type:
            return event

        with self._lock:
            now = time.perf_counter()
            self._timestamps = [stamp for stamp in self._timestamps if now - stamp < 1.0]

            if len(self._timestamps) >= self._max_per_second:
                logger.log(5, "Throttling event %s", event.type.value)
                return None

            self._timestamps.append(now)
            return event


def create_drop_filter(predicate: Callable[[Event], bool]) -> EventDropFilter:
    """Factory for :class:`EventDropFilter`.

    Args:
        predicate: Callable returning ``True`` when the event should be dropped.

    Returns:
        EventDropFilter: Configured drop filter instance.
    """

    return EventDropFilter(predicate)


def create_modify_filter(modifier: Callable[[Event], Event]) -> EventModifyFilter:
    """Factory for :class:`EventModifyFilter`.

    Args:
        modifier: Callable returning the modified event.

    Returns:
        EventModifyFilter: Configured modify filter instance.
    """

    return EventModifyFilter(modifier)


def create_throttle_filter(event_type: str, max_per_second: int = 10) -> EventThrottleFilter:
    """Factory for :class:`EventThrottleFilter`.

    Args:
        event_type: Event type key to throttle.
        max_per_second: Maximum number of events allowed per second.

    Returns:
        EventThrottleFilter: Configured throttle filter instance.
    """

    return EventThrottleFilter(event_type, max_per_second)


__all__ = [
    "EventDropFilter",
    "EventFilter",
    "EventFilterManager",
    "EventModifyFilter",
    "EventThrottleFilter",
    "create_drop_filter",
    "create_modify_filter",
    "create_throttle_filter",
]
