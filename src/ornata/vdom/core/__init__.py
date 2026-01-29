"""Auto-generated exports for ornata.vdom.core."""

from __future__ import annotations

from . import binding_integration, interfaces, keys, refs, tree
from .interfaces import (
    _get_thread_reconciler,  # type: ignore [private]
    create_vdom_tree,
    reconcile_vdom_trees,
    update_vdom_component,
)
from .keys import ComponentKeys
from .refs import ComponentRefs
from .tree import _clone_props_dict, _recompute_node_hash  # type: ignore [private]

__all__ = [
    "ComponentKeys",
    "ComponentRefs",
    "_clone_props_dict",
    "_get_thread_reconciler",
    "create_vdom_tree",
    "interfaces",
    "keys",
    "reconcile_vdom_trees",
    "refs",
    "tree",
    "update_vdom_component",
    "binding_integration",
    "_recompute_node_hash",
]
