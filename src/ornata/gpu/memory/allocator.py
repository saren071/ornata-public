"""GPU memory allocator with buffer pools and leak detection."""

from __future__ import annotations

import threading
import weakref
from typing import TYPE_CHECKING, Any

from ornata.api.exports.definitions import BufferStats, MemoryBlock
from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.gpu.misc import GPUBackend

logger = get_logger(__name__)


class Allocator:
    """REQUIRED: GPU memory allocator with pooling."""
    
    def __init__(self, backend: GPUBackend | None = None, max_pool_size: int = 1000) -> None:
        """Initialize the memory allocator.

        Args:
            backend: GPU backend for buffer creation.
            max_pool_size: Maximum number of buffers to keep in pools.
        """
        self.backend = backend
        self.max_pool_size = max_pool_size
        self._lock = threading.RLock()

        # Memory block tracking for low-level allocations
        self._memory_blocks: dict[int, MemoryBlock] = {}
        self._next_address = 0x1000  # Start addresses at 0x1000

        # Buffer pools by type and usage pattern
        self._vertex_pools: dict[str, list[Any]] = {}
        self._index_pools: dict[str, list[Any]] = {}
        self._uniform_pools: dict[str, list[Any]] = {}

        # Statistics tracking - separate buffer stats from memory stats
        self._buffer_stats = {
            "vertex": BufferStats(),
            "index": BufferStats(),
            "uniform": BufferStats()
        }
        self._memory_stats = {
            "memory_allocated": 0,
            "memory_freed": 0,
            "defragmentation_ops": 0
        }

        # Leak detection
        self._active_buffers: set[Any] = set()
        self._buffer_refs: list[weakref.ref[Any]] = []

        # Cleanup callback for leak detection
        def cleanup_callback(ref: weakref.ref[Any]) -> None:
            obj = ref()
            if obj is not None:
                self._active_buffers.discard(obj)

        self._cleanup_callback = cleanup_callback

    def allocate(self, size: int, alignment: int = 16, usage: str = "general") -> MemoryBlock:
        """REQUIRED: Allocate a memory block.

        Args:
            size: Size of the block in bytes.
            alignment: Memory alignment in bytes.
            usage: Usage pattern ('general', 'vertex', 'index', 'uniform').

        Returns:
            MemoryBlock: Allocated memory block.

        Raises:
            GPUMemoryError: If allocation fails.
        """
        with self._lock:
            # Calculate aligned address
            aligned_address = (self._next_address + alignment - 1) & ~(alignment - 1)
            
            block_id = f"block_{aligned_address:08x}"
            block = MemoryBlock(
                id=block_id,
                size=size,
                usage=usage,
                alignment=alignment,
                address=aligned_address,
                allocated=True
            )
            
            # Track the block
            self._memory_blocks[aligned_address] = block
            self._next_address = aligned_address + size
            
            # Update statistics
            self._memory_stats["memory_allocated"] += size
            
            logger.debug(f"Allocated {size} bytes at address 0x{aligned_address:08x} (alignment: {alignment})")
            
            return block

    def deallocate(self, block: MemoryBlock) -> None:
        """REQUIRED: Deallocate a memory block.

        Args:
            block: Memory block to deallocate.

        Raises:
            GPUMemoryError: If block is not found or already freed.
        """
        with self._lock:
            if block.address not in self._memory_blocks:
                from ornata.api.exports.definitions import GPUMemoryError
                raise GPUMemoryError(f"Memory block at address 0x{block.address:08x} not found")
            
            if not block.allocated:
                from ornata.api.exports.definitions import GPUMemoryError
                raise GPUMemoryError(f"Memory block at address 0x{block.address:08x} is already freed")
            
            # Mark as freed
            block.allocated = False
            
            # Update statistics
            self._memory_stats["memory_freed"] += block.size
            
            logger.debug(f"Deallocated {block.size} bytes from address 0x{block.address:08x}")

    def defragment(self) -> list[MemoryBlock]:
        """REQUIRED: Defragment memory and return moved blocks.

        Returns:
            list[MemoryBlock]: List of blocks that were moved during defragmentation.
        """
        with self._lock:
            moved_blocks: list[MemoryBlock] = []
            
            # Simple defragmentation: compact allocated blocks
            allocated_blocks = [block for block in self._memory_blocks.values() if block.allocated and block.address is not None]
            allocated_blocks.sort(key=lambda b: b.address if b.address is not None else 0)

            current_address = 0x1000
            for block in allocated_blocks:
                block_address = block.address
                if block_address is None:
                    continue

                if block_address != current_address:
                    # Move block to new location
                    old_address = block_address
                    _old_size = block.size

                    # Update block address
                    block.address = current_address
                    moved_blocks.append(block)

                    # Remove old entry and add new one
                    del self._memory_blocks[old_address]
                    self._memory_blocks[current_address] = block

                    logger.debug(
                        f"Defragmentation: moved block {block.id} from 0x{old_address:08x} to 0x{current_address:08x}"
                    )
                
                current_address += block.size
            
            # Update next address
            self._next_address = current_address
            
            # Update statistics
            self._memory_stats["defragmentation_ops"] += 1
            
            logger.info(f"Defragmentation completed: moved {len(moved_blocks)} blocks")
            
            return moved_blocks

    def get_stats(self) -> dict[str, int | float]:
        """REQUIRED: Get allocator statistics.

        Returns:
            dict[str, int | float]: Detailed allocation statistics.
        """
        with self._lock:
            allocated_blocks = [b for b in self._memory_blocks.values() if b.allocated]
            total_allocated = sum(block.size for block in allocated_blocks)
            total_blocks = len(self._memory_blocks)
            
            return {
                "total_blocks": total_blocks,
                "allocated_blocks": len(allocated_blocks),
                "freed_blocks": total_blocks - len(allocated_blocks),
                "total_memory_allocated": self._memory_stats["memory_allocated"],
                "total_memory_freed": self._memory_stats["memory_freed"],
                "current_memory_usage": total_allocated,
                "memory_efficiency": (total_allocated / max(self._memory_stats["memory_allocated"], 1)) * 100,
                "vertex_created": self._buffer_stats["vertex"].created,
                "vertex_reused": self._buffer_stats["vertex"].reused,
                "vertex_active": self._buffer_stats["vertex"].active,
                "index_created": self._buffer_stats["index"].created,
                "index_reused": self._buffer_stats["index"].reused,
                "index_active": self._buffer_stats["index"].active,
                "uniform_created": self._buffer_stats["uniform"].created,
                "uniform_reused": self._buffer_stats["uniform"].reused,
                "uniform_active": self._buffer_stats["uniform"].active,
                "defragmentation_ops": self._memory_stats["defragmentation_ops"]
            }

    def allocate_vertex_buffer(self, data: list[float], usage: str = "dynamic") -> Any:
        """Allocate a vertex buffer from pool or create new one.

        Args:
            data: Vertex data to store.
            usage: Buffer usage pattern.

        Returns:
            GPU vertex buffer object.

        Raises:
            GPUMemoryError: If buffer allocation fails.
        """
        with self._lock:
            # Try to reuse from pool
            pool = self._vertex_pools.setdefault(usage, [])
            if pool:
                buffer = pool.pop()
                self._buffer_stats["vertex"].reused += 1
                # Update buffer data
                self._update_buffer_data(buffer, data)
            else:
                # Create new buffer
                buffer = self._create_vertex_buffer(data, usage)
                self._buffer_stats["vertex"].created += 1

            # Track for leak detection
            self._active_buffers.add(buffer)
            self._buffer_refs.append(weakref.ref(buffer, self._cleanup_callback))
            self._buffer_stats["vertex"].active += 1

            return buffer

    def allocate_index_buffer(self, data: list[int], usage: str = "dynamic") -> Any:
        """Allocate an index buffer from pool or create new one.

        Args:
            data: Index data to store.
            usage: Buffer usage pattern.

        Returns:
            GPU index buffer object.

        Raises:
            GPUMemoryError: If buffer allocation fails.
        """
        with self._lock:
            # Try to reuse from pool
            pool = self._index_pools.setdefault(usage, [])
            if pool:
                buffer = pool.pop()
                self._buffer_stats["index"].reused += 1
                # Update buffer data
                self._update_buffer_data(buffer, data)
            else:
                # Create new buffer
                buffer = self._create_index_buffer(data, usage)
                self._buffer_stats["index"].created += 1

            # Track for leak detection
            self._active_buffers.add(buffer)
            self._buffer_refs.append(weakref.ref(buffer, self._cleanup_callback))
            self._buffer_stats["index"].active += 1

            return buffer

    def allocate_uniform_buffer(self, data: list[float], usage: str = "dynamic") -> Any:
        """Allocate a uniform buffer from pool or create new one.

        Args:
            data: Uniform data to store.
            usage: Buffer usage pattern.

        Returns:
            GPU uniform buffer object.

        Raises:
            GPUMemoryError: If buffer allocation fails.
        """
        with self._lock:
            # Try to reuse from pool
            pool = self._uniform_pools.setdefault(usage, [])
            if pool:
                buffer = pool.pop()
                self._buffer_stats["uniform"].reused += 1
                # Update buffer data
                self._update_buffer_data(buffer, data)
            else:
                # Create new buffer
                buffer = self._create_uniform_buffer(data, usage)
                self._buffer_stats["uniform"].created += 1

            # Track for leak detection
            self._active_buffers.add(buffer)
            self._buffer_refs.append(weakref.ref(buffer, self._cleanup_callback))
            self._buffer_stats["uniform"].active += 1

            return buffer

    def release_buffer(self, buffer: Any, buffer_type: str, usage: str = "dynamic") -> None:
        """Release a buffer back to the pool for reuse.

        Args:
            buffer: Buffer to release.
            buffer_type: Type of buffer ('vertex', 'index', 'uniform').
            usage: Buffer usage pattern.
        """
        with self._lock:
            if buffer in self._active_buffers:
                self._active_buffers.discard(buffer)
                self._buffer_stats[buffer_type].active -= 1

                # Return to pool if not full
                pool = self._get_pool(buffer_type, usage)
                if len(pool) < self.max_pool_size:
                    pool.append(buffer)
                else:
                    # Pool full, destroy buffer
                    self._destroy_buffer(buffer)

    def check_for_leaks(self) -> dict[str, int]:
        """Perform leak detection and return report.

        Returns:
            Dictionary with leak analysis results.
        """
        with self._lock:
            # Clean up dead references
            self._buffer_refs = [ref for ref in self._buffer_refs if ref() is not None]

            # Count active references
            active_refs = len([ref for ref in self._buffer_refs if ref() is not None])

            # Calculate leaks
            total_active = len(self._active_buffers)
            leaks = total_active - active_refs

            # Update stats
            for stats in self._buffer_stats.values():
                stats.leaked = leaks

            if leaks > 0:
                logger.warning(f"Memory leak detected: {leaks} buffers not properly released")

            return {
                "active_buffers": total_active,
                "tracked_references": active_refs,
                "leaks_detected": leaks,
                "vertex_pool_size": len(self._vertex_pools.get("dynamic", [])),
                "index_pool_size": len(self._index_pools.get("dynamic", [])),
                "uniform_pool_size": len(self._uniform_pools.get("dynamic", []))
            }

    def cleanup(self) -> None:
        """Clean up all pooled buffers and reset allocator state."""
        with self._lock:
            # Clear all pools
            self._vertex_pools.clear()
            self._index_pools.clear()
            self._uniform_pools.clear()

            # Clear tracking
            self._active_buffers.clear()
            self._buffer_refs.clear()

            # Clear memory blocks
            self._memory_blocks.clear()
            self._next_address = 0x1000

            # Reset stats
            for stats in self._buffer_stats.values():
                stats.created = 0
                stats.reused = 0
                stats.active = 0
                stats.leaked = 0
            for key in self._memory_stats:
                self._memory_stats[key] = 0

            logger.debug("Memory allocator cleaned up")

    def _create_vertex_buffer(self, data: list[float], usage: str) -> Any:
        """Create a new vertex buffer.

        Args:
            data: Vertex data.
            usage: Buffer usage.

        Returns:
            GPU vertex buffer.

        Raises:
            GPUMemoryError: If creation fails.
        """
        try:
            from ornata.gpu.fallback.sw_buffers import SwVertexBuffer
            return SwVertexBuffer(data, usage)
        except Exception as e:
            from ornata.api.exports.definitions import GPUMemoryError
            raise GPUMemoryError(f"Failed to create vertex buffer: {e}") from e

    def _create_index_buffer(self, data: list[int], usage: str) -> Any:
        """Create a new index buffer.

        Args:
            data: Index data.
            usage: Buffer usage.

        Returns:
            GPU index buffer.

        Raises:
            GPUMemoryError: If creation fails.
        """
        try:
            from ornata.gpu.fallback.sw_buffers import SwIndexBuffer
            return SwIndexBuffer(data, usage)
        except Exception as e:
            from ornata.api.exports.definitions import GPUMemoryError
            raise GPUMemoryError(f"Failed to create index buffer: {e}") from e

    def _create_uniform_buffer(self, data: list[float], usage: str) -> Any:
        """Create a new uniform buffer.

        Args:
            data: Uniform data.
            usage: Buffer usage.

        Returns:
            GPU uniform buffer.

        Raises:
            GPUMemoryError: If creation fails.
        """
        try:
            return list(data)
        except Exception as e:
            from ornata.api.exports.definitions import GPUMemoryError
            raise GPUMemoryError(f"Failed to create uniform buffer: {e}") from e

    def _update_buffer_data(self, buffer: Any, data: list[float] | list[int]) -> None:
        """Update buffer data.

        Args:
            buffer: Buffer to update.
            data: New data.
        """
        try:
            update_method = buffer.update_data
        except AttributeError:
            update_method = None

        if callable(update_method):
            update_method(data)
        elif isinstance(buffer, list):
            buffer[:] = data
        else:
            logger.debug("No update_data method available for buffer %s", buffer)

    def _destroy_buffer(self, buffer: Any) -> None:
        """Destroy a buffer.

        Args:
            buffer: Buffer to destroy.
        """
        try:
            cleanup_method = buffer.cleanup
        except AttributeError:
            cleanup_method = None

        if callable(cleanup_method):
            cleanup_method()

    def _get_pool(self, buffer_type: str, usage: str) -> list[Any]:
        """Get the appropriate buffer pool.

        Args:
            buffer_type: Type of buffer.
            usage: Usage pattern.

        Returns:
            Buffer pool list.
        """
        if buffer_type == "vertex":
            return self._vertex_pools.setdefault(usage, [])
        elif buffer_type == "index":
            return self._index_pools.setdefault(usage, [])
        elif buffer_type == "uniform":
            return self._uniform_pools.setdefault(usage, [])
        else:
            raise ValueError(f"Unknown buffer type: {buffer_type}")