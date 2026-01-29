"""Memory management for VDOM operations."""

from __future__ import annotations

import gc
import threading
from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.definitions import VDOMTree

logger = get_logger(__name__)


class MemoryManager:
    """Manages memory for VDOM operations."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._large_operations_threshold = 1000

    def optimize_for_large_tree(self, tree: VDOMTree) -> None:
        """Optimize memory usage for large VDOM trees."""
        with self._lock:
            node_count = self._count_nodes(tree)
            if node_count > self._large_operations_threshold:
                logger.debug(f"Optimizing memory for large VDOM tree ({node_count} nodes)")
                collected = gc.collect()
                
                # Clear internal caches if they exist
                from ornata.vdom.diffing.cache import DiffCache
                cache = DiffCache()
                cache.clear()
                
                # Run additional garbage collection for generations
                for generation in range(3):
                    collected += gc.collect(generation)
                
                logger.debug(f"Memory optimization completed: {collected} objects collected")

    def cleanup_after_operation(self, tree: VDOMTree) -> None:
        """Clean up memory after VDOM operations."""
        with self._lock:
            from ornata.vdom.core.refs import ComponentRefs
            refs = ComponentRefs()
            cleaned = refs.cleanup_dead_refs()
            if cleaned > 0:
                logger.debug(f"Cleaned up {cleaned} dead component references")
            node_count = self._count_nodes(tree)
            if node_count > self._large_operations_threshold:
                collected = gc.collect()
                logger.debug(f"Post-operation garbage collection collected {collected} objects")

    def monitor_memory_usage(self, tree: VDOMTree) -> dict[str, int]:
        """Monitor memory usage statistics."""
        with self._lock:
            node_count = self._count_nodes(tree)
            gc_stats = gc.get_stats()
            stats = {
                "node_count": node_count,
                "gc_collections": sum(gen["collections"] for gen in gc_stats),
                "gc_objects": sum(gen["collected"] for gen in gc_stats),
            }
            logger.debug(f"Memory stats: {stats}")
            return stats

    def _count_nodes(self, tree: VDOMTree) -> int:
        """Count total nodes in VDOM tree."""
        def count_recursive(node: Any) -> int:
            if not hasattr(node, "children"):
                return 1
            count = 1
            if getattr(node, "children", None):
                for child in node.children:
                    count += count_recursive(child)
            return count
        if tree.root is None:
            return 0
        return count_recursive(tree.root)
