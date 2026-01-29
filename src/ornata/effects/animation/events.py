"""Animation events and event handling."""

import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

from ornata.api.exports.definitions import AnimationEvent, AnimationEventType
from ornata.api.exports.utils import get_logger

logger = get_logger(__name__)


class AnimationEventDispatcher:
    """Dispatches animation events to listeners."""

    def __init__(self) -> None:
        """Initialize the event dispatcher."""
        self._listeners: dict[AnimationEventType, list[Callable[[AnimationEvent], None]]] = {}
        self._lock = threading.RLock()

    def add_listener(self, event_type: AnimationEventType, listener: Callable[[AnimationEvent], None]) -> None:
        """Add an event listener.

        Args:
            event_type: Type of event to listen for.
            listener: Callback function to handle the event.
        """
        with self._lock:
            if event_type not in self._listeners:
                self._listeners[event_type] = []
            self._listeners[event_type].append(listener)
            logger.debug(f"Added listener for {event_type.value}")

    def remove_listener(self, event_type: AnimationEventType, listener: Callable[[AnimationEvent], None]) -> None:
        """Remove an event listener.

        Args:
            event_type: Type of event to stop listening for.
            listener: Callback function to remove.
        """
        with self._lock:
            if event_type in self._listeners:
                try:
                    self._listeners[event_type].remove(listener)
                    logger.debug(f"Removed listener for {event_type.value}")
                except ValueError:
                    logger.warning(f"Listener not found for {event_type.value}")

    def dispatch_event(self, event: AnimationEvent) -> None:
        """Dispatch an event to all listeners.

        Args:
            event: The event to dispatch.
        """
        with self._lock:
            if event.event_type in self._listeners:
                for listener in self._listeners[event.event_type]:
                    try:
                        listener(event)
                        logger.log(5, f"Dispatched {event.event_type.value} event")  # TRACE level
                    except Exception as e:
                        logger.error(f"Animation event listener failed: {e}")

    def clear_listeners(self, event_type: AnimationEventType | None = None) -> None:
        """Clear all listeners or listeners for a specific event type.

        Args:
            event_type: Optional event type to clear listeners for.
        """
        with self._lock:
            if event_type is None:
                count = sum(len(listeners) for listeners in self._listeners.values())
                self._listeners.clear()
                logger.debug(f"Cleared all {count} animation event listeners")
            else:
                count = len(self._listeners.get(event_type, []))
                self._listeners.pop(event_type, None)
                logger.debug(f"Cleared {count} listeners for {event_type.value}")


# Global event dispatcher instance
_event_dispatcher = AnimationEventDispatcher()


def get_event_dispatcher() -> AnimationEventDispatcher:
    """Get the global animation event dispatcher.

    Returns:
        The global event dispatcher instance.
    """
    return _event_dispatcher


def dispatch_animation_event(event_type: AnimationEventType, animation_id: str | None = None, sequence_id: str | None = None, progress: float = 0.0) -> None:
    """Dispatch an animation event.

    Args:
        event_type: Type of animation event.
        animation_id: Optional animation ID.
        sequence_id: Optional sequence ID.
        progress: Animation progress (0.0 to 1.0).
    """
    event = AnimationEvent(event_type=event_type, animation_id=animation_id, sequence_id=sequence_id, progress=progress)
    _event_dispatcher.dispatch_event(event)
    logger.debug(f"Animation event: {event_type.value} (id: {animation_id})")
