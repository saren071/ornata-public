"""GPU memory residency management and eviction tracking."""

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING

from ornata.api.exports.definitions import MemoryBlock, ResidencyState
from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.gpu.misc import GPUBackend

logger = get_logger(__name__)


class Residency:
    """Manages GPU memory residency and eviction policies."""

    def __init__(self, backend: GPUBackend | None = None, max_memory_mb: int = 1024) -> None:
        """Initialize the residency manager.

        Args:
            backend: GPU backend for residency operations.
            max_memory_mb: Maximum GPU memory to manage in MB.
        """
        self.backend = backend
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self._lock = threading.RLock()

        # Memory tracking
        self._memory_blocks: dict[str, MemoryBlock] = {}
        self._total_resident_bytes = 0

        # Eviction policies
        self._eviction_threshold = 0.9  # Evict when 90% full
        self._min_resident_threshold = 0.7  # Keep at least 70% resident

        # Statistics
        self._stats = {
            "evictions": 0,
            "restorations": 0,
            "memory_pressure_events": 0,
            "peak_memory_usage": 0
        }

    def register_memory_block(self, block_id: str, size: int, usage: str, priority: int = 0) -> None:
        """Register a memory block for residency management.

        Args:
            block_id: Unique identifier for the memory block.
            size: Size of the memory block in bytes.
            usage: Usage pattern ('static', 'dynamic', etc.).
            priority: Eviction priority (higher = less likely to evict).
        """
        with self._lock:
            if block_id in self._memory_blocks:
                from ornata.api.exports.definitions import GPUMemoryError
                raise GPUMemoryError(f"Memory block {block_id} already registered")

            block = MemoryBlock(
                id=block_id,
                size=size,
                usage=usage,
                alignment=16,
                priority=priority,
                last_accessed=time.time()
            )

            self._memory_blocks[block_id] = block
            self._total_resident_bytes += size
            self._update_peak_memory()

            logger.debug(f"Registered memory block {block_id} ({size} bytes, {usage})")

    def unregister_memory_block(self, block_id: str) -> None:
        """Unregister a memory block from residency management.

        Args:
            block_id: Identifier of the memory block to unregister.
        """
        with self._lock:
            if block_id not in self._memory_blocks:
                return

            block = self._memory_blocks[block_id]
            if block.state == ResidencyState.RESIDENT:
                self._total_resident_bytes -= block.size

            del self._memory_blocks[block_id]
            logger.debug(f"Unregistered memory block {block_id}")

    def mark_accessed(self, block_id: str) -> None:
        """Mark a memory block as recently accessed.

        Args:
            block_id: Identifier of the accessed memory block.
        """
        with self._lock:
            if block_id not in self._memory_blocks:
                return

            block = self._memory_blocks[block_id]
            block.last_accessed = time.time()
            block.access_count += 1

    def check_memory_pressure(self) -> bool:
        """Check if memory pressure requires eviction.

        Returns:
            True if eviction is needed, False otherwise.
        """
        with self._lock:
            usage_ratio = self._total_resident_bytes / self.max_memory_bytes
            return usage_ratio >= self._eviction_threshold

    def evict_memory(self, target_bytes: int | None = None) -> int:
        """Evict memory blocks to free up space.

        Args:
            target_bytes: Target bytes to free, or None for default policy.

        Returns:
            Number of bytes freed through eviction.
        """
        with self._lock:
            if target_bytes is None:
                # Default: evict to bring usage below minimum threshold
                current_usage = self._total_resident_bytes / self.max_memory_bytes
                if current_usage <= self._min_resident_threshold:
                    return 0

                target_usage = (self._min_resident_threshold + (self._eviction_threshold - self._min_resident_threshold) * 0.5)
                target_bytes = int(self._total_resident_bytes - (target_usage * self.max_memory_bytes))

            # Find blocks to evict using LRU with priority weighting
            evictable_blocks = [
                block for block in self._memory_blocks.values()
                if block.state == ResidencyState.RESIDENT
            ]

            # Sort by eviction priority (lower score = more likely to evict)
            evictable_blocks.sort(key=self._calculate_eviction_score)

            freed_bytes = 0
            for block in evictable_blocks:
                if freed_bytes >= target_bytes:
                    break

                if self._evict_block(block):
                    freed_bytes += block.size
                    self._stats["evictions"] += 1

            if freed_bytes > 0:
                self._stats["memory_pressure_events"] += 1
                logger.debug(f"Evicted {freed_bytes} bytes of memory")

            return freed_bytes

    def restore_memory(self, block_id: str) -> bool:
        """Restore an evicted memory block to resident state.

        Args:
            block_id: Identifier of the block to restore.

        Returns:
            True if restoration succeeded, False otherwise.
        """
        with self._lock:
            if block_id not in self._memory_blocks:
                return False

            block = self._memory_blocks[block_id]
            if block.state != ResidencyState.EVICTED:
                return True  # Already resident

            # Check if we need to evict other blocks first
            if self._total_resident_bytes + block.size > self.max_memory_bytes:
                needed_bytes = block.size - (self.max_memory_bytes - self._total_resident_bytes)
                freed_bytes = self.evict_memory(needed_bytes)
                if freed_bytes < needed_bytes:
                    return False  # Couldn't free enough memory

            # Restore the block
            if self._restore_block(block):
                block.state = ResidencyState.RESIDENT
                self._total_resident_bytes += block.size
                self._stats["restorations"] += 1
                self._update_peak_memory()
                logger.debug(f"Restored memory block {block_id}")
                return True

            return False

    def get_memory_stats(self) -> dict[str, int | float]:
        """Get current memory residency statistics.

        Returns:
            Dictionary with memory statistics.
        """
        with self._lock:
            total_blocks = len(self._memory_blocks)
            resident_blocks = sum(1 for b in self._memory_blocks.values() if b.state == ResidencyState.RESIDENT)
            evicted_blocks = sum(1 for b in self._memory_blocks.values() if b.state == ResidencyState.EVICTED)

            return {
                "total_blocks": total_blocks,
                "resident_blocks": resident_blocks,
                "evicted_blocks": evicted_blocks,
                "total_memory_bytes": self._total_resident_bytes,
                "max_memory_bytes": self.max_memory_bytes,
                "memory_usage_percent": (self._total_resident_bytes / self.max_memory_bytes) * 100,
                "peak_memory_usage": self._stats["peak_memory_usage"],
                "evictions": self._stats["evictions"],
                "restorations": self._stats["restorations"],
                "memory_pressure_events": self._stats["memory_pressure_events"]
            }

    def cleanup(self) -> None:
        """Clean up residency management state."""
        with self._lock:
            self._memory_blocks.clear()
            self._total_resident_bytes = 0
            logger.debug("Memory residency manager cleaned up")

    def _calculate_eviction_score(self, block: MemoryBlock) -> float:
        """Calculate eviction score for a memory block.

        Args:
            block: Memory block to score.

        Returns:
            Eviction score (lower = more likely to evict).
        """
        # Base score from recency (newer = higher score)
        time_factor = time.time() - block.last_accessed

        # Priority factor (higher priority = higher score)
        priority_factor = block.priority * 1000

        # Access frequency factor
        access_factor = block.access_count * 100

        # Size factor (larger blocks slightly more likely to evict)
        size_factor = block.size / (1024 * 1024)  # MB factor

        return time_factor - priority_factor - access_factor + size_factor

    def _evict_block(self, block: MemoryBlock) -> bool:
        """Evict a memory block to non-resident storage.

        Args:
            block: Block to evict.

        Returns:
            True if eviction succeeded.
        """
        try:
            if self.backend is not None and hasattr(self.backend, "evict_memory_block"):
                self.backend.evict_memory_block(block.id)
            block.state = ResidencyState.EVICTED
            self._total_resident_bytes -= block.size
            return True
        except Exception as e:
            logger.warning(f"Failed to evict block {block.id}: {e}")
            return False

    def _restore_block(self, block: MemoryBlock) -> bool:
        """Restore a memory block to resident state.

        Args:
            block: Block to restore.

        Returns:
            True if restoration succeeded.
        """
        try:
            if self.backend is not None and hasattr(self.backend, "restore_memory_block"):
                self.backend.restore_memory_block(block.id)
            return True
        except Exception as e:
            logger.warning(f"Failed to restore block {block.id}: {e}")
            return False

    def _update_peak_memory(self) -> None:
        """Update peak memory usage statistic."""
        if self._total_resident_bytes > self._stats["peak_memory_usage"]:
            self._stats["peak_memory_usage"] = self._total_resident_bytes