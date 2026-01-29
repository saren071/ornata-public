"""Auto-generated exports for ornata.plugins."""

from __future__ import annotations

from . import interfaces, manager, registry
from .interfaces import (
    ComponentPlugin,
    EventPlugin,
    ExportPlugin,
    LayoutPlugin,
    Plugin,
    RendererPlugin,
    StylePlugin,
)
from .manager import (
    PluginManager,
    discover_plugins,
    get_plugin_manager,
    load_plugin,
    unload_plugin,
)
from .registry import PluginRegistry

__all__ = [
    "ComponentPlugin",
    "EventPlugin",
    "ExportPlugin",
    "LayoutPlugin",
    "Plugin",
    "PluginManager",
    "PluginRegistry",
    "RendererPlugin",
    "StylePlugin",
    "discover_plugins",
    "get_plugin_manager",
    "interfaces",
    "load_plugin",
    "manager",
    "registry",
    "unload_plugin",
]
