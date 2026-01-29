"""Animation timeline management."""

import threading
import time
from typing import TYPE_CHECKING

from ornata.api.exports.definitions import ScheduledCallback
from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable

    from ornata.effects.animation.keyframes import Animation

logger = get_logger(__name__)


class Timeline:
    """Animation timeline for coordinating multiple animations."""

    def __init__(self) -> None:
        """Initialize the timeline."""
        self._animations: list[Animation] = []
        self._lock = threading.RLock()

    def add_animation(self, animation: Animation) -> None:
        """Add an animation to the timeline.

        Args:
            animation: The animation to add.
        """
        with self._lock:
            self._animations.append(animation)
            logger.debug(f"Added animation to timeline for component {animation.component.component_name}")

    def remove_animation(self, animation: Animation) -> None:
        """Remove an animation from the timeline.

        Args:
            animation: The animation to remove.
        """
        with self._lock:
            try:
                self._animations.remove(animation)
                logger.debug(f"Removed animation from timeline for component {animation.component.component_name}")
            except ValueError:
                logger.warning(f"Animation not found in timeline for component {animation.component.component_name}")

    def update(self, delta_time: float) -> None:
        """Update all animations in the timeline.

        Args:
            delta_time: Time elapsed since last update.
        """
        with self._lock:
            completed: list[Animation] = []
            for animation in self._animations[:]:  # Copy to avoid modification during iteration
                animation.update(delta_time)
                if animation.is_complete():
                    completed.append(animation)

            # Remove completed animations
            for animation in completed:
                self._animations.remove(animation)
                logger.debug(f"Completed animation in timeline for component {animation.component.component_name}")

    def get_animations(self) -> list[Animation]:
        """Get all animations in the timeline.

        Returns:
            List of animations.
        """
        with self._lock:
            return self._animations.copy()

    def clear(self) -> None:
        """Clear all animations from the timeline."""
        with self._lock:
            count = len(self._animations)
            self._animations.clear()
            logger.debug(f"Cleared {count} animations from timeline")

    def is_empty(self) -> bool:
        """Check if the timeline is empty.

        Returns:
            True if no animations are in the timeline.
        """
        with self._lock:
            return len(self._animations) == 0


class AnimationScheduler:
    """Scheduler for managing animation timing and callbacks."""

    def __init__(self) -> None:
        """Initialize the scheduler."""
        self._scheduled_callbacks: dict[str, ScheduledCallback] = {}
        self._lock = threading.RLock()
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the scheduler thread."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return

            self._running = True
            self._thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self._thread.start()
            logger.debug("Animation scheduler started")

    def stop(self) -> None:
        """Stop the scheduler thread."""
        with self._lock:
            self._running = False
            if self._thread is not None:
                self._thread.join(timeout=1.0)
                self._thread = None
            logger.debug("Animation scheduler stopped")

    def schedule_callback(
        self,
        callback_id: str,
        callback: Callable[[], None],
        delay: float,
        repeating: bool = False,
        interval: float | None = None
    ) -> None:
        """Schedule a callback to be executed after a delay.

        Args:
            callback_id: Unique identifier for the callback.
            callback: The callback function to execute.
            delay: Delay in seconds before first execution.
            repeating: Whether the callback should repeat.
            interval: Interval between repetitions (if repeating).
        """
        with self._lock:
            scheduled_time = time.perf_counter() + delay
            scheduled_callback = ScheduledCallback(
                callback_id=callback_id,
                callback=callback,
                scheduled_time=scheduled_time,
                repeating=repeating,
                interval=interval or delay,
                next_execution=scheduled_time
            )

            self._scheduled_callbacks[callback_id] = scheduled_callback
            logger.log(5, f"Scheduled callback {callback_id} for {delay}s from now")  # TRACE

    def cancel_callback(self, callback_id: str) -> None:
        """Cancel a scheduled callback.

        Args:
            callback_id: The callback ID to cancel.
        """
        with self._lock:
            if callback_id in self._scheduled_callbacks:
                del self._scheduled_callbacks[callback_id]
                logger.log(5, f"Cancelled callback {callback_id}")  # TRACE

    def get_scheduled_callbacks(self) -> list[str]:
        """Get IDs of all scheduled callbacks.

        Returns:
            List of callback IDs.
        """
        with self._lock:
            return list(self._scheduled_callbacks.keys())

    def _run_scheduler(self) -> None:
        """Run the scheduler loop."""

        while self._running:
            try:
                current_time = time.perf_counter()
                to_execute: list[ScheduledCallback] = []

                with self._lock:
                    # Find callbacks that are ready to execute
                    for callback in self._scheduled_callbacks.values():
                        if current_time >= callback.next_execution:
                            to_execute.append(callback)

                    # Update next execution times for repeating callbacks
                    for callback in to_execute:
                        if callback.repeating:
                            callback.next_execution = current_time + callback.interval
                        else:
                            # Remove non-repeating callbacks
                            del self._scheduled_callbacks[callback.callback_id]

                # Execute callbacks outside the lock
                for callback in to_execute:
                    try:
                        callback.callback()
                        logger.log(5, f"Executed callback {callback.callback_id}")  # TRACE
                    except Exception as e:
                        logger.error(f"Animation callback {callback.callback_id} failed: {e}")

                # Sleep to avoid busy waiting
                time.sleep(0.016)  # ~60 FPS

            except Exception as e:
                logger.error(f"Animation scheduler error: {e}")
                time.sleep(0.1)  # Back off on errors
