"""Auto-generated lazy exports for the utils subsystem."""

from __future__ import annotations

from importlib import import_module

from ornata.api._warnings import setup_internal_warnings

setup_internal_warnings()

_EXPORT_TARGETS: dict[str, str] = {
    "cache": "ornata.utils:cache",
    "lock": "ornata.utils:lock",
    "logging": "ornata.utils:logging",
    "memory": "ornata.utils:memory",
    "LFUCache": "ornata.utils.cache:LFUCache",
    "LRUCache": "ornata.utils.cache:LRUCache",
    "SimpleCache": "ornata.utils.cache:SimpleCache",
    "ThreadSafeLFUCache": "ornata.utils.cache:ThreadSafeLFUCache",
    "ThreadSafeLRUCache": "ornata.utils.cache:ThreadSafeLRUCache",
    "ThreadSafeSimpleCache": "ornata.utils.cache:ThreadSafeSimpleCache",
    "ThreadSafeTTLCache": "ornata.utils.cache:ThreadSafeTTLCache",
    "TTLCache": "ornata.utils.cache:TTLCache",
    "Lock": "ornata.utils.lock:Lock",
    "NoOpLock": "ornata.utils.lock:NoOpLock",
    "ReadWriteLock": "ornata.utils.lock:ReadWriteLock",
    "SpinLock": "ornata.utils.lock:SpinLock",
    "OrnataFormatter": "ornata.utils.logging:OrnataFormatter",
    "OrnataHandler": "ornata.utils.logging:OrnataHandler",
    "get_logger": "ornata.utils.logging:get_logger",
    "ArenaAllocator": "ornata.utils.memory:ArenaAllocator",
    "MemoryPool": "ornata.utils.memory:MemoryPool",
    "SlabAllocator": "ornata.utils.memory:SlabAllocator",
    "ThreadSafeArenaAllocator": "ornata.utils.memory:ThreadSafeArenaAllocator",
    "ThreadSafeMemoryPool": "ornata.utils.memory:ThreadSafeMemoryPool",
    "ThreadSafeSlabAllocator": "ornata.utils.memory:ThreadSafeSlabAllocator",
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
            "module 'ornata.api.exports.utils' has no attribute {name!r}"
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
