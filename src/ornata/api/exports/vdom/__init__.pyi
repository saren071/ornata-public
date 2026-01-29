"""Type stubs for the vdom subsystem exports."""

from __future__ import annotations

from ornata.vdom.core import keys as keys
from ornata.vdom.core import refs as refs
from ornata.vdom.core import tree as tree
from ornata.vdom.core.bindings import HostBindingRegistry as HostBindingRegistry
from ornata.vdom.core.bindings import get_bindings_registry as get_bindings_registry
from ornata.vdom.core.interfaces import _get_thread_reconciler as _get_thread_reconciler  # type: ignore
from ornata.vdom.core.interfaces import create_vdom_tree as create_vdom_tree
from ornata.vdom.core.interfaces import reconcile_vdom_trees as reconcile_vdom_trees
from ornata.vdom.core.interfaces import update_vdom_component as update_vdom_component
from ornata.vdom.core.keys import ComponentKeys as ComponentKeys
from ornata.vdom.core.refs import ComponentRefs as ComponentRefs
from ornata.vdom.core.tree import _clear_subtree_dirty as _clear_subtree_dirty  # type: ignore [private]
from ornata.vdom.core.tree import _clone_props_dict as _clone_props_dict  # type: ignore [private]
from ornata.vdom.core.tree import _recompute_node_hash as _recompute_node_hash  # type: ignore [private]
from ornata.vdom.diffing import incremental as incremental
from ornata.vdom.diffing import lifecycle as lifecycle
from ornata.vdom.diffing import patcher as patcher
from ornata.vdom.diffing import reconciler as reconciler
from ornata.vdom.diffing.algorithms import IncrementalDiff as IncrementalDiff
from ornata.vdom.diffing.algorithms import KeyedDiff as KeyedDiff
from ornata.vdom.diffing.algorithms import SimpleDiff as SimpleDiff
from ornata.vdom.diffing.cache import DiffCache as DiffCache
from ornata.vdom.diffing.engine import DiffingEngine as DiffingEngine
from ornata.vdom.diffing.incremental import IncrementalDiffer as IncrementalDiffer
from ornata.vdom.diffing.interfaces import apply_patches as apply_patches
from ornata.vdom.diffing.interfaces import diff_vdom_trees as diff_vdom_trees
from ornata.vdom.diffing.lifecycle import ComponentLifecycle as ComponentLifecycle
from ornata.vdom.diffing.object_pool import PatchObjectPool as PatchObjectPool
from ornata.vdom.diffing.object_pool import PatchPool as PatchPool
from ornata.vdom.diffing.object_pool import PatchPoolStats as PatchPoolStats
from ornata.vdom.diffing.object_pool import PooledPatch as PooledPatch
from ornata.vdom.diffing.object_pool import get_patch_object_pool as get_patch_object_pool
from ornata.vdom.diffing.object_pool import pooled_patch as pooled_patch
from ornata.vdom.diffing.optimization import PatchOptimizer as PatchOptimizer
from ornata.vdom.diffing.patcher import TreePatcher as TreePatcher
from ornata.vdom.diffing.reconciler import TreeReconciler as TreeReconciler
from ornata.vdom.diffing.scheduler import EffectScheduler as EffectScheduler
from ornata.vdom.diffing.scheduler import get_scheduler as get_scheduler
from ornata.vdom.memory.memory import MemoryManager as MemoryManager

__all__ = [
    "ComponentKeys",
    "ComponentLifecycle",
    "ComponentRefs",
    "MemoryManager",
    "TreePatcher",
    "TreeReconciler",
    "_clone_props_dict",
    "_get_thread_reconciler",
    "create_vdom_tree",
    "keys",
    "lifecycle",
    "patcher",
    "reconcile_vdom_trees",
    "reconciler",
    "refs",
    "tree",
    "update_vdom_component",
    "DiffCache",
    "DiffingEngine",
    "IncrementalDiff",
    "IncrementalDiffer",
    "KeyedDiff",
    "PatchObjectPool",
    "PatchOptimizer",
    "PatchPool",
    "PatchPoolStats",
    "PooledPatch",
    "SimpleDiff",
    "apply_patches",
    "diff_vdom_trees",
    "get_patch_object_pool",
    "incremental",
    "pooled_patch",
    "EffectScheduler",
    "get_bindings_registry",
    "get_scheduler",
    "HostBindingRegistry",
    "_recompute_node_hash",
    "_clear_subtree_dirty",
]
