"""Diffing engine for efficient VDOM tree comparison and patch generation."""

from __future__ import annotations

import logging
from threading import RLock
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ornata.api.exports.definitions import Patch, VDOMNode, VDOMTree

logger = logging.getLogger(__name__)


class DiffingEngine:
    """Engine for efficient VDOM tree diffing and patch generation."""

    def __init__(self) -> None:
        """Initialize the diffing engine."""
        from ornata.vdom.diffing.algorithms import IncrementalDiff, KeyedDiff, SimpleDiff
        from ornata.vdom.diffing.cache import DiffCache
        from ornata.vdom.diffing.optimization import PatchOptimizer
        self._algorithms = {"simple": SimpleDiff(), "keyed": KeyedDiff(), "incremental": IncrementalDiff()}
        self._cache = DiffCache()
        self._optimizer = PatchOptimizer()
        self._lock = RLock()

    def diff_trees(self, old_tree: VDOMTree, new_tree: VDOMTree) -> list[Patch]:
        """Diff two VDOM trees and return patches."""
        with self._lock:
            try:
                logger.debug(f"Starting diff operation for trees of size {self._tree_size(old_tree)} -> {self._tree_size(new_tree)}")

                # Fast-path: identical root nodes
                if old_tree.root is new_tree.root:
                    logger.debug("Identical root nodes, returning empty patches")
                    return []

                # Check cache first with improved key
                cache_key = self._make_cache_key(old_tree, new_tree)
                if cache_key in self._cache:
                    logger.debug("Using cached diff result")
                    return self._cache[cache_key]

                # Select appropriate algorithm
                algorithm = self._select_algorithm(old_tree, new_tree)
                logger.log(5, f"Selected algorithm: {algorithm.__class__.__name__}")

                # Perform diffing
                patches = algorithm.diff(old_tree, new_tree)

                # Optimize patches
                patches = self._optimizer.optimize(patches)
                logger.log(5, f"Generated {len(patches)} optimized patches")

                # Cache result only if not too large
                if len(patches) < 1000:  # Avoid caching very large patch sets
                    self._cache[cache_key] = patches

                logger.debug("Diff operation completed successfully")
                return patches

            except Exception as e:
                logger.error(f"Diff operation failed: {e}")
                from ornata.api.exports.definitions import DiffingError
                raise DiffingError(f"Tree diffing failed: {e}") from e

    def _select_algorithm(self, old_tree: VDOMTree, new_tree: VDOMTree):
        """Select appropriate diffing algorithm based on tree characteristics."""
        old_size = self._tree_size(old_tree)
        new_size = self._tree_size(new_tree)

        # Use incremental diff for large trees
        if old_size > 1000 or new_size > 1000:
            return self._algorithms["incremental"]

        # Use keyed diff if trees have keys
        if self._has_keys(old_tree) and self._has_keys(new_tree):
            return self._algorithms["keyed"]

        # Default to simple diff
        return self._algorithms["simple"]

    def _tree_size(self, tree: VDOMTree) -> int:
        """Calculate the size of a VDOM tree."""

        cached_size = getattr(tree, "node_count", None)
        if isinstance(cached_size, int) and cached_size >= 0:
            return cached_size

        def count_nodes(node: VDOMNode | None) -> int:
            if node is None:
                return 0
            return 1 + sum(count_nodes(child) for child in node.children)

        return count_nodes(tree.root)

    def _has_keys(self, tree: VDOMTree) -> bool:
        """Check if tree has keyed components."""

        def check_keys(node: VDOMNode | None) -> bool:
            if node is None:
                return False
            if node.key:
                return True
            return any(check_keys(child) for child in node.children)

        return check_keys(tree.root)

    def _make_cache_key(self, old_tree: VDOMTree, new_tree: VDOMTree) -> str:
        """Create cache key for diff operation."""
        old_root = old_tree.root
        new_root = new_tree.root
        old_hash = getattr(old_root, "subtree_hash", None) if old_root is not None else None
        new_hash = getattr(new_root, "subtree_hash", None) if new_root is not None else None
        if old_hash is not None and new_hash is not None:
            return f"{old_hash}:{new_hash}:{len(old_tree.key_map)}:{len(new_tree.key_map)}"

        old_text = self._hash_tree(old_root) if old_root else "none"
        new_text = self._hash_tree(new_root) if new_root else "none"
        return f"{old_text}:{new_text}"

    def _hash_tree(self, node: VDOMNode | None) -> str:
        """Create a content-based hash for a tree node."""
        if node is None:
            return "none"
        
        # Hash based on component name, key, props, and children
        node_hash = hash((node.component_name, node.key))
        
        # Include properties in hash
        if node.props:
            normalized_props = tuple(
                (key, self._normalize_hashable(value))
                for key, value in sorted(node.props.items())
            )
            node_hash ^= hash(normalized_props)
        
        # Include children in hash
        children_hashes = tuple(self._hash_tree(child) for child in node.children)
        if children_hashes:
            node_hash ^= hash(children_hashes)

        return f"{node_hash & 0xFFFFFFFF:08x}"  # 32-bit hex string

    def _normalize_hashable(self, value: Any) -> Any:
        """Convert objects to hash-friendly representations."""
        if isinstance(value, (str, int, float, bool, type(None))):
            return value
        if isinstance(value, dict):
            preliminary: list[tuple[str, Any]] = [
                (str(key), val)
                for key, val in value.items()
            ]
            sorted_items = sorted(preliminary, key=lambda item: item[0])
            return tuple(
                (key, self._normalize_hashable(val))
                for key, val in sorted_items
            )
        if isinstance(value, (list, tuple)):
            return tuple(self._normalize_hashable(item) for item in value)
        if isinstance(value, (set, frozenset)):
            return tuple(sorted(self._normalize_hashable(item) for item in value))
        return repr(value)
