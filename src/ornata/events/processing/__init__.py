"""Auto-generated exports for ornata.events.processing."""

from __future__ import annotations

from . import async_processor, filtering, propagation
from .async_processor import (
    AsyncEventProcessor,
    BatchedEventProcessor,
    EventQueue,
)
from .filtering import (
    EventDropFilter,
    EventFilter,
    EventFilterManager,
    EventModifyFilter,
    EventThrottleFilter,
    create_drop_filter,
    create_modify_filter,
    create_throttle_filter,
)
from .propagation import EventPropagationEngine

__all__ = [
    "AsyncEventProcessor",
    "BatchedEventProcessor",
    "EventDropFilter",
    "EventFilter",
    "EventFilterManager",
    "EventModifyFilter",
    "EventPropagationEngine",
    "EventQueue",
    "EventThrottleFilter",
    "async_processor",
    "create_drop_filter",
    "create_modify_filter",
    "create_throttle_filter",
    "filtering",
    "propagation",
]
