# vdom/diffing/patcher.py
"""VDOM tree patching operations."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger
from ornata.vdom.core.bindings import get_bindings_registry as _core_get_bindings_registry

if TYPE_CHECKING:
    from collections.abc import Callable

    from ornata.api.exports.definitions import Patch, VDOMNode, VDOMTree
    from ornata.vdom.core.bindings import HostBindingRegistry


logger = get_logger(__name__)


def get_bindings_registry() -> "HostBindingRegistry":
    """Return the host binding registry used by patch application."""

    return _core_get_bindings_registry()


class TreePatcher:
    """Applies patches to VDOM trees."""

    def __init__(self) -> None:
        self._lock = threading.RLock()

    def apply_patches(self, tree: VDOMTree, patches: list[Patch]) -> None:
        """Apply a list of patches to a VDOM tree."""
        from ornata.vdom.diffing.scheduler import get_scheduler
        with self._lock:
            logger.log(5, "Applying %d patches to VDOM tree", len(patches))  # TRACE level

            # Begin effect commit batch: effects will flush after all patches apply.
            scheduler = get_scheduler()
            scheduler.begin_commit()
            try:
                for patch in patches:
                    self._apply_patch(tree, patch)
            finally:
                scheduler.end_commit()
                reset_dirty = getattr(tree, "reset_dirty_tracking", None)
                if callable(reset_dirty):
                    reset_dirty()

    def _apply_patch(self, tree: VDOMTree, patch: Patch) -> None:
        """Apply a single patch to the tree."""
        from ornata.api.exports.definitions import PatchType
        if patch.patch_type == PatchType.ADD_NODE:
            self._add_node(tree, patch.data)
        elif patch.patch_type == PatchType.REMOVE_NODE:
            if patch.key is None:
                raise ValueError("Key is required for remove node patch")
            self._remove_node(tree, patch.key)
        elif patch.patch_type == PatchType.UPDATE_PROPS:
            if patch.key is None:
                raise ValueError("Key is required for update props patch")
            self._update_props(tree, patch.key, patch.data)
        elif patch.patch_type == PatchType.REPLACE_ROOT:
            self._replace_root(tree, patch.data)
        elif patch.patch_type == PatchType.MOVE_NODE:
            if patch.key is None:
                raise ValueError("Key is required for move node patch")
            self._move_node(tree, patch.key, patch.data)

    def _add_node(self, tree: VDOMTree, node: VDOMNode | None) -> None:
        """Add a node to the tree."""
        if node is None:
            return

        parent_key = getattr(node, "parent_key", None)
        position = getattr(node, "child_index", 0)
        cloned = node.clone(parent_key=parent_key, index=position)
        attached = tree.attach_node(cloned, parent_key=parent_key, position=position, mark_dirty=False)
        logger.debug("Added node with key '%s' to VDOM tree", attached.key)

        self._create_host_binding(tree, attached)

    def _remove_node(self, tree: VDOMTree, key: str) -> None:
        """Remove a node from the tree."""
        node = tree.key_map.get(key)
        if node is None:
            logger.warning("Node with key '%s' not found, skipping remove", key)
            return

        reg = self._destroy_host_binding(tree, key)
        reg.on_patch_remove_node(tree, key)

        tree.detach_subtree(key)
        logger.debug("Removed node with key '%s' from VDOM tree", key)

    def _update_props(self, tree: VDOMTree, key: str, props: dict[str, Any]) -> None:
        """Update properties of a node."""
        if key not in tree.key_map:
            logger.warning("Node with key '%s' not found, skipping update", key)
            return

        tree.update_node_props(key, props)
        logger.log(5, "Updated properties for node '%s': %s", key, list(props.keys()))  # TRACE

        host_apply: Callable[[Any, dict[str, Any]], None] | None = getattr(tree, "_host_apply_props", None)
        if callable(host_apply):
            reg = get_bindings_registry()
            host = reg.lookup_by_key(tree.backend_target, key)
            if host is not None:
                try:
                    host_apply(host, props)
                except Exception as e:
                    logger.error("Host prop apply failed for key '%s': %s", key, e)

    def _replace_root(self, tree: VDOMTree, new_root: VDOMNode | None) -> None:
        """Replace the root node of the tree."""
        old_root = tree.root
        if old_root is not None and old_root.key is not None:
            reg = self._destroy_host_binding(tree, old_root.key)
            reg.on_patch_remove_node(tree, old_root.key)
            tree.detach_subtree(old_root.key)

        if new_root is None:
            tree.root = None
            logger.debug("Cleared VDOM tree root")
            return

        cloned = new_root.clone(parent_key=None, index=0)
        attached = tree.attach_node(cloned, parent_key=None, position=0, mark_dirty=False)
        logger.debug("Replaced VDOM tree root")
        self._create_host_binding(tree, attached)

    def _move_node(self, tree: VDOMTree, key: str, new_position: int) -> None:
        """Move a node to a new position."""
        if key not in tree.key_map:
            logger.warning("Node with key '%s' not found, skipping move", key)
            return

        tree.move_node(key, new_position)

        host_move: Callable[[Any, int], None] | None = getattr(tree, "_host_move", None)
        if callable(host_move):
            reg = get_bindings_registry()
            host = reg.lookup_by_key(tree.backend_target, key)
            if host is not None:
                try:
                    host_move(host, new_position)
                except Exception as e:
                    logger.error("Host move failed for key '%s': %s", key, e)

        logger.log(5, "Moved node '%s' to position %d", key, new_position)  # TRACE

    def _create_host_binding(self, tree: VDOMTree, node: VDOMNode) -> None:
        """Create renderer bindings for ``node`` when host factories are provided."""
        host_factory: Callable[[VDOMNode], Any] | None = getattr(tree, "_host_factory", None)
        if not callable(host_factory) or node.key is None:
            return

        try:
            host_obj = host_factory(node)
        except Exception as exc:
            logger.error("Host factory failed for key '%s': %s", node.key, exc)
            return

        if host_obj is None:
            return

        reg = get_bindings_registry()
        reg.on_patch_add_node(tree, node.key, host_obj)

    def _destroy_host_binding(self, tree: VDOMTree, key: str) -> "HostBindingRegistry":
        """Destroy host bound to ``key`` and return the registry used.

        Parameters
        ----------
        tree: VDOMTree
            Tree whose backend target provides namespace for host lookup.
        key: str
            VDOM node key whose host should be destroyed.

        Returns
        -------
        HostBindingRegistry
            Registry instance used for the lookup, enabling callers to reuse it.
        """

        reg = get_bindings_registry()
        host = reg.lookup_by_key(tree.backend_target, key)
        if host is not None:
            destroy = getattr(host, "destroy", None)
            if callable(destroy):
                try:
                    destroy()
                except Exception as exc:  # pragma: no cover - logging path
                    logger.error("Host destroy failed for key '%s': %s", key, exc)
        return reg
