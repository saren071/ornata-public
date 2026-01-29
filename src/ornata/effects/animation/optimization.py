"""Animation optimization utilities."""

import threading
from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.effects.animation.keyframes import Animation

logger = get_logger(__name__)


class AnimationOptimizer:
    """Optimizes animation performance and memory usage."""

    def __init__(self) -> None:
        """Initialize the optimizer."""
        self._cache: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()

    def optimize_animation(self, animation: Animation) -> Animation:
        """Optimize an animation for better performance.

        Args:
            animation: The animation to optimize.

        Returns:
            Optimized animation.
        """
        with self._lock:
            # Check cache first
            cache_key = self._get_cache_key(animation)
            if cache_key in self._cache:
                cached = self._cache[cache_key]
                logger.log(5, f"Using cached optimized animation for {animation.component.component_name}")  # TRACE
                return cached["optimized"]

            # Perform optimizations
            optimized = self._perform_optimizations(animation)

            # Cache the result
            self._cache[cache_key] = {"optimized": optimized, "timestamp": self._get_timestamp()}

            # Clean old cache entries
            self._cleanup_cache()

            logger.log(5, f"Optimized animation for {animation.component.component_name}")  # TRACE
            return optimized

    def _perform_optimizations(self, animation: Animation) -> Animation:
        """Perform optimization operations on an animation.

        Args:
            animation: The animation to optimize.

        Returns:
            Optimized animation.
        """
        # For now, return the animation as-is
        # In a full implementation, this would:
        # - Reduce keyframes for simple animations
        # - Optimize easing functions
        # - Pre-calculate transform matrices
        # - Compress animation data
        return animation

    def _get_cache_key(self, animation: Animation) -> str:
        """Generate a cache key for an animation.

        Args:
            animation: The animation to generate a key for.

        Returns:
            Cache key string.
        """
        # Simple cache key based on component and animation properties
        return f"{animation.component.component_name}:{animation.duration}:{len(animation.keyframes)}"

    def _get_timestamp(self) -> float:
        """Get current timestamp for cache management.

        Returns:
            Current timestamp.
        """
        import time

        return time.time()

    def _cleanup_cache(self) -> None:
        """Clean up old cache entries."""
        current_time = self._get_timestamp()
        max_age = 300.0  # 5 minutes

        to_remove: list[str] = []
        for key, data in self._cache.items():
            if current_time - data["timestamp"] > max_age:
                to_remove.append(key)

        for key in to_remove:
            del self._cache[key]

        if to_remove:
            logger.log(5, f"Cleaned up {len(to_remove)} old animation cache entries")  # TRACE

    def get_cache_stats(self) -> dict[str, int]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics.
        """
        with self._lock:
            return {"entries": len(self._cache), "total_size": sum(len(str(data)) for data in self._cache.values())}


class AnimationBatcher:
    """Batches multiple animations for efficient processing."""

    def __init__(self) -> None:
        """Initialize the batcher."""
        self._batches: dict[str, list[Animation]] = {}
        self._lock = threading.RLock()

    def add_to_batch(self, batch_id: str, animation: Animation) -> None:
        """Add an animation to a batch.

        Args:
            batch_id: The batch identifier.
            animation: The animation to add.
        """
        with self._lock:
            if batch_id not in self._batches:
                self._batches[batch_id] = []
            self._batches[batch_id].append(animation)
            logger.log(5, f"Added animation to batch {batch_id}")  # TRACE

    def process_batch(self, batch_id: str, delta_time: float) -> None:
        """Process all animations in a batch.

        Args:
            batch_id: The batch identifier.
            delta_time: Time elapsed since last update.
        """
        with self._lock:
            if batch_id not in self._batches:
                return

            batch: list[Animation] = self._batches[batch_id]
            completed: list[Animation] = []

            for animation in batch:
                animation.update(delta_time)
                if animation.is_complete():
                    completed.append(animation)

            # Remove completed animations
            for animation in completed:
                batch.remove(animation)

            # Remove empty batches
            if not batch:
                del self._batches[batch_id]

            logger.log(5, f"Processed batch {batch_id}: {len(completed)} completed")  # TRACE

    def clear_batch(self, batch_id: str) -> None:
        """Clear all animations from a batch.

        Args:
            batch_id: The batch identifier.
        """
        with self._lock:
            count = len(self._batches.get(batch_id, []))
            self._batches.pop(batch_id, None)
            logger.log(5, f"Cleared batch {batch_id} with {count} animations")  # TRACE
