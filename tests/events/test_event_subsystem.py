"""Coverage for Ornata's event subsystem and handler/filter management."""

from __future__ import annotations

from collections import deque

import pytest

from ornata.api.exports.events import EventHandlerManager
from ornata.definitions.dataclasses.events import Event
from ornata.definitions.enums import EventPriority, EventType
from ornata.events.core.bus import EventBus, GlobalEventBus
from ornata.events.core.subsystem import EventSubsystem
from ornata.events.platform.cli import create_cli_handler
from ornata.events.processing.async_processor import AsyncEventProcessor
from ornata.events.processing.filtering import EventFilter, EventFilterManager


class _RecordingFilter(EventFilter):
    """Filter that records events without dropping them."""

    def __init__(self) -> None:
        self.events: list[Event] = []

    def filter_event(self, event: Event) -> Event | None:
        self.events.append(event)
        return event


class _DropFilter(EventFilter):
    """Filter that drops every event passed to it."""

    def filter_event(self, event: Event) -> Event | None:
        return None


@pytest.fixture
def subsystem() -> EventSubsystem:
    """Return an EventSubsystem with deterministic async/platform behavior."""

    subsystem = EventSubsystem()
    subsystem._platform_handler = create_cli_handler()  # noqa: SLF001

    class _ImmediateAsyncProcessor(AsyncEventProcessor):
        def __init__(self) -> None:
            super().__init__(max_workers=1)

        def process_event_async(self, event: Event, handler):  # type: ignore[no-untyped-def, override]
            handler(event)

        def shutdown(self, wait: bool = True) -> None:  # type: ignore[override]
            super().shutdown(wait)

    subsystem._async_processor = _ImmediateAsyncProcessor()  # noqa: SLF001
    return subsystem


def test_event_subsystem_routes_filters_handlers(subsystem: EventSubsystem) -> None:
    """Filters should run before handlers, and global listeners should receive events."""

    recorded: list[str] = []

    def handler(event: Event) -> bool:
        recorded.append(event.type.value)
        return False

    recording_filter = _RecordingFilter()
    subsystem.add_global_listener(
        EventType.TICK,
        lambda event: recorded.append(f"global:{event.type.value}"),
    )
    subsystem.register_handler(EventType.TICK, handler, priority=5)
    subsystem.register_filter(EventType.TICK, recording_filter)

    tick = Event(type=EventType.TICK)
    subsystem.dispatch_event(tick)

    assert recorded == ["tick", "global:tick"]
    assert recording_filter.events and recording_filter.events[0] is tick


def test_event_subsystem_async_dispatch_clones_events(subsystem: EventSubsystem) -> None:
    """Async dispatch should clone events except for high-priority fast paths."""

    dispatched: deque[Event] = deque()

    def handler(event: Event) -> None:
        dispatched.append(event)

    subsystem.add_global_listener(EventType.COMPONENT_UPDATE, handler)
    slow_event = Event(type=EventType.COMPONENT_UPDATE, priority=EventPriority.NORMAL)
    subsystem.dispatch_event_async(slow_event)
    assert dispatched and dispatched[0] is not slow_event

    fast_events = [
        Event(type=EventType.COMPONENT_UPDATE, priority=EventPriority.CRITICAL)
        for _ in range(5)
    ]
    for event in fast_events:
        subsystem.dispatch_event_async(event)

    assert len(dispatched) == 1 + len(fast_events)
    assert dispatched[-1] is fast_events[-1]


def test_event_subsystem_replay_records_and_replays(subsystem: EventSubsystem) -> None:
    """Replay buffer should capture routed events and replay them through helpers."""

    replayed: list[str] = []
    subsystem.start_replay("session")
    subsystem.add_global_listener(
        EventType.LAYOUT_INVALIDATED,
        lambda event: replayed.append(event.type.value),
    )
    subsystem.dispatch_event(Event(type=EventType.LAYOUT_INVALIDATED))
    recorded = subsystem.stop_replay()
    assert recorded

    replayed.clear()
    subsystem.replay_events_sync(recorded, lambda event: replayed.append(event.type.value))
    assert replayed == [EventType.LAYOUT_INVALIDATED.value]


def test_event_handler_manager_priority_and_unregister() -> None:
    """EventHandlerManager should obey priorities and support unregistering."""

    manager = EventHandlerManager()
    call_order: list[str] = []

    def handler_factory(name: str):  # type: ignore[no-untyped-def]
        def run(event: Event) -> bool:
            call_order.append(name)
            return False

        return run

    first = manager.register_handler(EventType.TICK.value, handler_factory("high"), priority=10)
    manager.register_handler(EventType.TICK.value, handler_factory("low"), priority=0)

    manager.execute_handlers(Event(type=EventType.TICK))
    assert call_order == ["high", "low"]

    assert manager.unregister_handler(first) is True
    assert manager.execute_handlers(Event(type=EventType.TICK)) is False


def test_event_filter_manager_add_remove_and_apply() -> None:
    """EventFilterManager should add, drop, and apply filters in order."""

    manager = EventFilterManager()
    recorder = _RecordingFilter()
    dropper = _DropFilter()

    recorder_id = manager.add_filter(EventType.ANIMATION_FRAME.value, recorder)
    drop_id = manager.add_filter(EventType.ANIMATION_FRAME.value, dropper)

    event = Event(type=EventType.ANIMATION_FRAME)
    assert manager.apply_filters(event) is None
    assert recorder.events == [event]

    assert manager.remove_filter(drop_id) is True
    assert manager.apply_filters(event) is event
    assert manager.remove_filter(recorder_id) is True


def test_event_subsystem_subsystem_bus_routing() -> None:
    """Registering subsystem buses should route targeted dispatches."""

    subsystem = EventSubsystem()
    captured: list[str] = []

    class StubBus(EventBus):
        def publish(self, event: Event) -> None:  # type: ignore[override]
            captured.append(event.type.value)

    stub = StubBus()
    subsystem.register_subsystem("telemetry", stub)
    subsystem.register_handler(EventType.COMPONENT_UPDATE, lambda event: False)

    subsystem.dispatch_event(
        Event(type=EventType.COMPONENT_UPDATE),
        target_subsystems=["telemetry"],
    )
    assert captured == [EventType.COMPONENT_UPDATE.value]


def test_global_bus_bridging() -> None:
    """Global bus should forward events into subsystem listeners via snapshots."""

    global_bus = GlobalEventBus()
    subsystem_bus = EventBus()
    recorded: list[str] = []

    global_bus.subscribe(
        EventType.COMPONENT_MOUNT.value,
        lambda event: recorded.append(f"global:{event.type.value}"),
    )
    subsystem_bus.subscribe(
        EventType.COMPONENT_MOUNT.value,
        lambda event: recorded.append(f"sub:{event.type.value}"),
    )
    global_bus.connect_subsystem_bus("ui", subsystem_bus)

    global_bus.publish(Event(type=EventType.COMPONENT_MOUNT))
    assert recorded == ["global:component_mount", "sub:component_mount"]
