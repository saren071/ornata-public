"""Auto-generated lazy exports for the vdom subsystem."""

from __future__ import annotations

from importlib import import_module

from ornata.api._warnings import setup_internal_warnings

setup_internal_warnings()

_EXPORT_TARGETS: dict[str, str] = {
    'keys': 'ornata.vdom.core:keys',
    'refs': 'ornata.vdom.core:refs',
    'tree': 'ornata.vdom.core:tree',
    'HostBindingRegistry': 'ornata.vdom.core.bindings:HostBindingRegistry',
    'get_bindings_registry': 'ornata.vdom.core.bindings:get_bindings_registry',
    '_get_thread_reconciler': 'ornata.vdom.core.interfaces:_get_thread_reconciler',
    'create_vdom_tree': 'ornata.vdom.core.interfaces:create_vdom_tree',
    'reconcile_vdom_trees': 'ornata.vdom.core.interfaces:reconcile_vdom_trees',
    'update_vdom_component': 'ornata.vdom.core.interfaces:update_vdom_component',
    'ComponentKeys': 'ornata.vdom.core.keys:ComponentKeys',
    'ComponentRefs': 'ornata.vdom.core.refs:ComponentRefs',
    '_clone_props_dict': 'ornata.vdom.core.tree:_clone_props_dict',
    'incremental': 'ornata.vdom.diffing:incremental',
    'lifecycle': 'ornata.vdom.diffing:lifecycle',
    'patcher': 'ornata.vdom.diffing:patcher',
    'reconciler': 'ornata.vdom.diffing:reconciler',
    'IncrementalDiff': 'ornata.vdom.diffing.algorithms:IncrementalDiff',
    'KeyedDiff': 'ornata.vdom.diffing.algorithms:KeyedDiff',
    'SimpleDiff': 'ornata.vdom.diffing.algorithms:SimpleDiff',
    'DiffCache': 'ornata.vdom.diffing.cache:DiffCache',
    'DiffingEngine': 'ornata.vdom.diffing.engine:DiffingEngine',
    'IncrementalDiffer': 'ornata.vdom.diffing.incremental:IncrementalDiffer',
    'apply_patches': 'ornata.vdom.diffing.interfaces:apply_patches',
    'diff_vdom_trees': 'ornata.vdom.diffing.interfaces:diff_vdom_trees',
    'ComponentLifecycle': 'ornata.vdom.diffing.lifecycle:ComponentLifecycle',
    'PatchObjectPool': 'ornata.vdom.diffing.object_pool:PatchObjectPool',
    'PatchPool': 'ornata.vdom.diffing.object_pool:PatchPool',
    'PatchPoolStats': 'ornata.vdom.diffing.object_pool:PatchPoolStats',
    'PooledPatch': 'ornata.vdom.diffing.object_pool:PooledPatch',
    'get_patch_object_pool': 'ornata.vdom.diffing.object_pool:get_patch_object_pool',
    'pooled_patch': 'ornata.vdom.diffing.object_pool:pooled_patch',
    'PatchOptimizer': 'ornata.vdom.diffing.optimization:PatchOptimizer',
    'TreePatcher': 'ornata.vdom.diffing.patcher:TreePatcher',
    'TreeReconciler': 'ornata.vdom.diffing.reconciler:TreeReconciler',
    'EffectScheduler': 'ornata.vdom.diffing.scheduler:EffectScheduler',
    'get_scheduler': 'ornata.vdom.diffing.scheduler:get_scheduler',
    'MemoryManager': 'ornata.vdom.memory.memory:MemoryManager',
    "_recompute_node_hash": 'ornata.vdom.core.tree:_recompute_node_hash',
    "_clear_subtree_dirty": 'ornata.vdom.core.tree:_clear_subtree_dirty',
}

_RESOLVED_EXPORTS: dict[str, object] = {}

__all__ = ["__getattr__"]

def _load_target(name: str) -> object:
    """Load and cache ``name`` for this subsystem.

    Parameters
    ----------
    name : str
        Export name to resolve.

    Returns
    -------
    object
        Resolved attribute from the owning module.

    Raises
    ------
    AttributeError
        If ``name`` is unknown to this subsystem.
    """

    target = _EXPORT_TARGETS.get(name)
    if target is None:
        raise AttributeError(
            "module 'ornata.api.exports.vdom' has no attribute {name!r}"
        )
    module_name, _, attr_name = target.partition(':')
    module = import_module(module_name)
    value = getattr(module, attr_name)
    _RESOLVED_EXPORTS[name] = value
    globals()[name] = value
    return value

def __getattr__(name: str) -> object:
    """Resolve an export attribute on first access.

    Parameters
    ----------
    name : str
        Export name requested from this module.

    Returns
    -------
    object
        Resolved export value.

    Raises
    ------
    AttributeError
        If ``name`` is not part of this subsystem.
    """

    if name in _RESOLVED_EXPORTS:
        return _RESOLVED_EXPORTS[name]
    return _load_target(name)

def __dir__() -> list[str]:
    """Return the sorted list of exportable names.

    Returns
    -------
    list[str]
        Sorted names available via this module.
    """

    names = ['__getattr__']
    names.extend(_EXPORT_TARGETS)
    return sorted(names)
