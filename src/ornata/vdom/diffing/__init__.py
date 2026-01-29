"""Auto-generated exports for ornata.vdom.diffing."""

from __future__ import annotations

from . import (
    algorithms,
    cache,
    engine,
    incremental,
    interfaces,
    lifecycle,
    object_pool,
    optimization,
    patcher,
    reconciler,
    scheduler,
)
from .algorithms import IncrementalDiff, KeyedDiff, SimpleDiff
from .cache import DiffCache
from .engine import DiffingEngine
from .incremental import IncrementalDiffer
from .interfaces import apply_patches, diff_vdom_trees
from .lifecycle import ComponentLifecycle
from .object_pool import (
    PatchObjectPool,
    PatchPool,
    PooledPatch,
    get_patch_object_pool,
    pooled_patch,
)
from .optimization import PatchOptimizer
from .patcher import TreePatcher
from .reconciler import TreeReconciler
from .scheduler import EffectScheduler, get_scheduler

__all__ = [
    "ComponentLifecycle",
    "DiffCache",
    "DiffingEngine",
    "EffectScheduler",
    "get_scheduler",
    "IncrementalDiff",
    "IncrementalDiffer",
    "KeyedDiff",
    "PatchObjectPool",
    "PatchOptimizer",
    "PatchPool",
    "PooledPatch",
    "SimpleDiff",
    "TreePatcher",
    "TreeReconciler",
    "algorithms",
    "apply_patches",
    "cache",
    "diff_vdom_trees",
    "engine",
    "get_patch_object_pool",
    "incremental",
    "interfaces",
    "lifecycle",
    "object_pool",
    "optimization",
    "pooled_patch",
    "patcher",
    "reconciler",
    "scheduler",
]
