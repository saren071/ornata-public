"""Auto-generated lazy exports for the events subsystem."""

from __future__ import annotations

from importlib import import_module

from ornata.api._warnings import setup_internal_warnings

setup_internal_warnings()

_EXPORT_TARGETS: dict[str, str] = {
    "handlers": "ornata.events.handlers:handlers",
    "history": "ornata.events:history",
    "processing": "ornata.events:processing",
    "bus": "ornata.events.core:bus",
    "subsystem": "ornata.events.core:subsystem",
    "EventBus": "ornata.events.core.bus:EventBus",
    "GlobalEventBus": "ornata.events.core.bus:GlobalEventBus",
    "LockFreeEventQueue": "ornata.events.core.bus:LockFreeEventQueue",
    "SubsystemEventBus": "ornata.events.core.bus:SubsystemEventBus",
    "EventObjectPool": "ornata.events.core.object_pool:EventObjectPool",
    "EventPool": "ornata.events.core.object_pool:EventPool",
    "EventPoolConfig": "ornata.events.core.object_pool:EventPoolConfig",
    "EventPoolStats": "ornata.events.core.object_pool:EventPoolStats",
    "PooledComponentEvent": "ornata.events.core.object_pool:PooledComponentEvent",
    "PooledEvent": "ornata.events.core.object_pool:PooledEvent",
    "PooledKeyEvent": "ornata.events.core.object_pool:PooledKeyEvent",
    "PooledMouseEvent": "ornata.events.core.object_pool:PooledMouseEvent",
    "get_event_object_pool": "ornata.events.core.object_pool:get_event_object_pool",
    "pooled_component_event": "ornata.events.core.object_pool:pooled_component_event",
    "pooled_event": "ornata.events.core.object_pool:pooled_event",
    "pooled_key_event": "ornata.events.core.object_pool:pooled_key_event",
    "pooled_mouse_event": "ornata.events.core.object_pool:pooled_mouse_event",
    "EventSubsystem": "ornata.events.core.subsystem:EventSubsystem",
    "add_event_listener": "ornata.events.core.subsystem:add_event_listener",
    "create_event_subsystem": "ornata.events.core.subsystem:create_event_subsystem",
    "dispatch_cross_subsystem_event": "ornata.events.core.subsystem:dispatch_cross_subsystem_event",
    "EventHandler": "ornata.events.handlers.handlers:EventHandler",
    "EventHandlerManager": "ornata.events.handlers.handlers:EventHandlerManager",
    "replay": "ornata.events.history:replay",
    "EventEntry": "ornata.events.history.replay:EventEntry",
    "EventReplayAnalyzer": "ornata.events.history.replay:EventReplayAnalyzer",
    "EventReplayBuffer": "ornata.events.history.replay:EventReplayBuffer",
    "EventReplayer": "ornata.events.history.replay:EventReplayer",
    "create_event_replayer": "ornata.events.history.replay:create_event_replayer",
    "create_replay_analyzer": "ornata.events.history.replay:create_replay_analyzer",
    "create_replay_buffer": "ornata.events.history.replay:create_replay_buffer",
    "factory": "ornata.events.platform:factory",
    "CliEventHandler": "ornata.events.platform.cli:CliEventHandler",
    "create_cli_handler": "ornata.events.platform.cli:create_cli_handler",
    "PlatformEventHandler": "ornata.events.platform.factory:PlatformEventHandler",
    "create_platform_handler": "ornata.events.platform.factory:create_platform_handler",
    "WindowsEventHandler": "ornata.events.platform.windows:WindowsEventHandler",
    "create_windows_handler": "ornata.events.platform.windows:create_windows_handler",
    "async_processor": "ornata.events.processing:async_processor",
    "filtering": "ornata.events.processing:filtering",
    "propagation": "ornata.events.processing:propagation",
    "AsyncEventProcessor": "ornata.events.processing.async_processor:AsyncEventProcessor",
    "BatchedEventProcessor": "ornata.events.processing.async_processor:BatchedEventProcessor",
    "EventQueue": "ornata.events.processing.async_processor:EventQueue",
    "EventDropFilter": "ornata.events.processing.filtering:EventDropFilter",
    "EventFilter": "ornata.events.processing.filtering:EventFilter",
    "EventFilterManager": "ornata.events.processing.filtering:EventFilterManager",
    "EventModifyFilter": "ornata.events.processing.filtering:EventModifyFilter",
    "EventThrottleFilter": "ornata.events.processing.filtering:EventThrottleFilter",
    "EventTransformer": "ornata.events.processing.filtering:EventTransformer",
    "create_drop_filter": "ornata.events.processing.filtering:create_drop_filter",
    "create_modify_filter": "ornata.events.processing.filtering:create_modify_filter",
    "create_throttle_filter": "ornata.events.processing.filtering:create_throttle_filter",
    "EventPropagationEngine": "ornata.events.processing.propagation:EventPropagationEngine"
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
            "module 'ornata.api.exports.events' has no attribute {name!r}"
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
