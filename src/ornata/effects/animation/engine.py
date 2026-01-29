"""Animation engine for managing component animations."""

import threading
import time
from typing import TYPE_CHECKING

from ornata.api.exports.utils import get_logger
from ornata.effects.animation.timeline import Timeline

if TYPE_CHECKING:
    from ornata.effects.animation.keyframes import Animation

logger = get_logger(__name__)


class AnimationEngine:
    """Engine for managing component animations."""

    def __init__(self) -> None:
        """Initialize the animation engine."""
        self._active_animations: dict[str, Animation] = {}
        self._timelines: dict[str, Timeline] = {}
        self._lock = threading.RLock()

    def start_animation(self, animation: Animation) -> str:
        """Start an animation.

        Args:
            animation: The animation to start.

        Returns:
            The animation ID.
        """
        with self._lock:
            animation_id = self._generate_id()
            self._active_animations[animation_id] = animation
            animation.start()
            logger.debug(f"Started animation {animation_id}")
            return animation_id

    def stop_animation(self, animation_id: str) -> None:
        """Stop an animation.

        Args:
            animation_id: The animation ID to stop.
        """
        with self._lock:
            if animation_id in self._active_animations:
                animation = self._active_animations[animation_id]
                animation.stop()
                del self._active_animations[animation_id]
                logger.debug(f"Stopped animation {animation_id}")

    def pause_animation(self, animation_id: str) -> None:
        """Pause an animation.

        Args:
            animation_id: The animation ID to pause.
        """
        with self._lock:
            if animation_id in self._active_animations:
                self._active_animations[animation_id].pause()
                logger.debug(f"Paused animation {animation_id}")

    def resume_animation(self, animation_id: str) -> None:
        """Resume an animation.

        Args:
            animation_id: The animation ID to resume.
        """
        with self._lock:
            if animation_id in self._active_animations:
                self._active_animations[animation_id].resume()
                logger.debug(f"Resumed animation {animation_id}")

    def get_active_animations(self) -> list[Animation]:
        """Get all active animations.

        Returns:
            List of active animations.
        """
        with self._lock:
            return list(self._active_animations.values())

    def update_animations(self, delta_time: float) -> None:
        """Update all active animations.

        Args:
            delta_time: Time elapsed since last update.
        """
        with self._lock:
            completed: list[str] = []
            for animation_id, animation in self._active_animations.items():
                animation.update(delta_time)
                if animation.is_complete():
                    completed.append(animation_id)

            # Remove completed animations
            for animation_id in completed:
                del self._active_animations[animation_id]
                logger.debug(f"Completed animation {animation_id}")

    def create_timeline(self, timeline_id: str) -> Timeline:
        """Create a new animation timeline.

        Args:
            timeline_id: Unique identifier for the timeline.

        Returns:
            The created timeline.
        """
        from ornata.effects.animation.timeline import Timeline

        with self._lock:
            if timeline_id in self._timelines:
                raise ValueError(f"Timeline with ID '{timeline_id}' already exists")

            timeline = Timeline()
            self._timelines[timeline_id] = timeline
            logger.debug(f"Created timeline {timeline_id}")
            return timeline

    def get_timeline(self, timeline_id: str) -> Timeline | None:
        """Get a timeline by ID.

        Args:
            timeline_id: The timeline ID to retrieve.

        Returns:
            The timeline if found, None otherwise.
        """
        with self._lock:
            return self._timelines.get(timeline_id)

    def remove_timeline(self, timeline_id: str) -> None:
        """Remove a timeline.

        Args:
            timeline_id: The timeline ID to remove.
        """
        with self._lock:
            if timeline_id in self._timelines:
                del self._timelines[timeline_id]
                logger.debug(f"Removed timeline {timeline_id}")

    def _generate_id(self) -> str:
        """Generate a unique animation ID.

        Returns:
            Unique animation ID.
        """
        return f"anim_{int(time.time() * 1000000)}"
