"""Advanced diffing algorithms for efficient VDOM tree comparison."""

from __future__ import annotations

import logging
from threading import RLock
from typing import TYPE_CHECKING, Any

try:
    import importlib
    vdom_diff_ext = importlib.import_module("ornata.api.exports.optimization.vdom_diff")
except Exception:
    vdom_diff_ext = None
from ornata.api.exports.definitions import DiffingError
from ornata.vdom.diffing.reconciler import TreeReconciler

if TYPE_CHECKING:
    from ornata.api.exports.definitions import Patch, VDOMNode, VDOMTree

logger = logging.getLogger(__name__)


def _collect_dirty_state(*trees: VDOMTree) -> tuple[set[str], set[str]] | None:
    dirty: set[str] = set()
    structural: set[str] = set()
    for tree in trees:
        consume = tree.consume_dirty_state
        if callable(consume):
            state = consume()
            if state:
                nodes, structural_nodes = state
                dirty.update(nodes)
                structural.update(structural_nodes)
    if not dirty and not structural:
        return None
    return dirty, structural


class IncrementalDiff:
    """Incremental diffing algorithm optimized for large trees."""

    def __init__(self) -> None:
        """Initialize incremental diff algorithm."""
        self._cache = {}
        self._lock = RLock()
        self._cython_available = vdom_diff_ext is not None

    def diff(self, old_tree: VDOMTree, new_tree: VDOMTree) -> list[Patch]:
        """Perform incremental diff between trees."""
        with self._lock:
            try:
                logger.debug(f"Starting incremental diff: {self._tree_size(old_tree)} -> {self._tree_size(new_tree)} nodes")

                if old_tree.root is new_tree.root:
                    logger.debug("Identical trees, returning empty patches")
                    return []

                old_hashes = self._compute_tree_hashes(old_tree)
                new_hashes = self._compute_tree_hashes(new_tree)
                changed_keys = self._find_changed_keys(old_hashes, new_hashes)
                from ornata.api.exports.definitions import Patch
                patches: list[Patch] = []
                for key in changed_keys:
                    old_subtree = self._get_subtree(old_tree, key)
                    new_subtree = self._get_subtree(new_tree, key)
                    if old_subtree is None and new_subtree is not None:
                        patches.append(Patch.add_node(new_subtree))
                    elif old_subtree is not None and new_subtree is None:
                        patches.append(Patch.remove_node(key))
                    elif old_subtree is not None and new_subtree is not None:
                        subtree_patches = self._diff_subtrees(old_subtree, new_subtree)
                        patches.extend(subtree_patches)
                logger.debug(f"Generated {len(patches)} incremental patches")
                return patches
            except Exception as e:
                logger.error(f"Incremental diff failed: {e}")
                raise DiffingError(f"Incremental diffing failed: {e}") from e

    def _compute_tree_hashes(self, tree: VDOMTree) -> dict[str, int]:
        """Compute content hashes for tree nodes."""
        if tree.root is None:
            return {}

        if getattr(tree.root, "_subtree_hash", None):
            return self._collect_cached_hashes(tree.root)

        if self._cython_available:
            if vdom_diff_ext is None:
                return {}
            return vdom_diff_ext.compute_tree_hashes(tree.root)

        hashes: dict[str, int] = {}

        def hash_node(node: VDOMNode) -> int:
            if node.key is None:
                return 0
            node_hash = hash(node.component_name)
            if node.props:
                for prop_key, value in sorted(node.props.items()):
                    node_hash ^= hash((prop_key, self._normalize_hashable(value)))
            for child in getattr(node, "children", []) or []:
                node_hash ^= hash_node(child)
            hashes[node.key] = node_hash
            return node_hash

        hash_node(tree.root)
        return hashes

    def _collect_cached_hashes(self, node: VDOMNode) -> dict[str, int]:
        hashes: dict[str, int] = {}
        stack: list[VDOMNode] = [node]
        while stack:
            current = stack.pop()
            if current.key is not None:
                hashes[current.key] = getattr(current, "_subtree_hash", 0)
            stack.extend(current.children)
        return hashes

    def _find_changed_keys(self, old_hashes: dict[str, int], new_hashes: dict[str, int]) -> list[str]:
        """Find keys that have changed between hash sets."""
        all_keys = set(old_hashes) | set(new_hashes)
        changed: list[str] = []
        for key in all_keys:
            old_hash = old_hashes.get(key)
            new_hash = new_hashes.get(key)
            if old_hash != new_hash:
                changed.append(key)
        return changed

    def _get_subtree(self, tree: VDOMTree, key: str) -> VDOMNode | None:
        """Get subtree referenced by ``key``."""
        return tree.key_map.get(key)

    def _normalize_hashable(self, value: Any) -> Any:
        """Convert nested structures into hash-friendly primitives."""
        if isinstance(value, (str, int, float, bool, type(None))):
            return value
        if isinstance(value, dict):
            return tuple[
                tuple[str, Any]
            ](
                (key, self._normalize_hashable(val))
                for key, val in sorted(value.items())
            )
        if isinstance(value, (list, tuple)):
            return tuple(self._normalize_hashable(item) for item in value)
        if isinstance(value, (set, frozenset)):
            return tuple(sorted(self._normalize_hashable(item) for item in value))
        return repr(value)

    def _diff_subtrees(self, old_node: VDOMNode, new_node: VDOMNode) -> list[Patch]:
        """Diff two subtrees using key-aware operations."""
        from ornata.api.exports.definitions import Patch
        patches: list[Patch] = []
        if old_node.key is None or new_node.key is None:
            return patches

        if old_node.component_name != new_node.component_name:
            patches.append(Patch.remove_node(old_node.key))
            patches.append(Patch.add_node(new_node))
            return patches

        old_props = old_node.props or {}
        new_props = new_node.props or {}
        if old_props != new_props:
            patches.append(Patch.update_props(old_node.key, new_props))

        old_children = getattr(old_node, "children", []) or []
        new_children = getattr(new_node, "children", []) or []
        child_patches = self._diff_children(old_children, new_children)
        patches.extend(child_patches)
        return patches

    def _diff_children(self, old_children: list[VDOMNode], new_children: list[VDOMNode]) -> list[Patch]:
        """Diff child lists using key-based algorithm."""
        from ornata.api.exports.definitions import Patch
        patches: list[Patch] = []
        old_keyed: dict[str, tuple[int, VDOMNode]] = {}
        old_unkeyed: list[tuple[int, VDOMNode]] = []
        new_keyed: dict[str, tuple[int, VDOMNode]] = {}
        new_unkeyed: list[tuple[int, VDOMNode]] = []

        for i, child in enumerate(old_children):
            if hasattr(child, 'key') and child.key is not None:
                old_keyed[child.key] = (i, child)
            else:
                old_unkeyed.append((i, child))

        for i, child in enumerate(new_children):
            if hasattr(child, 'key') and child.key is not None:
                new_keyed[child.key] = (i, child)
            else:
                new_unkeyed.append((i, child))
        handled_keys: set[str] = set()
        for key, (new_index, new_child) in new_keyed.items():
            if key in old_keyed:
                old_index, old_child = old_keyed[key]
                handled_keys.add(key)

                if old_index != new_index:
                    patches.append(Patch.move_node(key, new_index))
                child_patches = self._diff_subtrees(old_child, new_child)
                patches.extend(child_patches)
            else:
                patches.append(Patch.add_node(new_child))
        for key in set(old_keyed.keys()) - handled_keys:
            patches.append(Patch.remove_node(key))
        max_len = max(len(old_unkeyed), len(new_unkeyed))
        for i in range(max_len):
            old_child = old_unkeyed[i][1] if i < len(old_unkeyed) else None
            new_child = new_unkeyed[i][1] if i < len(new_unkeyed) else None

            if old_child is None and new_child is not None:
                patches.append(Patch.add_node(new_child))
            elif old_child is not None and new_child is None:
                if old_child.key is not None:
                    patches.append(Patch.remove_node(old_child.key))
            elif old_child is not None and new_child is not None:
                child_patches = self._diff_subtrees(old_child, new_child)
                patches.extend(child_patches)

        return patches

    def _convert_cython_patch(self, cython_patch: dict[str, Any]) -> Patch:
        """Convert Cython patch format to Patch object."""
        from ornata.api.exports.definitions import Patch
        patch_type = cython_patch.get("type")
        if patch_type == "add":
            return Patch.add_node(cython_patch["node"])
        elif patch_type == "remove":
            return Patch.remove_node(cython_patch["key"])
        elif patch_type == "update":
            return Patch.replace_root(cython_patch["new_node"])
        else:
            raise ValueError(f"Unknown patch type: {patch_type}")

    def _tree_size(self, tree: VDOMTree) -> int:
        """Calculate tree size."""
        cached_size = getattr(tree, "node_count", None)
        if isinstance(cached_size, int) and cached_size >= 0:
            return cached_size

        def count_nodes(node: VDOMNode | None) -> int:
            if node is None:
                return 0
            count = 1
            if hasattr(node, 'children') and node.children:
                for child in node.children:
                    count += count_nodes(child)
            return count

        return count_nodes(tree.root)


class KeyedDiff:
    """Key-based diffing algorithm optimized for lists with stable keys."""

    def __init__(self) -> None:
        """Initialize keyed diff algorithm."""
        self._lock = RLock()
        self._reconciler = TreeReconciler()

    def diff(self, old_tree: VDOMTree, new_tree: VDOMTree) -> list[Patch]:
        """Perform key-based diff between trees."""
        with self._lock:
            try:
                logger.debug("Starting keyed diff (delegated to TreeReconciler)")
                if old_tree.root is None or new_tree.root is None:
                    return []
                dirty_state = _collect_dirty_state(old_tree, new_tree)
                return self._reconciler.reconcile(old_tree.root, new_tree.root, dirty_state)
            except Exception as exc:
                logger.error(f"Keyed diff failed: {exc}")
                raise DiffingError(f"Keyed diffing failed: {exc}") from exc


class SimpleDiff:
    """Simple recursive diffing algorithm for basic use cases."""

    def __init__(self) -> None:
        """Initialize simple diff algorithm."""
        self._lock = RLock()
        self._reconciler = TreeReconciler()

    def diff(self, old_tree: VDOMTree, new_tree: VDOMTree) -> list[Patch]:
        """Perform simple recursive diff."""
        with self._lock:
            try:
                logger.debug("Starting simple diff (delegated to TreeReconciler)")
                if old_tree.root is None or new_tree.root is None:
                    return []
                dirty_state = _collect_dirty_state(old_tree, new_tree)
                return self._reconciler.reconcile(old_tree.root, new_tree.root, dirty_state)
            except Exception as exc:
                logger.error(f"Simple diff failed: {exc}")
                raise DiffingError(f"Simple diffing failed: {exc}") from exc
