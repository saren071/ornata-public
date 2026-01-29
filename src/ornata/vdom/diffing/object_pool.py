"""Object pooling system for efficient patch reuse and memory management."""

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING, TypeVar

from ornata.api.exports.definitions import PatchPoolConfig, PatchPoolStats
from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import TracebackType
    from weakref import ReferenceType

    from ornata.api.exports.definitions import Patch


logger = get_logger(__name__)

T = TypeVar("T")


class PatchPool[T]:
    """Generic object pool for efficient patch reuse."""

    def __init__(
        self,
        factory: Callable[[], T],
        config: PatchPoolConfig | None = None,
        reset_func: Callable[[T], None] | None = None,
    ):
        from ornata.api.exports.definitions import PatchPoolConfig, PatchPoolStats
        self.factory = factory
        self.config = config or PatchPoolConfig()
        self.reset_func = reset_func or (lambda obj: None)

        # Pool storage
        self._pool: list[T] = []
        self._weak_refs: set[ReferenceType[T]] = set()

        # Statistics
        self.stats = PatchPoolStats()

        # Cleanup tracking
        self._last_cleanup = 0.0
        self._lock = threading.RLock()

    def acquire(self) -> T:
        """Get a patch from the pool, creating a new one if necessary."""
        with self._lock:
            # Try to get from pool first
            obj = self._get_from_pool()

            if obj is not None:
                self.stats.reused += 1
                self.reset_func(obj)
                return obj

            # Create new object
            obj = self.factory()
            self.stats.created += 1

            # Update hit rate
            total_requests = self.stats.created + self.stats.reused
            if total_requests > 0:
                self.stats.hit_rate = self.stats.reused / total_requests

            return obj

    def release(self, obj: T) -> None:
        """Return a patch to the pool for reuse."""
        if self._should_pool_object(obj):
            with self._lock:
                self._add_to_pool(obj)
                self.stats.returned += 1
        else:
            with self._lock:
                self.stats.evicted += 1

    def clear(self) -> None:
        """Clear all patches from the pool."""
        with self._lock:
            self._pool.clear()
            self._weak_refs.clear()
            self.stats.pool_size = 0

    def cleanup(self) -> None:
        """Clean up expired patches and update statistics."""
        current_time = time.time()

        with self._lock:
            # Clean up weak references (disabled for Patch objects)
            if self.config.enable_weak_refs:
                dead_refs = [ref for ref in self._weak_refs if ref() is None]
                self._weak_refs.difference_update(dead_refs)
                self.stats.garbage_collected += len(dead_refs)

            # Periodic cleanup of pool
            if current_time - self._last_cleanup > self.config.cleanup_interval:
                # Remove excess objects
                while len(self._pool) > self.config.max_pool_size:
                    self._pool.pop(0)
                    self.stats.evicted += 1

                self._last_cleanup = current_time

            self.stats.pool_size = len(self._pool)

    def get_stats(self) -> PatchPoolStats:
        """Get pool statistics."""
        with self._lock:
            return self.stats

    def _get_from_pool(self) -> T | None:
        """Get a patch from the pool."""
        if self._pool:
            return self._pool.pop(0)
        return None

    def _add_to_pool(self, obj: T) -> None:
        """Add a patch to the pool."""
        if len(self._pool) < self.config.max_pool_size:
            self._pool.append(obj)

            if self.config.enable_weak_refs:
                # Add weak reference for tracking
                self._weak_refs.add(__import__('weakref').ref(obj))

    def _should_pool_object(self, obj: T) -> bool:
        """Determine if a patch should be pooled."""
        # Basic checks - can be extended for specific patch types
        return True


class PatchObjectPool:
    """Specialized pool for Patch objects with type-based sub-pools."""

    def __init__(self, config: PatchPoolConfig | None = None):
        self.config = config or PatchPoolConfig()
        self._pools: dict[str, PatchPool[Patch]] = {}
        self._stats = PatchPoolStats()
        self._lock = threading.RLock()

    def acquire_patch(self, patch_type: str = "generic") -> Patch:
        """Get a Patch from the pool."""
        pool = self._get_pool(patch_type, self._create_patch)
        patch = pool.acquire()
        self._update_global_stats()
        return patch

    def release_patch(self, patch: Patch, patch_type: str = "generic") -> None:
        """Return a Patch to the pool."""
        pool = self._get_pool(patch_type, self._create_patch)
        pool.release(patch)
        self._update_global_stats()

    def cleanup(self) -> None:
        """Clean up all pools."""
        with self._lock:
            for pool in self._pools.values():
                pool.cleanup()
            self._update_global_stats()

    def get_stats(self, patch_type: str | None = None) -> PatchPoolStats:
        """Get statistics for a specific patch type or global stats."""
        from ornata.api.exports.definitions import PatchPoolStats
        with self._lock:
            if patch_type:
                pool = self._pools.get(patch_type)
                return pool.get_stats() if pool else PatchPoolStats()
            return self._stats

    def _get_pool(self, patch_type: str, factory: Callable[[], Patch]) -> PatchPool[Patch]:
        """Get or create a pool for the given patch type."""
        with self._lock:
            if patch_type not in self._pools:
                self._pools[patch_type] = PatchPool(factory, self.config, self._reset_patch)
            return self._pools[patch_type]

    def _create_patch(self) -> Patch:
        """Factory function for creating Patch objects."""
        from ornata.api.exports.definitions import Patch, PatchType

        return Patch(patch_type=PatchType.ADD_NODE)  # Default type, will be overridden

    def _reset_patch(self, patch: Patch) -> None:
        """Reset a patch for reuse."""
        # Reset common fields
        patch.key = None
        patch.data = None

    def _update_global_stats(self) -> None:
        """Update global statistics across all pools."""
        with self._lock:
            total_created = 0
            total_reused = 0
            total_returned = 0
            total_evicted = 0
            total_gc = 0
            total_pool_size = 0

            for pool in self._pools.values():
                stats = pool.get_stats()
                total_created += stats.created
                total_reused += stats.reused
                total_returned += stats.returned
                total_evicted += stats.evicted
                total_gc += stats.garbage_collected
                total_pool_size += stats.pool_size

            self._stats.created = total_created
            self._stats.reused = total_reused
            self._stats.returned = total_returned
            self._stats.evicted = total_evicted
            self._stats.garbage_collected = total_gc
            self._stats.pool_size = total_pool_size

            total_requests = total_created + total_reused
            self._stats.hit_rate = total_reused / total_requests if total_requests > 0 else 0.0


# Global patch object pool instance
_patch_object_pool = PatchObjectPool()


def get_patch_object_pool() -> PatchObjectPool:
    """Get the global patch object pool instance."""
    return _patch_object_pool


class PooledPatch:
    """Context manager for pooled Patch usage."""

    def __init__(self, patch_type: str = "generic"):
        self.patch_type = patch_type
        self.patch: Patch | None = None

    def __enter__(self) -> Patch:
        self.patch = get_patch_object_pool().acquire_patch(self.patch_type)
        return self.patch

    def __exit__(self, exc_type: type | None, exc_val: Exception | None, exc_tb: TracebackType | None) -> None:
        if self.patch is not None:
            get_patch_object_pool().release_patch(self.patch, self.patch_type)


def pooled_patch(patch_type: str = "generic"):
    """Context manager for getting a pooled Patch."""
    return PooledPatch(patch_type)