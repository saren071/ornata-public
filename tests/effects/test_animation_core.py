"""Animation subsystem coverage tests."""

from __future__ import annotations

from collections import deque

import pytest

from ornata.api.exports.definitions import Keyframe
from ornata.api.exports.effects import (
    AnimationBatcher,
    AnimationCoordinator,
    AnimationEngine,
    AnimationEvent,
    AnimationEventDispatcher,
    AnimationEventType,
    AnimationOptimizer,
    AnimationScheduler,
)
from ornata.effects.animation.keyframes import Animation
from ornata.definitions.dataclasses.components import Component

import ornata.effects.animation.keyframes as keyframes_module
import ornata.effects.animation.timeline as animation_timeline_module


def _make_component(name: str = "Demo") -> Component:
    return Component(component_name=name)


def _make_animation(component_name: str = "Anim", duration: float = 1.0) -> Animation:
    component = _make_component(component_name)
    keyframes = [
        Keyframe(offset=0.0, properties={"translate_x": 0.0}),
        Keyframe(offset=1.0, properties={"translate_x": 10.0}),
    ]
    return Animation(component, keyframes, duration)


def test_animation_updates_progress_and_transforms(monkeypatch: pytest.MonkeyPatch) -> None:
    """Animation should honor start/update/complete lifecycle semantics."""

    animation = _make_animation()

    clock = deque([0.0, 0.5, 1.5])

    def fake_perf_counter() -> float:
        value = clock[0]
        if len(clock) > 1:
            clock.popleft()
        return value

    monkeypatch.setattr(keyframes_module.time, "perf_counter", fake_perf_counter)

    animation.start()
    animation.update(0.5)
    state = animation.get_current_state()
    assert state.progress == pytest.approx(0.5)
    assert state.transforms and state.transforms[0].translate_x == pytest.approx(5.0)

    animation.pause()
    animation.resume()
    animation.update(0.6)
    assert animation.is_complete() is True


def test_animation_engine_manages_lifecycle(monkeypatch: pytest.MonkeyPatch) -> None:
    """AnimationEngine should start, update, and dispose animations and timelines."""

    # Ensure timeline creation uses predictable object by patching underlying module import.
    class StubTimeline:
        def __init__(self) -> None:
            self.animations: list[str] = []

    monkeypatch.setattr("ornata.effects.animation.engine.Timeline", StubTimeline)

    engine = AnimationEngine()
    animation = _make_animation("Engine")

    animation_id = engine.start_animation(animation)
    assert engine.get_active_animations()

    engine.pause_animation(animation_id)
    engine.resume_animation(animation_id)
    engine.update_animations(1.0)
    assert engine.get_active_animations() == []

    engine.stop_animation(animation_id)  # Should be a no-op for absent animations

    timeline = engine.create_timeline("main")
    assert engine.get_timeline("main") is timeline
    with pytest.raises(ValueError):
        engine.create_timeline("main")

    engine.remove_timeline("main")
    assert engine.get_timeline("main") is None


def test_animation_coordinator_sequences() -> None:
    """AnimationCoordinator should advance sequences and drop completed animations."""

    animations = [_make_animation("first", duration=0.5), _make_animation("second", duration=0.5)]
    coordinator = AnimationCoordinator()

    coordinator.create_sequence("seq", animations)
    coordinator.start_sequence("seq")

    coordinator.update_sequences(0.5)
    assert animations[0].get_current_state().progress == pytest.approx(1.0)

    coordinator.update_sequences(0.6)
    assert coordinator.get_active_sequences() == []


def test_animation_event_dispatcher_routes_events() -> None:
    """AnimationEventDispatcher should add/remove/dispatch listeners."""

    dispatcher = AnimationEventDispatcher()
    seen: list[str] = []

    def listener(event: AnimationEvent) -> None:
        seen.append(event.event_type.value)

    dispatcher.add_listener(AnimationEventType.ANIMATION_START, listener)
    dispatcher.dispatch_event(
        AnimationEvent(
            event_type=AnimationEventType.ANIMATION_START,
            animation_id="anim",
            progress=0.0,
        )
    )
    assert seen == [AnimationEventType.ANIMATION_START.value]

    dispatcher.remove_listener(AnimationEventType.ANIMATION_START, listener)
    dispatcher.clear_listeners(AnimationEventType.ANIMATION_START)
    dispatcher.clear_listeners()


def test_animation_scheduler_executes_callbacks(monkeypatch: pytest.MonkeyPatch) -> None:
    """AnimationScheduler should run due callbacks and support cancellation."""

    scheduler = AnimationScheduler()
    executed: list[str] = []

    class FakeClock:
        def __init__(self) -> None:
            self.value = 0.0

        def perf_counter(self) -> float:
            self.value += 0.05
            return self.value

        @staticmethod
        def sleep(_dt: float) -> None:
            return None

    fake_time = FakeClock()

    monkeypatch.setattr(animation_timeline_module, "time", fake_time)

    def callback() -> None:
        executed.append("cb")
        scheduler._running = False

    scheduler.schedule_callback("cb", callback, delay=0.0)
    scheduler._running = True
    scheduler._run_scheduler()

    assert executed == ["cb"]
    assert scheduler.get_scheduled_callbacks() == []

    scheduler.schedule_callback("late", callback, delay=1.0)
    scheduler.cancel_callback("late")
    assert scheduler.get_scheduled_callbacks() == []


def test_animation_optimizer_and_batcher(monkeypatch: pytest.MonkeyPatch) -> None:
    """Animation optimizer and batcher should reuse cache entries and retire completed animations."""

    optimizer = AnimationOptimizer()
    animation = _make_animation("Optimized")

    optimized_first = optimizer.optimize_animation(animation)
    optimized_second = optimizer.optimize_animation(animation)
    assert optimized_first is optimized_second is animation

    optimizer._cache["stale"] = {"optimized": animation, "timestamp": 0.0}
    optimizer._cleanup_cache()
    assert "stale" not in optimizer._cache
    stats = optimizer.get_cache_stats()
    assert "entries" in stats

    batcher = AnimationBatcher()
    batcher.add_to_batch("batch", animation)
    batcher.process_batch("batch", delta_time=2.0)
    batcher.clear_batch("batch")
