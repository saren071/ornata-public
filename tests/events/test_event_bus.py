"""Event bus system coverage tests."""

from __future__ import annotations

from collections import deque

from ornata.definitions.dataclasses.events import BatchedEvent, Event
from ornata.definitions.enums import EventType
from ornata.events.core.bus import (
    EventBus,
    GlobalEventBus,
    LockFreeEventQueue,
    SubsystemEventBus,
)


def test_event_bus_publish_and_unsubscribe() -> None:
    """EventBus should route events via snapshot cache and honor unsubscribe."""

    bus = EventBus()
    received: list[str] = []

    unsubscribe = bus.subscribe(EventType.TICK.value, lambda event: received.append(event.type.value))
    bus.publish(Event(type=EventType.TICK))
    assert received == [EventType.TICK.value]

    unsubscribe()
    bus.publish(Event(type=EventType.TICK))
    assert received == [EventType.TICK.value]


def test_event_bus_coalescing_and_async_queue() -> None:
    """Coalescing and async queue processing should deliver events in order."""

    bus = EventBus()
    batched_counts: list[int] = []
    async_received: deque[str] = deque()

    def _capture_batched(event: Event) -> None:
        assert isinstance(event.data, BatchedEvent)
        batched_counts.append(event.data.count)

    bus.subscribe(EventType.BATCHED_EVENT.value, _capture_batched)
    bus.subscribe(EventType.LAYOUT_INVALIDATED.value, lambda event: async_received.append(event.type.value))

    bus.set_coalescing_enabled(True)
    event = Event(type=EventType.LAYOUT_INVALIDATED)
    bus._publish_with_coalescing(event)
    bus._publish_with_coalescing(event)
    bus._flush_coalesced_events()
    assert batched_counts == [1]

    bus.publish_async(event)
    bus.process_queued_events(EventType.LAYOUT_INVALIDATED.value)
    assert list(async_received) == [EventType.LAYOUT_INVALIDATED.value]

    queue = LockFreeEventQueue()
    queued_event = Event(type=EventType.TICK)
    assert queue.put(queued_event) is True
    assert queue.size() == 1
    assert queue.get_batch(1) == [queued_event]
    assert queue.size() == 0


def test_global_event_bus_bridging_and_batch_processing() -> None:
    """Global bus should forward events to subscribers and subsystem buses."""

    global_bus = GlobalEventBus()
    subsystem_bus = SubsystemEventBus("ui")
    received_order: list[str] = []

    global_bus.subscribe(EventType.TICK.value, lambda event: received_order.append("global"))
    subsystem_bus.subscribe(EventType.TICK.value, lambda event: received_order.append("subsystem"))
    global_bus.connect_subsystem_bus("ui", subsystem_bus)

    global_bus.publish(Event(type=EventType.TICK))
    assert received_order == ["global", "subsystem"]

    subsystem_event = Event(type=EventType.TICK)
    subsystem_bus.publish(subsystem_event)
    global_bus.process_batch_queue()
    assert received_order[-2:] == ["global", "subsystem"]


def test_subsystem_bus_avoids_forwarding_global_events() -> None:
    """SubsystemEventBus should not re-forward events sourced from the global bus."""

    subsystem_bus = SubsystemEventBus("telemetry")
    forwarded: list[Event] = []

    class _Bridge(GlobalEventBus):
        def receive_subsystem_event(self, source_bus: EventBus, event: Event) -> None:  # type: ignore[override]
            forwarded.append(event)

    bridge = _Bridge()
    subsystem_bus.set_global_bridge(bridge)

    regular_event = Event(type=EventType.TICK)
    subsystem_bus.publish(regular_event)
    bridge.process_batch_queue()
    assert forwarded

    forwarded.clear()
    global_event = Event(type=EventType.TICK)
    global_event.source = "__global__"
    subsystem_bus.publish(global_event)
    assert forwarded == []
