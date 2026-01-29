"""Keyframe definitions for animations."""

import threading
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ornata.api.exports.definitions import AnimationDirection, AnimationState, Transform
from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable

    from ornata.api.exports.definitions import Component, Keyframe

logger = get_logger(__name__)


@dataclass(slots=True)
class Animation:
    """Animation definition and state."""

    component: Component
    keyframes: list[Keyframe]
    duration: float
    easing: Callable[[float], float] | None = None
    loop: bool = False
    direction: AnimationDirection = AnimationDirection.NORMAL

    _start_time: float = field(default=0.0, init=False)
    _current_time: float = field(default=0.0, init=False)
    _is_playing: bool = field(default=False, init=False)
    _is_paused: bool = field(default=False, init=False)
    _lock: threading.RLock = field(default_factory=threading.RLock, init=False)

    def __post_init__(self) -> None:
        """Initialize animation."""
        if not self.keyframes:
            raise ValueError("Animation must have at least one keyframe")

        if self.easing is None:
            from ornata.effects.animation.easing import linear_easing

            self.easing = linear_easing

        # Sort keyframes by offset
        self.keyframes.sort(key=lambda k: k.offset)

    def start(self) -> None:
        """Start the animation."""
        with self._lock:
            self._start_time = time.perf_counter()
            self._current_time = 0.0
            self._is_playing = True
            self._is_paused = False
            logger.debug(f"Started animation for component {self.component.component_name}")

    def stop(self) -> None:
        """Stop the animation."""
        with self._lock:
            self._is_playing = False
            self._is_paused = False
            logger.debug(f"Stopped animation for component {self.component.component_name}")

    def pause(self) -> None:
        """Pause the animation."""
        with self._lock:
            self._is_paused = True
            logger.debug(f"Paused animation for component {self.component.component_name}")

    def resume(self) -> None:
        """Resume the animation."""
        with self._lock:
            self._is_paused = False
            logger.debug(f"Resumed animation for component {self.component.component_name}")

    def update(self, delta_time: float) -> None:
        """Update animation state.

        Args:
            delta_time: Time elapsed since last update.
        """
        with self._lock:
            if not self._is_playing or self._is_paused:
                return

            self._current_time += delta_time

            # Handle looping
            if self._current_time >= self.duration:
                if self.loop:
                    self._current_time = self._current_time % self.duration
                else:
                    self._current_time = self.duration
                    self._is_playing = False

    def get_current_state(self) -> AnimationState:
        """Get current animation state.

        Returns:
            Current animation state.
        """
        with self._lock:
            if not self._is_playing:
                progress = 1.0 if self._current_time >= self.duration else 0.0
            else:
                progress = min(self._current_time / self.duration, 1.0)

            if self.easing is None:
                eased_progress = progress
            else:
                eased_progress = self.easing(progress)
            transforms = self._calculate_transforms(eased_progress)

            return AnimationState(progress=eased_progress, transforms=transforms)

    def is_complete(self) -> bool:
        """Check if animation is complete.

        Returns:
            True if animation is complete.
        """
        with self._lock:
            return not self.loop and self._current_time >= self.duration

    def _calculate_transforms(self, progress: float) -> list[Transform]:
        """Calculate transforms for current progress.

        Args:
            progress: Animation progress (0.0 to 1.0).

        Returns:
            List of transforms.
        """
        transforms: list[Transform] = []

        for i in range(len(self.keyframes) - 1):
            start_keyframe = self.keyframes[i]
            end_keyframe = self.keyframes[i + 1]

            if start_keyframe.offset <= progress <= end_keyframe.offset:
                # Interpolate between keyframes
                keyframe_progress = (progress - start_keyframe.offset) / (end_keyframe.offset - start_keyframe.offset)
                transform = self._interpolate_keyframes(start_keyframe, end_keyframe, keyframe_progress)
                transforms.append(transform)
                break

        return transforms

    def _interpolate_keyframes(self, start: Keyframe, end: Keyframe, progress: float) -> Transform:
        """Interpolate between two keyframes.

        Args:
            start: Start keyframe.
            end: End keyframe.
            progress: Interpolation progress (0.0 to 1.0).

        Returns:
            Interpolated transform.
        """
        transform = Transform()

        # Interpolate numeric properties
        for prop in ["translate_x", "translate_y", "scale_x", "scale_y", "rotate", "opacity"]:
            if prop in start.properties and prop in end.properties:
                start_val = float(start.properties[prop])
                end_val = float(end.properties[prop])
                setattr(transform, prop, start_val + (end_val - start_val) * progress)

        return transform
