"""Auto-generated lazy exports for the plugins subsystem."""

from __future__ import annotations

from importlib import import_module

from ornata.api._warnings import setup_internal_warnings

setup_internal_warnings()

_EXPORT_TARGETS: dict[str, str] = {
    "ComponentPlugin": "ornata.plugins.interfaces:ComponentPlugin",
    "EventPlugin": "ornata.plugins.interfaces:EventPlugin",
    "ExportPlugin": "ornata.plugins.interfaces:ExportPlugin",
    "LayoutPlugin": "ornata.plugins.interfaces:LayoutPlugin",
    "Plugin": "ornata.plugins.interfaces:Plugin",
    "PluginManager": "ornata.plugins.manager:PluginManager",
    "PluginRegistry": "ornata.plugins.registry:PluginRegistry",
    "RendererPlugin": "ornata.plugins.interfaces:RendererPlugin",
    "StylePlugin": "ornata.plugins.interfaces:StylePlugin",
    "discover_plugins": "ornata.plugins.manager:discover_plugins",
    "get_plugin_manager": "ornata.plugins.manager:get_plugin_manager",
    "load_plugin": "ornata.plugins.manager:load_plugin",
    "unload_plugin": "ornata.plugins.manager:unload_plugin",
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
            "module 'ornata.api.exports.plugins' has no attribute {name!r}"
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
