""" Events Dataclasses for Ornata """

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ornata.definitions.enums import EventPriority, EventType, KeyEventType, MouseEventType

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from ornata.api.exports.events import EventFilter, EventHandler


def _default_route_mask() -> int:
    """Return the default routing mask for events."""
    from ornata.definitions.constants import ROUTE_FILTER, ROUTE_HANDLER
    return ROUTE_FILTER | ROUTE_HANDLER


def _default_timestamp() -> float:
    """Return the default timestamp for events."""
    from ornata.definitions.constants import ZERO_TIME
    return ZERO_TIME


@dataclass(slots=True)
class EventPoolConfig:
    """Configuration for event object pooling behavior."""
    max_pool_size: int = 1000
    max_idle_time: float = 300.0
    cleanup_interval: float = 60.0
    enable_weak_refs: bool = False


@dataclass(slots=True)
class EventPoolStats:
    """Statistics for event pool usage and performance."""
    created: int = 0
    reused: int = 0
    returned: int = 0
    evicted: int = 0
    garbage_collected: int = 0
    pool_size: int = 0
    hit_rate: float = 0.0


@dataclass(slots=True)
class Event:
    """Ultra-lightweight event for microsecond performance."""
    type: EventType = EventType.TICK
    data: Any = None
    priority: EventPriority = EventPriority.NORMAL
    route_mask: int = field(default_factory=_default_route_mask)
    propagation_stopped: bool = False
    timestamp: float = field(default_factory=_default_timestamp)
    source: str = ""
    target: str = ""
    _shared_data: Any = None

    def stop_propagation(self) -> None:
        self.propagation_stopped = True


@dataclass(slots=True)
class EventHandlerWrapper:
    """Internal structure tracking handler metadata."""
    handler: Callable[[Event], bool] | EventHandler
    priority: int
    name: str
    identifier: str

    def should_handle(self, event: Event) -> bool:
        """Return whether the wrapped handler should run for the event."""
        # Note: Runtime import check avoided for performance, assumes correct typing
        can_handle = getattr(self.handler, "can_handle", None)
        if callable(can_handle):
            return bool(can_handle(event))
        return True

    def execute(self, event: Event) -> bool:
        """Execute the wrapped handler against the event."""
        handle_event = getattr(self.handler, "handle_event", None)
        if callable(handle_event):
            return bool(handle_event(event))

        if callable(self.handler):
            return bool(self.handler(event))

        return False


@dataclass(slots=True)
class EventFilterWrapper:
    """Wrapper storing filter metadata for priority ordering."""
    filter_obj: EventFilter
    priority: int
    identifier: str


@dataclass(slots=True, frozen=True)
class KeyEvent:
    """Keyboard event data."""
    event_type: KeyEventType
    key: str
    char: str | None = None
    modifiers: frozenset[str] = field(default_factory=frozenset)
    ctrl: bool = False
    alt: bool = False
    shift: bool = False
    repeat: bool = False
    location: str = "standard"


@dataclass(slots=True, frozen=True)
class MouseEvent:
    """Mouse event data."""
    event_type: MouseEventType
    x: int
    y: int
    button: int | None = None
    button_name: str | None = None
    modifiers: frozenset[str] = field(default_factory=frozenset)
    delta_x: int = 0
    delta_y: int = 0


@dataclass(slots=True)
class QuitEvent:
    """Event indicating the application should quit."""


@dataclass(slots=True)
class TickEvent:
    """Event indicating a tick of the clock."""
    dt: float = 0.0


@dataclass(slots=True)
class BatchedEvent:
    """Container for multiple coalesced events of the same type."""
    event_type: EventType
    events: list[Event] = field(default_factory=list)
    count: int = 0


@dataclass(slots=True)
class ComponentEvent:
    """Describes a runtime event emitted by or about a component."""
    name: str
    component_id: str | None
    payload: object | None = None
    timestamp: float | None = None
    metadata: Mapping[str, object] | None = None
    component_type: str | None = None
    parent_id: str | None = None
    properties: dict[str, Any] = field(default_factory=dict)

__all__ = [
    "BatchedEvent",
    "ComponentEvent",
    "Event",
    "EventFilterWrapper",
    "EventHandlerWrapper",
    "EventPoolConfig",
    "EventPoolStats",
    "KeyEvent",
    "MouseEvent",
    "QuitEvent",
    "TickEvent",
]
