"""VDOM interface functions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ornata.api.exports.definitions import BackendTarget, Patch, VDOMTree
    from ornata.vdom.diffing.reconciler import TreeReconciler


def _get_thread_reconciler() -> TreeReconciler:
    """Return a thread-local reconciler instance."""
    from ornata.api.exports.definitions import RECONCILER_LOCAL
    from ornata.vdom.diffing.reconciler import TreeReconciler
    reconciler = getattr(RECONCILER_LOCAL, "reconciler", None)
    if reconciler is None:
        reconciler = TreeReconciler()
        RECONCILER_LOCAL.reconciler = reconciler
    return reconciler


def create_vdom_tree(root_component: Any, backend_target: BackendTarget) -> VDOMTree:
    """Create a VDOM tree from a root component."""
    from ornata.api.exports.definitions import VDOMTree

    tree = VDOMTree(backend_target=backend_target)
    root_key = tree.add_component(root_component)
    tree.root = tree.key_map.get(root_key)
    return tree


def update_vdom_component(tree: VDOMTree, key: str, new_component: Any) -> list[Patch]:
    """Update a component in the VDOM tree."""
    return tree.update_component(key, new_component)


def reconcile_vdom_trees(old_tree: VDOMTree, new_tree: VDOMTree) -> list[Patch]:
    """Reconcile two VDOM trees."""
    old_root = old_tree.root
    new_root = new_tree.root
    # Per instruction "B": fail loudly if roots are missing (no silent logic change).
    assert old_root is not None and new_root is not None, "VDOM roots must be present before reconciliation"
    return _get_thread_reconciler().reconcile(old_root, new_root, None)
