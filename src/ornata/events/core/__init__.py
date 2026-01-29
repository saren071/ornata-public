"""Auto-generated exports for ornata.events.core."""

from __future__ import annotations

from . import bus, object_pool, subsystem
from .bus import (
    EventBus,
    GlobalEventBus,
    LockFreeEventQueue,
    SubsystemEventBus,
)
from .object_pool import (
    EventObjectPool,
    EventPool,
    PooledComponentEvent,
    PooledEvent,
    PooledKeyEvent,
    PooledMouseEvent,
    get_event_object_pool,
    pooled_component_event,
    pooled_event,
    pooled_key_event,
    pooled_mouse_event,
)
from .subsystem import (
    EventSubsystem,
    add_event_listener,
    create_event_subsystem,
    dispatch_cross_subsystem_event,
)

__all__ = [
    "EventBus",
    "EventObjectPool",
    "EventPool",
    "EventSubsystem",
    "GlobalEventBus",
    "LockFreeEventQueue",
    "PooledComponentEvent",
    "PooledEvent",
    "PooledKeyEvent",
    "PooledMouseEvent",
    "SubsystemEventBus",
    "add_event_listener",
    "bus",
    "create_event_subsystem",
    "dispatch_cross_subsystem_event",
    "get_event_object_pool",
    "object_pool",
    "pooled_component_event",
    "pooled_event",
    "pooled_key_event",
    "pooled_mouse_event",
    "subsystem",
]
