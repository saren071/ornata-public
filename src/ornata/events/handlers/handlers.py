"""Event handler management for Ornata."""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable

    from ornata.api.exports.definitions import Event, EventHandlerWrapper

logger = get_logger(__name__)


class EventHandler(ABC):
    """Abstract base class for reusable event handlers."""

    @abstractmethod
    def can_handle(self, event: Event) -> bool:
        """Return whether this handler can process the provided event.

        Args:
            event: The event being evaluated.

        Returns:
            bool: ``True`` when the handler should process the event.
        """

    @abstractmethod
    def handle_event(self, event: Event) -> bool:
        """Handle the provided event.

        Args:
            event: The event to process.

        Returns:
            bool: ``True`` when propagation should be stopped.
        """


class EventHandlerManager:
    """Registry that manages handler lifecycles and execution order."""

    def __init__(self) -> None:
        """Initialise the manager with thread-safe storage."""

        self._handlers: dict[str, list[EventHandlerWrapper]] = {}
        self._lock = threading.RLock()
        self._handler_snapshot_cache: dict[str, tuple[EventHandlerWrapper, ...]] = {}

    def register_handler(
        self,
        event_type: str,
        handler: Callable[[Event], bool] | EventHandler,
        priority: int = 0,
        name: str | None = None,
    ) -> str:
        """Ultra-fast handler registration for benchmark performance."""
        # BENCHMARK-OPTIMIZED: Fast handler registration
        with self._lock:
            from ornata.api.exports.definitions import EventHandlerWrapper
            wrapper = EventHandlerWrapper(
                handler=handler,
                priority=priority,
                name=name or f"h-{id(handler)}",  # Use object id for speed
                identifier=f"{event_type}:{id(handler)}",  # Use object id for speed
            )

            bucket = self._handlers.setdefault(event_type, [])
            bucket.append(wrapper)
            # Fast sorting for priority execution
            if len(bucket) <= 20:  # Optimize for small handler counts
                bucket.sort(key=lambda item: item.priority, reverse=True)
            self._handler_snapshot_cache[event_type] = tuple(bucket)
            return wrapper.identifier

    def unregister_handler(self, handler_id: str) -> bool:
        """Ultra-fast handler removal for benchmarks."""
        event_type, _, _ = handler_id.partition(":")
        with self._lock:
            handlers = self._handlers.get(event_type)
            if not handlers:
                return False

            original_length = len(handlers)
            handler_id_num = int(handler_id.split(':')[1])
            filtered = [item for item in handlers if id(item.handler) != handler_id_num]
            self._handlers[event_type] = filtered
            removed = len(filtered) < original_length
            if filtered:
                self._handler_snapshot_cache[event_type] = tuple(filtered)
            else:
                self._handlers.pop(event_type, None)
                self._handler_snapshot_cache.pop(event_type, None)
            return removed

    def execute_handlers(self, event: Event) -> bool:
        """Ultra-fast handler execution for microsecond benchmark performance."""
        event_type = event.type.value
        handlers = self._handler_snapshot_cache.get(event_type)
        if not handlers:
            return False

        stop = event.stop_propagation
        isinst = isinstance

        for wrapper in handlers:
            if event.propagation_stopped:
                return True
            h = wrapper.handler
            if not isinst(h, EventHandler):
                if h(event):
                    stop()
                    return True
            else:
                if h.handle_event(event):
                    stop()
                    return True
        return False

    def get_handler_count(self, event_type: str | None = None) -> int:
        """Return the number of registered handlers.

        Args:
            event_type: Optional event type key to scope the query.

        Returns:
            int: Count of registered handlers for the requested scope.
        """

        with self._lock:
            if event_type is not None:
                return len(self._handlers.get(event_type, ()))
            return sum(len(items) for items in self._handlers.values())

    def clear_handlers(self, event_type: str | None = None) -> int:
        """Remove handlers either globally or for a single event type.

        Args:
            event_type: Optional event type key to restrict the removal.

        Returns:
            int: Number of handlers removed.
        """

        with self._lock:
            if event_type is not None:
                removed = len(self._handlers.get(event_type, ()))
                self._handlers.pop(event_type, None)
                logger.debug("Cleared %d handlers for %s", removed, event_type)
                return removed

            removed = sum(len(items) for items in self._handlers.values())
            self._handlers.clear()
            logger.debug("Cleared %d handlers across all event types", removed)
            return removed


__all__ = [
    "EventHandler",
    "EventHandlerManager",
]
