"""Event subsystem implementation for Ornata."""

from __future__ import annotations

import copy
import threading
from typing import TYPE_CHECKING

from ornata.api.exports.definitions import EventType
from ornata.api.exports.utils import get_logger
from ornata.events.core.bus import GlobalEventBus, SubsystemEventBus
from ornata.events.handlers.handlers import EventHandler, EventHandlerManager
from ornata.events.history.replay import EventReplayBuffer, EventReplayer
from ornata.events.platform.factory import PlatformEventHandler, create_platform_handler
from ornata.events.processing.async_processor import AsyncEventProcessor
from ornata.events.processing.filtering import EventFilter, EventFilterManager

if TYPE_CHECKING:
    from collections.abc import Callable

    from ornata.api.exports.definitions import Event
    from ornata.events.core.bus import EventBus

logger = get_logger(__name__)


class EventSubsystem:
    """Coordinates event dispatch, filtering, and replay services."""

    def __init__(self) -> None:
        """Initialise subsystem state."""
        self._global_bus = GlobalEventBus()
        self._subsystem_buses: dict[str, EventBus] = {}
        self._platform_handler = self._detect_platform_handler()
        self._async_processor = AsyncEventProcessor()
        self._replay_player = EventReplayer()
        self._replay_buffer = EventReplayBuffer()
        self._filter_manager = EventFilterManager()
        self._handler_manager = EventHandlerManager()
        self._high_priority_batch: list[tuple[Event, list[str] | None]] = []
        self._lock = threading.RLock()
        self._platform_loop_started = False

        # Routing table: maps event key -> whether ANY routing work is required.
        # True  => route (there are filters, handlers, or listeners somewhere)
        # False => bypass pipeline (only optional recording)
        self._routing_table: dict[str, int] = {}
        # Pre-seed routing for all known event keys, default 0 = no routing
        for e in EventType:
            self._routing_table[e.value] = 0

        self._dirty_routing_keys: set[str] = set()

        logger.debug("EventSubsystem initialised")

    def initialize(self) -> None:
        """Initialize the event subsystem and start platform integrations.

        Returns:
            None
        """
        self.start_platform_event_loop()

    # -----------------------
    # Routing table utilities (FAST PATH VERSION)
    # -----------------------
    def update_routing_table_for(self, event_key: str) -> None:
        mask = 0

        if self._filter_manager.get_filter_count(event_key) > 0:
            from ornata.api.exports.definitions import ROUTE_FILTER
            mask |= ROUTE_FILTER

        if self._handler_manager.get_handler_count(event_key) > 0:
            from ornata.api.exports.definitions import ROUTE_HANDLER
            mask |= ROUTE_HANDLER

        if self._global_bus.get_subscriber_count(event_key) > 0:
            from ornata.api.exports.definitions import ROUTE_GLOBAL
            mask |= ROUTE_GLOBAL

        for bus in self._subsystem_buses.values():
            c = getattr(bus, "get_subscriber_count", None)
            if c and c(event_key) > 0:
                from ornata.api.exports.definitions import ROUTE_SUBSYSTEM
                mask |= ROUTE_SUBSYSTEM
                break

        self._routing_table[event_key] = mask
        self._dirty_routing_keys.discard(event_key)

    def _get_route_mask(self, event_key: str) -> int:
        """Return the routing mask for ``event_key``.

        Args:
            event_key: Canonical event key.

        Returns:
            int: Bit mask describing required pipeline work.
        """

        if event_key in self._dirty_routing_keys:
            self.update_routing_table_for(event_key)
        return self._routing_table.get(event_key, 0)

    def _should_route(self, event_key: str) -> bool:
        return (self._get_route_mask(event_key) != 0)

    def _invalidate_all_routes(self) -> None:
        """Mark every routing entry as dirty so it is recomputed lazily."""
        self._dirty_routing_keys.update(self._routing_table.keys())

    def _mark_routing_dirty(self, event_key: str) -> None:
        """Mark a single routing entry as dirty."""

        self._dirty_routing_keys.add(event_key)

    def _detect_platform_handler(self) -> PlatformEventHandler | None:
        """Return a platform handler when available.

        Returns:
            PlatformEventHandler | None: Handler instance for the current
            platform or ``None`` when no handler can operate.
        """
        try:
            handler = create_platform_handler()
        except Exception as exc:
            logger.warning("Platform handler detection failed: %s", exc)
            return None

        if handler is not None and not handler.is_available():
            logger.debug("Platform handler reported unavailable")
            return None

        return handler

    def register_subsystem(self, subsystem_name: str, bus: EventBus) -> None:
        """Register ``bus`` under ``subsystem_name`` and bridge to the global bus.

        Args:
            subsystem_name: Name identifying the subsystem.
            bus: Subsystem bus responsible for local dispatch.

        Raises:
            EventError: When the bus does not support global bridging.
        """
        with self._lock:
            if subsystem_name in self._subsystem_buses:
                logger.warning("Subsystem %s already registered; replacing", subsystem_name)

            if not isinstance(bus, SubsystemEventBus) and (not hasattr(bus, "set_global_bridge") or not hasattr(bus, "receive_global_event")):
                from ornata.api.exports.definitions import EventError
                raise EventError(
                    f"Event bus for subsystem '{subsystem_name}' does not support global bridging",
                )

            self._subsystem_buses[subsystem_name] = bus
            self._global_bus.connect_subsystem_bus(subsystem_name, bus)
            logger.debug("Registered subsystem bus for %s", subsystem_name)

        # Subsystem listener landscape changed: invalidate all route decisions.
        self._invalidate_all_routes()

    def dispatch_event(self, event: Event, target_subsystems: list[str] | None = None) -> None:
        """Dispatch ``event`` synchronously to registered listeners.

        Args:
            event: Event to dispatch.
            target_subsystems: Optional list limiting dispatch to specific subsystems.
        """
        if logger.isEnabledFor(5):  # TRACE level
            logger.log(5, "Dispatching %s to %s", event.type.value, target_subsystems)
        self._dispatch_event_internal(event, target_subsystems, record_event=True)

    def dispatch_event_async(self, event: Event, target_subsystems: list[str] | None = None) -> None:
        """Dispatch ``event`` using the asynchronous processor.

        Args:
            event: Event to dispatch asynchronously.
            target_subsystems: Optional list limiting dispatch to specific subsystems.
        """
        from ornata.api.exports.definitions import EventPriority
        if event.priority in (EventPriority.HIGH, EventPriority.CRITICAL):
            self._process_high_priority_event(event, target_subsystems)
        else:
            targets = list(target_subsystems) if target_subsystems else None
            event_copy = self._clone_event(event)

            def runner(dispatched_event: Event) -> None:
                self._dispatch_event_internal(dispatched_event, targets, record_event=True)

            self._async_processor.process_event_async(event_copy, runner)

    def dispatch_many(self, events: list[Event], target_subsystems: list[str] | None = None) -> None:
        """Ultra-fast bulk dispatch for benchmark / high throughput loops."""
        dispatch_internal = self._dispatch_event_internal  # local bind avoids attribute lookup in loop local
        record_event = True
        for event in events:
            dispatch_internal(event, target_subsystems, record_event)

    def add_global_listener(self, event_type: str | EventType, handler: Callable[[Event], None]) -> None:
        """Subscribe ``handler`` to global events of ``event_type``.

        Args:
            event_type: Event type identifier or :class:`EventType` value.
            handler: Callable invoked when the event fires globally.
        """
        event_key = self._normalize_event_type(event_type)
        with self._lock:
            self._global_bus.subscribe(event_key, handler)
            logger.debug("Added global listener for %s", event_key)
        # Update only the affected key
        self._mark_routing_dirty(event_key)

    def remove_global_listener(self, event_type: str | EventType, handler: Callable[[Event], None]) -> None:
        """Remove ``handler`` from the global bus.

        Args:
            event_type: Event type identifier or enum value.
            handler: Handler previously registered with :meth:`add_global_listener`.
        """

        event_key = self._normalize_event_type(event_type)
        with self._lock:
            self._global_bus.unsubscribe(event_key, handler)
            logger.debug("Removed global listener for %s", event_key)
        # Update only the affected key
        self.update_routing_table_for(event_key)

    def register_handler(
        self,
        event_type: str | EventType,
        handler: Callable[[Event], bool] | EventHandler,
        priority: int = 0,
        name: str | None = None,
    ) -> str:
        """Register a pre-dispatch handler.

        Args:
            event_type: Event type identifier or enum value.
            handler: Callable or :class:`EventHandler` controlling propagation.
            priority: Higher priorities execute first.
            name: Optional descriptive name for logging.

        Returns:
            str: Identifier used for later removal.
        """

        event_key = self._normalize_event_type(event_type)
        handler_id = self._handler_manager.register_handler(event_key, handler, priority, name)
        logger.debug("Registered handler %s for %s", handler_id, event_key)
        # Update only the affected key
        self.update_routing_table_for(event_key)
        return handler_id

    def unregister_handler(self, handler_id: str) -> bool:
        """Remove a handler registered with :meth:`register_handler`.

        Args:
            handler_id: Identifier returned during registration.

        Returns:
            bool: ``True`` when the handler was removed.
        """

        event_key, _, _ = handler_id.partition(":")
        removed = self._handler_manager.unregister_handler(handler_id)
        if removed:
            logger.debug("Removed handler %s", handler_id)
            self._mark_routing_dirty(event_key)
        return removed

    def register_filter(self, event_type: str | EventType, filter_: EventFilter, priority: int = 0) -> str:
        """Register an event filter.

        Args:
            event_type: Event type identifier or enum value.
            filter_: Filter implementation invoked before dispatch.
            priority: Higher priorities run earlier.

        Returns:
            str: Identifier for later removal.
        """

        event_key = self._normalize_event_type(event_type)
        filter_id = self._filter_manager.add_filter(event_key, filter_, priority)
        logger.debug("Registered filter %s for %s", filter_id, event_key)
        # Update only the affected key
        self.update_routing_table_for(event_key)
        return filter_id

    def unregister_filter(self, filter_id: str) -> bool:
        """Remove a filter previously registered with :meth:`register_filter`.

        Args:
            filter_id: Identifier returned during registration.

        Returns:
            bool: ``True`` when the filter was removed.
        """

        event_key, _, _ = filter_id.partition(":")
        removed = self._filter_manager.remove_filter(filter_id)
        if removed:
            logger.debug("Removed filter %s", filter_id)
            self._mark_routing_dirty(event_key)
        return removed

    def get_subsystem_bus(self, subsystem_name: str) -> EventBus:
        """Return the bus registered under ``subsystem_name``.

        Args:
            subsystem_name: Name used during :meth:`register_subsystem`.

        Returns:
            EventBus: Registered subsystem bus.

        Raises:
            EventError: When the subsystem has not been registered.
        """

        with self._lock:
            try:
                return self._subsystem_buses[subsystem_name]
            except KeyError as exc:
                from ornata.api.exports.definitions import EventError
                raise EventError(f"Subsystem '{subsystem_name}' is not registered") from exc

    def list_subsystems(self) -> list[str]:
        """Return the list of registered subsystem names.

        Returns:
            list[str]: Names of registered subsystems.
        """

        with self._lock:
            return list(self._subsystem_buses.keys())

    def start_platform_event_loop(self) -> None:
        """Start the platform loop when a handler is available."""

        if self._platform_handler is None:
            return

        with self._lock:
            if self._platform_loop_started:
                return
            self._platform_handler.start_event_loop()
            self._platform_loop_started = True

        logger.debug("Platform event loop started")

    def stop_platform_event_loop(self) -> None:
        """Stop the platform loop if it is currently running."""

        if self._platform_handler is None:
            return

        with self._lock:
            if not self._platform_loop_started:
                return
            self._platform_handler.stop_event_loop()
            self._platform_loop_started = False

        logger.debug("Platform event loop stopped")

    def pump_platform_events(self) -> None:
        """Poll the platform handler and dispatch collected events."""

        if self._platform_handler is None:
            return

        for platform_event in self._platform_handler.poll_events():
            self.dispatch_event(platform_event)

    def shutdown(self) -> None:
        """Shutdown asynchronous resources and platform integrations."""

        self.stop_platform_event_loop()
        self._async_processor.shutdown()

    def get_async_processor(self) -> AsyncEventProcessor:
        """Return the asynchronous processor for diagnostics.

        Returns:
            AsyncEventProcessor: Processor instance.
        """

        return self._async_processor

    def get_replay_buffer(self) -> EventReplayBuffer:
        """Return the replay buffer for inspection.

        Returns:
            EventReplayBuffer: Buffer instance storing recorded events.
        """

        return self._replay_buffer

    def start_replay(self, session_id: str) -> None:
        """Begin recording events into the replay buffer.

        Args:
            session_id: Identifier for the recording session.
        """

        with self._lock:
            self._replay_buffer.start_recording(session_id)
            logger.debug("Started replay recording for session %s", session_id)

    def stop_replay(self) -> list[Event]:
        """Stop recording and return captured events.

        Returns:
            list[Event]: Recorded events since :meth:`start_replay`.
        """

        with self._lock:
            events = self._replay_buffer.stop_recording()
            logger.debug("Stopped replay recording, captured %d events", len(events))
            return events

    def replay_events(
        self,
        events: list[Event],
        handler: Callable[[Event], None],
        speed_multiplier: float = 1.0,
        real_time: bool = True,
    ) -> None:
        """Replay ``events`` using :class:`EventReplayer`.

        Args:
            events: Events to replay.
            handler: Callback invoked for each event.
            speed_multiplier: Playback speed multiplier.
            real_time: When ``True`` respects original timing gaps.
        """

        with self._lock:
            self._replay_player.replay_events(events, handler, speed_multiplier, real_time)
            logger.debug("Replayed %d events at %.2fx", len(events), speed_multiplier)

    def replay_events_sync(self, events: list[Event], handler: Callable[[Event], None]) -> None:
        """Replay ``events`` synchronously without timing delays.

        Args:
            events: Events to replay.
            handler: Callback invoked for each event.
        """

        with self._lock:
            self._replay_player.replay_events_sync(events, handler)
            logger.debug("Synchronously replayed %d events", len(events))

    def _normalize_event_type(self, event_type: str | EventType) -> str:
        """Return a canonical string representation of ``event_type``.

        Args:
            event_type: Event type identifier or enum value.

        Returns:
            str: Canonical event type key.
        """

        return event_type.value if isinstance(event_type, EventType) else event_type

    def _dispatch_event_internal(
        self,
        event: Event,
        target_subsystems: list[str] | None,
        record_event: bool,
    ) -> None:
        event_key = event.type.value
        routing_mask = self._get_route_mask(event_key)

        # nothing interested, only optional record
        if routing_mask == 0:
            if record_event and self._replay_buffer.is_recording():
                self._replay_buffer.record_event(event)
            return

        # filters
        from ornata.api.exports.definitions import ROUTE_FILTER
        if (routing_mask & ROUTE_FILTER) == 0:
            filtered_event = event
        else:
            filtered_event = self._filter_manager.apply_filters(event)

        if filtered_event is None:
            return

        # handlers
        from ornata.api.exports.definitions import ROUTE_HANDLER
        if routing_mask & ROUTE_HANDLER:
            should_stop = self._handler_manager.execute_handlers(filtered_event)
            if record_event and self._replay_buffer.is_recording():
                self._replay_buffer.record_event(filtered_event)
            if should_stop or filtered_event.propagation_stopped:
                return
        else:
            if record_event and self._replay_buffer.is_recording():
                self._replay_buffer.record_event(filtered_event)

        # dispatch
        if target_subsystems is None:
            try:
                self._global_bus.publish(filtered_event)
            except Exception:
                pass
            return

        # targeted subsystem path
        with self._lock:
            target_buses = [(name, self._subsystem_buses.get(name)) for name in target_subsystems]

        for subsystem_name, bus in target_buses:
            if bus is None:
                logger.warning("Unknown subsystem %s for event dispatch", subsystem_name)
                continue
            try:
                bus.publish(filtered_event)
            except Exception:
                pass

    def _clone_event(self, event: Event) -> Event:
        """Return a shallow copy of ``event`` for asynchronous dispatch.

        Args:
            event: Event to clone.

        Returns:
            Event: Cloned event instance.
        """
        data_copy = None if event.data is None else copy.copy(event.data)
        from ornata.api.exports.definitions import Event
        return Event(
            type=event.type,
            data=data_copy,
            timestamp=event.timestamp,
            source=event.source,
            target=event.target,
            propagation_stopped=event.propagation_stopped,
        )

    def _process_high_priority_event(self, event: Event, target_subsystems: list[str] | None) -> None:
        """Process high-priority events with batching and immediate dispatch.

        Args:
            event: High-priority event to process.
            target_subsystems: Optional list of target subsystems.
        """
        self._high_priority_batch.append((event, target_subsystems))
        if len(self._high_priority_batch) >= 5:
            self._flush_high_priority_batch()

    def _flush_high_priority_batch(self) -> None:
        """Flush the high-priority event batch immediately."""
        if not self._high_priority_batch:
            return

        batch = list(self._high_priority_batch)
        self._high_priority_batch.clear()

        for event, targets in batch:
            self._dispatch_event_internal(event, targets, record_event=True)


def create_event_subsystem() -> EventSubsystem:
    """Create and return a new :class:`EventSubsystem` instance.

    Returns:
        EventSubsystem: Newly created subsystem.
    """

    return EventSubsystem()


def dispatch_cross_subsystem_event(event: Event, source_subsystem: str, target_subsystems: list[str]) -> None:
    """Dispatch ``event`` from ``source_subsystem`` to ``target_subsystems``.

    Args:
        event: Event to dispatch across subsystems.
        source_subsystem: Name of the originating subsystem.
        target_subsystems: Target subsystem names.

    Raises:
        EventError: When dispatch fails.
    """

    try:
        subsystem = EventSubsystem()
        event.source = source_subsystem
        subsystem.dispatch_event(event, target_subsystems)
        logger.debug(
            "Cross-subsystem event dispatched from %s to %s",
            source_subsystem,
            target_subsystems,
        )
    except Exception as exc:
        from ornata.api.exports.definitions import EventError
        logger.error("Failed to dispatch cross-subsystem event: %s", exc)
        raise EventError(f"Cross-subsystem event dispatch failed: {exc}") from exc


def add_event_listener(
    event_type: str | EventType,
    handler: Callable[[Event], None],
    subsystem_filter: str | None = None,
) -> Callable[[], None]:
    """Register ``handler`` for ``event_type`` with optional subsystem scoping.

    Args:
        event_type: Event type identifier or enum value.
        handler: Callable invoked when the event fires.
        subsystem_filter: Optional subsystem name restricting registration.

    Returns:
        Callable[[], None]: Function that removes the listener when invoked.

    Raises:
        EventError: When registration fails.
    """

    try:
        subsystem = EventSubsystem()
        from ornata.api.exports.definitions import EventType
        event_key = event_type.value if isinstance(event_type, EventType) else event_type

        if subsystem_filter:
            bus = subsystem.get_subsystem_bus(subsystem_filter)
            unsubscribe_func = bus.subscribe(event_key, handler)
            # Listener landscape changed for this key
            subsystem.update_routing_table_for(event_key)

            def remove_listener() -> None:
                unsubscribe_func()
                subsystem.update_routing_table_for(event_key)

            logger.debug("Added listener for %s on subsystem %s", event_key, subsystem_filter)
            return remove_listener

        subsystem.add_global_listener(event_key, handler)
        logger.debug("Added global listener for %s", event_key)

        def remove_listener() -> None:
            subsystem.remove_global_listener(event_key, handler)

        return remove_listener
    except Exception as exc:
        from ornata.api.exports.definitions import EventError
        logger.error("Failed to add event listener: %s", exc)
        raise EventError(f"Event listener registration failed: {exc}") from exc
