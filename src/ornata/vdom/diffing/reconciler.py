"""VDOM tree reconciliation logic."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger

try:
    import importlib
    vdom_diff_ext = importlib.import_module("ornata.api.exports.optimization.vdom_diff")
except Exception:
    vdom_diff_ext = None

if TYPE_CHECKING:
    from ornata.api.exports.definitions import Patch, VDOMNode

logger = get_logger(__name__)


class TreeReconciler:
    """Reconciles VDOM trees to find differences."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._cython_diff_props = getattr(vdom_diff_ext, "diff_props", None) if vdom_diff_ext else None
        self._cython_keyed_plan = getattr(vdom_diff_ext, "reconcile_children_keyed", None) if vdom_diff_ext else None
        self._cython_keyed_fast = getattr(vdom_diff_ext, "reconcile_children_keyed_fast", None) if vdom_diff_ext else None
        self._cython_children_keyed = getattr(vdom_diff_ext, "children_all_keyed", None) if vdom_diff_ext else None
        self._cython_nodes_differ = getattr(vdom_diff_ext, "nodes_differ", None) if vdom_diff_ext else None
        self._active_dirty_keys: set[str] | None = None
        self._active_structural_keys: set[str] | None = None

    def reconcile(
        self,
        old_tree: VDOMNode,
        new_tree: VDOMNode,
        dirty_state: tuple[set[str], set[str]] | None = None,
    ) -> list[Patch]:
        """Reconcile two trees and return patches."""
        with self._lock:
            previous_dirty = self._active_dirty_keys
            previous_struct = self._active_structural_keys
            if dirty_state is None:
                self._active_dirty_keys = None
                self._active_structural_keys = None
            else:
                self._active_dirty_keys, self._active_structural_keys = dirty_state
            try:
                return self._reconcile_internal(old_tree, new_tree)
            finally:
                self._active_dirty_keys = previous_dirty
                self._active_structural_keys = previous_struct

    def _reconcile_internal(self, old_tree: VDOMNode, new_tree: VDOMNode) -> list[Patch]:
        """Reconcile two trees without acquiring the external lock."""
        from ornata.api.exports.definitions import Patch
        trace_enabled = logger.isEnabledFor(5)
        if trace_enabled:
            logger.log(5, "Starting VDOM tree reconciliation")  # TRACE level

        if not self._should_reconcile(old_tree, new_tree):
            return []

        patches: list[Patch] = []

        # Compare roots
        if old_tree.component_name != new_tree.component_name:
            patches.append(Patch.replace_root(new_tree))
            if trace_enabled:
                logger.log(
                    5,
                    "Root component changed: %s -> %s",
                    old_tree.component_name,
                    new_tree.component_name,
                )  # TRACE
            return patches

        old_hash = getattr(old_tree, "subtree_hash", None)
        new_hash = getattr(new_tree, "subtree_hash", None)
        hashes_match = old_hash is not None and new_hash is not None and old_hash == new_hash
        nodes_clean = not self._node_is_dirty(old_tree) and not self._node_is_dirty(new_tree)
        if hashes_match and nodes_clean:
            if trace_enabled:
                logger.log(5, "Skipping subtree '%s' due to hash match", old_tree.key)
            return patches

        # Compare props
        prop_diffs = self._diff_props(old_tree, new_tree)
        if prop_diffs:
            if old_tree.key is None:
                raise ValueError("Node must have a key to update props")
            patches.append(Patch.update_props(old_tree.key, prop_diffs))
            if trace_enabled:
                logger.log(5, "Properties changed for node '%s': %s", old_tree.key, list(prop_diffs.keys()))  # TRACE

        # Compare children
        child_patches = self._reconcile_children(old_tree, new_tree, trace_enabled)
        patches.extend(child_patches)

        if trace_enabled:
            logger.log(5, "Reconciliation complete: %d patches generated", len(patches))  # TRACE
        return patches

    def _diff_props(self, old_node: VDOMNode, new_node: VDOMNode) -> dict[str, Any]:
        """Find differences between property dictionaries."""
        if self._cython_diff_props is not None:
            return self._cython_diff_props(old_node, new_node)

        diffs: dict[str, Any] = {}
        old_props = old_node.props or {}
        new_props = new_node.props or {}

        old_dirty = bool(getattr(old_node, "props_dirty", False))
        new_dirty = bool(getattr(new_node, "props_dirty", False))

        old_norm = getattr(old_node, "normalized_props", None)
        new_norm = getattr(new_node, "normalized_props", None)
        if (
            not old_dirty
            and not new_dirty
            and old_norm is not None
            and new_norm is not None
            and old_norm == new_norm
        ):
            return diffs

        if not old_dirty and not new_dirty:
            return diffs

        # Find changed and added properties
        for key, new_value in new_props.items():
            if key not in old_props or old_props[key] != new_value:
                diffs[key] = new_value

        # Note: We don't track removed properties as they're handled by node removal
        return diffs

    def _reconcile_children(
        self,
        old_parent: VDOMNode,
        new_parent: VDOMNode,
        trace_enabled: bool,
    ) -> list[Patch]:
        old_children = old_parent.children
        new_children = new_parent.children

        structural_dirty = self._is_structural_dirty(old_parent, new_parent)
        if not structural_dirty and self._active_dirty_keys:
            return self._reconcile_dirty_descendants(old_parent, new_parent)

        if self._children_all_keyed(old_children, new_children):
            return self._reconcile_children_keyed(old_children, new_children, trace_enabled)
        return self._reconcile_children_fallback(old_children, new_children, trace_enabled)

    def _children_all_keyed(self, *groups: list[VDOMNode]) -> bool:
        if self._cython_children_keyed is not None and len(groups) == 2:
            return bool(self._cython_children_keyed(groups[0], groups[1]))
        return all(child.key is not None for group in groups for child in group)

    def _reconcile_children_keyed(
        self,
        old_children: list[VDOMNode],
        new_children: list[VDOMNode],
        trace_enabled: bool,
    ) -> list[Patch]:
        from ornata.api.exports.definitions import Patch
        if self._cython_keyed_fast is not None:
            patches = self._cython_keyed_fast(
                old_children,
                new_children,
                Patch.add_node,
                Patch.move_node,
                Patch.remove_node,
                self._reconcile_internal,
            )
            if trace_enabled:
                self._log_keyed_events(patches)
            return patches
        if self._cython_keyed_plan is not None:
            plan = self._cython_keyed_plan(old_children, new_children)
            return self._apply_keyed_plan(plan, trace_enabled)

        patches: list[Patch] = []
        old_map: dict[str, tuple[int, VDOMNode]] = {
            child.key: (idx, child) for idx, child in enumerate(old_children) if child.key is not None
        }
        seen: set[str] = set()

        for idx, new_child in enumerate(new_children):
            key = new_child.key
            if key is None:
                continue
            info = old_map.get(key)
            if info is None:
                patches.append(Patch.add_node(new_child))
                if trace_enabled:
                    logger.log(5, "Adding node '%s'", key)
                continue

            old_idx, old_child = info
            seen.add(key)
            if old_idx != idx:
                patches.append(Patch.move_node(key, idx))
                if trace_enabled:
                    logger.log(5, "Moving node '%s' from %d to %d", key, old_idx, idx)
            if self._nodes_differ(old_child, new_child):
                patches.extend(self._reconcile_internal(old_child, new_child))

        for key, (_, _) in old_map.items():
            if key not in seen:
                patches.append(Patch.remove_node(key))
                if trace_enabled:
                    logger.log(5, "Removing node '%s'", key)

        return patches

    def _apply_keyed_plan(self, plan: list[tuple[Any, ...]], trace_enabled: bool) -> list[Patch]:
        """Convert Cython plan instructions into Patch objects."""
        from ornata.api.exports.definitions import Patch
        patches: list[Patch] = []
        for instruction in plan:
            if not instruction:
                continue
            op = instruction[0]
            if op == "add":
                node = instruction[1]
                patches.append(Patch.add_node(node))
                if trace_enabled and getattr(node, "key", None):
                    logger.log(5, "Adding node '%s'", node.key)
            elif op == "move":
                key = instruction[1]
                target = instruction[2]
                original = instruction[3] if len(instruction) > 3 else None
                patches.append(Patch.move_node(key, target))
                if trace_enabled:
                    if original is None:
                        logger.log(5, "Moving node '%s' to %d", key, target)
                    else:
                        logger.log(5, "Moving node '%s' from %d to %d", key, original, target)
            elif op == "diff":
                old_node = instruction[1]
                new_node = instruction[2]
                patches.extend(self._reconcile_internal(old_node, new_node))
            elif op == "remove":
                key = instruction[1]
                patches.append(Patch.remove_node(key))
                if trace_enabled:
                    logger.log(5, "Removing node '%s'", key)
            else:
                raise ValueError(f"Unknown Cython keyed reconciliation op: {op}")
        return patches

    def _reconcile_children_fallback(
        self,
        old_children: list[VDOMNode],
        new_children: list[VDOMNode],
        trace_enabled: bool,
    ) -> list[Patch]:
        """Legacy reconciliation path for mixes of keyed/unkeyed nodes."""
        from ornata.api.exports.definitions import Patch
        patches: list[Patch] = []
        append_patch = patches.append

        old_len = len(old_children)
        new_len = len(new_children)
        start = 0

        while start < old_len and start < new_len:
            old_child = old_children[start]
            new_child = new_children[start]
            if old_child.key is None or new_child.key is None or old_child.key != new_child.key:
                break
            if self._nodes_differ(old_child, new_child):
                patches.extend(self._reconcile_internal(old_child, new_child))
            start += 1

        if start == old_len and start == new_len:
            return patches

        suffix_patches: list[list[Patch]] = []
        end_old = old_len
        end_new = new_len
        while end_old > start and end_new > start:
            old_child = old_children[end_old - 1]
            new_child = new_children[end_new - 1]
            if old_child.key is None or new_child.key is None or old_child.key != new_child.key:
                break
            if self._nodes_differ(old_child, new_child):
                suffix_patches.append(self._reconcile_internal(old_child, new_child))
            end_old -= 1
            end_new -= 1

        trimmed_old = old_children[start:end_old]
        trimmed_new = new_children[start:end_new]

        oldkey_map: dict[str, VDOMNode] = {}
        newkey_map: dict[str, VDOMNode] = {}
        old_pos_map: dict[str, int] = {}
        new_pos_map: dict[str, int] = {}

        for index, child in enumerate(trimmed_old):
            if child.key is not None:
                actual_index = start + index
                oldkey_map[child.key] = child
                old_pos_map[child.key] = actual_index

        for index, child in enumerate(trimmed_new):
            if child.key is not None:
                actual_index = start + index
                newkey_map[child.key] = child
                new_pos_map[child.key] = actual_index

        if oldkey_map or newkey_map:
            old_keys = set(oldkey_map)
            new_keys = set(newkey_map)

            removed_keys = old_keys - new_keys
            if removed_keys:
                for key in removed_keys:
                    append_patch(Patch.remove_node(key))
                    if trace_enabled:
                        logger.log(5, "Removing node '%s'", key)

            added_keys = new_keys - old_keys
            if added_keys:
                for key in added_keys:
                    append_patch(Patch.add_node(newkey_map[key]))
                    if trace_enabled:
                        logger.log(5, "Adding node '%s'", key)

            shared_keys = old_keys & new_keys
            for key in shared_keys:
                old_node = oldkey_map[key]
                new_node = newkey_map[key]

                old_pos = old_pos_map.get(key, -1)
                new_pos = new_pos_map.get(key, -1)
                if old_pos != new_pos:
                    append_patch(Patch.move_node(key, new_pos))
                    if trace_enabled:
                        logger.log(5, "Moving node '%s' from %d to %d", key, old_pos, new_pos)

                if self._nodes_differ(old_node, new_node):
                    patches.extend(self._reconcile_internal(old_node, new_node))

        old_unkeyed_iter = (child for child in trimmed_old if child.key is None)
        new_unkeyed_iter = (child for child in trimmed_new if child.key is None)
        for old_child, new_child in zip(old_unkeyed_iter, new_unkeyed_iter, strict=False):
            if self._nodes_differ(old_child, new_child):
                patches.extend(self._reconcile_internal(old_child, new_child))

        if suffix_patches:
            for patch_list in reversed(suffix_patches):
                patches.extend(patch_list)

        return patches

    def _nodes_differ(self, old_node: VDOMNode, new_node: VDOMNode) -> bool:
        """Check if two nodes are different."""
        if self._cython_nodes_differ is not None:
            return bool(self._cython_nodes_differ(old_node, new_node))

        if self._node_is_dirty(old_node) or self._node_is_dirty(new_node):
            return True

        old_hash = getattr(old_node, "subtree_hash", None)
        new_hash = getattr(new_node, "subtree_hash", None)
        if old_hash is not None and new_hash is not None:
            return old_hash != new_hash

        if old_node.component_name != new_node.component_name:
            return True

        if old_node.props != new_node.props:
            return True

        if len(old_node.children) != len(new_node.children):
            return True

        return False

    def _node_is_dirty(self, node: VDOMNode) -> bool:
        """Return True when node has prop or structural dirtiness markers."""

        return bool(getattr(node, "props_dirty", False) or getattr(node, "dirty", False))

    def _should_reconcile(self, old_node: VDOMNode, new_node: VDOMNode) -> bool:
        dirty_keys = self._active_dirty_keys
        if dirty_keys is None:
            return True
        if self._node_is_dirty(old_node) or self._node_is_dirty(new_node):
            return True
        key_candidates: list[str | None] = [
            getattr(old_node, "key", None),
            getattr(new_node, "key", None),
        ]
        if not any(key_candidates):
            return bool(old_node.children or new_node.children)
        for key in key_candidates:
            if key and key in dirty_keys:
                return True
        return bool(old_node.children or new_node.children)

    def _is_structural_dirty(self, old_node: VDOMNode, new_node: VDOMNode) -> bool:
        structural_keys = self._active_structural_keys
        if not structural_keys:
            return False
        for node in (old_node, new_node):
            key = getattr(node, "key", None)
            if key and key in structural_keys:
                return True
        return False

    def _reconcile_dirty_descendants(self, old_parent: VDOMNode, new_parent: VDOMNode) -> list[Patch]:
        from ornata.api.exports.definitions import Patch
        dirty_keys = self._active_dirty_keys
        if not dirty_keys:
            return []
        patches: list[Patch] = []
        old_map: dict[str, VDOMNode] = {}
        for child in old_parent.children:
            if child.key is not None:
                old_map[child.key] = child
        for new_child in new_parent.children:
            key = getattr(new_child, "key", None)
            if key is None or key not in dirty_keys:
                continue
            old_child = old_map.get(key)
            if old_child is None:
                patches.append(Patch.add_node(new_child))
            else:
                patches.extend(self._reconcile_internal(old_child, new_child))
        return patches

    def _log_keyed_events(self, patches: list[Patch]) -> None:
        from ornata.api.exports.definitions import PatchType
        for patch in patches:
            if patch.patch_type == PatchType.ADD_NODE:
                node = patch.data
                key = getattr(node, "key", None)
                logger.log(5, "Adding node '%s'", key)
            elif patch.patch_type == PatchType.REMOVE_NODE:
                logger.log(5, "Removing node '%s'", patch.key)
            elif patch.patch_type == PatchType.MOVE_NODE:
                logger.log(5, "Moving node '%s' to %s", patch.key, patch.data)
