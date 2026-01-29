"""Plugin manager for Ornata extensibility.

This module provides a comprehensive plugin management system that supports
loading, registering, and managing plugins with proper lifecycle management.
"""

from __future__ import annotations

import importlib.util
import inspect
import threading
from pathlib import Path

from ornata.api.exports.utils import get_logger
from ornata.plugins.interfaces import ComponentPlugin, EventPlugin, ExportPlugin, LayoutPlugin, Plugin, RendererPlugin, StylePlugin
from ornata.plugins.registry import PluginRegistry

logger = get_logger(__name__)


class PluginManager:
    """Comprehensive plugin manager with lifecycle management and discovery."""

    def __init__(self) -> None:
        self._registry = PluginRegistry()
        self._loaded_plugins: dict[str, Plugin] = {}
        self._plugin_dirs: list[Path] = []
        self._lock = threading.RLock()

    def add_plugin_directory(self, directory: Path | str) -> None:
        """Add a directory to search for plugins.

        Args:
            directory: Directory path to add.
        """
        path = Path(directory)
        if path not in self._plugin_dirs:
            self._plugin_dirs.append(path)
            logger.debug(f"Added plugin directory: {path}")

    def load_plugin(self, plugin_class: type[Plugin], name: str | None = None) -> None:
        """Load a plugin by class.

        Args:
            plugin_class: The plugin class to instantiate and load.
            name: Optional name for the plugin. Defaults to class name.
        """
        with self._lock:
            if name is None:
                name = plugin_class.__name__

            if name in self._loaded_plugins:
                logger.warning(f"Plugin '{name}' is already loaded")
                return

            try:
                plugin = plugin_class()
                plugin.initialize()
                self._loaded_plugins[name] = plugin

                # Register plugin capabilities
                self._register_plugin_capabilities(plugin, name)

                logger.debug(f"Loaded plugin: {name} (version {plugin.version})")

            except Exception as e:
                logger.error(f"Failed to load plugin '{name}': {e}")
                raise

    def unload_plugin(self, name: str) -> None:
        """Unload a plugin.

        Args:
            name: Name of the plugin to unload.
        """
        with self._lock:
            if name not in self._loaded_plugins:
                logger.warning(f"Plugin '{name}' is not loaded")
                return

            plugin = self._loaded_plugins[name]

            try:
                plugin.cleanup()
                self._unregister_plugin_capabilities(plugin, name)
                del self._loaded_plugins[name]

                logger.debug(f"Unloaded plugin: {name}")

            except Exception as e:
                logger.error(f"Error during plugin cleanup '{name}': {e}")

    def discover_and_load_plugins(self) -> int:
        """Discover and load plugins from configured directories.

        Returns:
            Number of plugins loaded.
        """
        loaded_count = 0

        for plugin_dir in self._plugin_dirs:
            if not plugin_dir.exists():
                continue

            # Look for Python files in the plugin directory
            for py_file in plugin_dir.glob("*.py"):
                if py_file.name.startswith("_"):
                    continue

                try:
                    module_name = py_file.stem
                    spec = importlib.util.spec_from_file_location(module_name, py_file)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)

                        # Look for plugin classes in the module
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            if not isinstance(attr, type):
                                continue
                            if not issubclass(attr, Plugin) or attr is Plugin:
                                continue
                            if attr.__module__ != module.__name__:
                                continue
                            if inspect.isabstract(attr):
                                continue

                            self.load_plugin(attr)
                            loaded_count += 1

                except Exception as e:
                    logger.warning(f"Failed to load plugin from {py_file}: {e}")

        # Also try to load via entry points
        loaded_count += self._registry.load_entry_points()

        return loaded_count

    def get_plugin(self, name: str) -> Plugin | None:
        """Get a loaded plugin by name.

        Args:
            name: Name of the plugin.

        Returns:
            The plugin instance if loaded, None otherwise.
        """
        with self._lock:
            return self._loaded_plugins.get(name)

    def list_loaded_plugins(self) -> list[str]:
        """List names of all loaded plugins.

        Returns:
            List of plugin names.
        """
        with self._lock:
            return list(self._loaded_plugins.keys())

    def get_component_plugins(self) -> list[ComponentPlugin]:
        """Get all loaded component plugins.

        Returns:
            List of component plugins.
        """
        with self._lock:
            return [
                plugin for plugin in self._loaded_plugins.values()
                if isinstance(plugin, ComponentPlugin)
            ]

    def get_renderer_plugins(self) -> list[RendererPlugin]:
        """Get all loaded renderer plugins.

        Returns:
            List of renderer plugins.
        """
        with self._lock:
            return [
                plugin for plugin in self._loaded_plugins.values()
                if isinstance(plugin, RendererPlugin)
            ]

    def get_style_plugins(self) -> list[StylePlugin]:
        """Get all loaded style plugins.

        Returns:
            List of style plugins.
        """
        with self._lock:
            return [
                plugin for plugin in self._loaded_plugins.values()
                if isinstance(plugin, StylePlugin)
            ]

    def get_event_plugins(self) -> list[EventPlugin]:
        """Get all loaded event plugins.

        Returns:
            List of event plugins.
        """
        with self._lock:
            return [
                plugin for plugin in self._loaded_plugins.values()
                if isinstance(plugin, EventPlugin)
            ]

    def get_layout_plugins(self) -> list[LayoutPlugin]:
        """Get all loaded layout plugins.

        Returns:
            List of layout plugins.
        """
        with self._lock:
            return [
                plugin for plugin in self._loaded_plugins.values()
                if isinstance(plugin, LayoutPlugin)
            ]

    def get_export_plugins(self) -> list[ExportPlugin]:
        """Get all loaded export plugins.

        Returns:
            List of export plugins.
        """
        with self._lock:
            return [
                plugin for plugin in self._loaded_plugins.values()
                if isinstance(plugin, ExportPlugin)
            ]

    def _register_plugin_capabilities(self, plugin: Plugin, name: str) -> None:
        """Register plugin capabilities with the registry.

        Args:
            plugin: The plugin instance.
            name: Plugin name.
        """
        if isinstance(plugin, ComponentPlugin):
            for comp_type in plugin.get_component_types():
                self._registry.register_component(f"{name}.{comp_type}", plugin.create_component)

        if isinstance(plugin, RendererPlugin):
            for rend_type in plugin.get_renderer_types():
                self._registry.register_renderer(f"{name}.{rend_type}", plugin.create_renderer)

        if isinstance(plugin, LayoutPlugin):
            for layout_type in plugin.get_layout_types():
                self._registry.register_layout(f"{name}.{layout_type}", plugin.calculate_layout)

        # Note: Style and event plugins are handled differently as they integrate
        # directly with the styling and event subsystems

    def _unregister_plugin_capabilities(self, plugin: Plugin, name: str) -> None:
        """Unregister plugin capabilities from the registry.

        Args:
            plugin: The plugin instance.
            name: Plugin name.
        """
        if isinstance(plugin, ComponentPlugin):
            for _comp_type in plugin.get_component_types():
                # Note: The registry doesn't have unregister methods yet
                # This would need to be added if plugin unloading is required
                pass

        if isinstance(plugin, RendererPlugin):
            for _rend_type in plugin.get_renderer_types():
                pass

        if isinstance(plugin, LayoutPlugin):
            for _layout_type in plugin.get_layout_types():
                pass


# Global plugin manager instance
_plugin_manager = PluginManager()


def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager instance.

    Returns:
        The global PluginManager instance.
    """
    return _plugin_manager


def load_plugin(plugin_class: type[Plugin], name: str | None = None) -> None:
    """Load a plugin globally.

    Args:
        plugin_class: The plugin class to load.
        name: Optional name for the plugin.
    """
    _plugin_manager.load_plugin(plugin_class, name)


def unload_plugin(name: str) -> None:
    """Unload a plugin globally.

    Args:
        name: Name of the plugin to unload.
    """
    _plugin_manager.unload_plugin(name)


def discover_plugins() -> int:
    """Discover and load plugins from configured directories.

    Returns:
        Number of plugins loaded.
    """
    return _plugin_manager.discover_and_load_plugins()
