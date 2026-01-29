"""Type stubs for the plugins subsystem exports."""

from __future__ import annotations

from ornata.plugins.interfaces import ComponentPlugin as ComponentPlugin
from ornata.plugins.interfaces import EventPlugin as EventPlugin
from ornata.plugins.interfaces import ExportPlugin as ExportPlugin
from ornata.plugins.interfaces import LayoutPlugin as LayoutPlugin
from ornata.plugins.interfaces import Plugin as Plugin
from ornata.plugins.interfaces import RendererPlugin as RendererPlugin
from ornata.plugins.interfaces import StylePlugin as StylePlugin
from ornata.plugins.manager import PluginManager as PluginManager
from ornata.plugins.manager import discover_plugins as discover_plugins
from ornata.plugins.manager import get_plugin_manager as get_plugin_manager
from ornata.plugins.manager import load_plugin as load_plugin  #type: ignore
from ornata.plugins.manager import unload_plugin as unload_plugin
from ornata.plugins.registry import PluginRegistry as PluginRegistry

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
    "load_plugin",
    "unload_plugin",
]