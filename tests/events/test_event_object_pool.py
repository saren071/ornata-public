"""Event object pool and pooled context tests."""

from __future__ import annotations

from ornata.definitions.dataclasses.events import Event
from ornata.events.core.object_pool import (
    EventObjectPool,
    PooledEvent,
    get_event_object_pool,
    pooled_event,
)


def test_event_object_pool_reuses_and_resets_events() -> None:
    """Events released back into the pool should be reset before reuse."""

    pool = EventObjectPool()
    event = pool.acquire_event("custom")
    event.data = {"value": 10}
    pool.release_event(event, "custom")

    reused = pool.acquire_event("custom")
    assert reused is event
    assert reused.data is None
    pool.release_event(reused, "custom")


def test_event_object_pool_component_helpers() -> None:
    """Component event pools should hand out reusable instances."""

    pool = EventObjectPool()
    component_event = pool.acquire_component_event()
    component_event.name = "button"
    pool.release_component_event(component_event)

    reused = pool.acquire_component_event()
    assert reused.name == ""
    pool.release_component_event(reused)


def test_pooled_event_context_manager_returns_event() -> None:
    """Global pooled_event helper should provide reset events on each entry."""

    global_pool = get_event_object_pool()
    tracked_ids: list[int] = []

    for _ in range(2):
        with pooled_event("ctx") as event:
            assert isinstance(event, Event)
            tracked_ids.append(id(event))
            event.data = "payload"
    assert len(tracked_ids) == 2

    with PooledEvent("ctx") as pooled:
        assert pooled.data is None
        global_pool.release_event(pooled, "ctx")
