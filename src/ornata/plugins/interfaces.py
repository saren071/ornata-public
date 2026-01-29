"""Plugin interfaces for Ornata extensibility.

This module defines the abstract base classes and interfaces that plugins
must implement to extend Ornata functionality.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ornata.api.exports.definitions import Component, Event, LayoutResult, ResolvedStyle
    from ornata.api.exports.rendering import Renderer


class Plugin(ABC):
    """Base class for all Ornata plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version."""
        pass

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the plugin."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up plugin resources."""
        pass


class ComponentPlugin(Plugin):
    """Plugin interface for custom components."""

    @abstractmethod
    def get_component_types(self) -> list[str]:
        """Return list of component types this plugin provides.

        Returns:
            List of component type names.
        """
        pass

    @abstractmethod
    def create_component(self, component_type: str, *args: Any, **kwargs: Any) -> Component:
        """Create a component instance.

        Args:
            component_type: The type of component to create.
            *args: Positional arguments for component creation.
            **kwargs: Keyword arguments for component creation.

        Returns:
            A new component instance.

        Raises:
            ValueError: If component type is not supported.
        """
        pass


class RendererPlugin(Plugin):
    """Plugin interface for custom renderers."""

    @abstractmethod
    def get_renderer_types(self) -> list[str]:
        """Return list of renderer types this plugin provides.

        Returns:
            List of renderer type names.
        """
        pass

    @abstractmethod
    def create_renderer(self, renderer_type: str, *args: Any, **kwargs: Any) -> Renderer:
        """Create a renderer instance.

        Args:
            renderer_type: The type of renderer to create.
            *args: Positional arguments for renderer creation.
            **kwargs: Keyword arguments for renderer creation.

        Returns:
            A new renderer instance.

        Raises:
            ValueError: If renderer type is not supported.
        """
        pass


class StylePlugin(Plugin):
    """Plugin interface for custom styling."""

    @abstractmethod
    def get_style_properties(self) -> list[str]:
        """Return list of custom style properties this plugin provides.

        Returns:
            List of style property names.
        """
        pass

    @abstractmethod
    def resolve_custom_style(
        self,
        component_name: str,
        property_name: str,
        property_value: Any,
        context: Any
    ) -> ResolvedStyle:
        """Resolve a custom style property.

        Args:
            component_name: Name of the component.
            property_name: Name of the custom property.
            property_value: Value of the custom property.
            context: Style resolution context.

        Returns:
            Resolved style information.
        """
        pass


class EventPlugin(Plugin):
    """Plugin interface for custom event handling."""

    @abstractmethod
    def get_event_types(self) -> list[str]:
        """Return list of custom event types this plugin provides.

        Returns:
            List of event type names.
        """
        pass

    @abstractmethod
    def handle_event(self, event: Event) -> bool:
        """Handle a custom event.

        Args:
            event: The event to handle.

        Returns:
            True if the event was handled, False otherwise.
        """
        pass


class LayoutPlugin(Plugin):
    """Plugin interface for custom layout algorithms."""

    @abstractmethod
    def get_layout_types(self) -> list[str]:
        """Return list of layout types this plugin provides.

        Returns:
            List of layout type names.
        """
        pass

    @abstractmethod
    def calculate_layout(
        self,
        layout_type: str,
        component: Component,
        container_bounds: Any,
        renderer_type: Any
    ) -> LayoutResult:
        """Calculate layout using a custom algorithm.

        Args:
            layout_type: The type of layout to calculate.
            component: The component to layout.
            container_bounds: Bounds of the container.
            renderer_type: Type of renderer.

        Returns:
            Layout calculation result.

        Raises:
            ValueError: If layout type is not supported.
        """
        pass


class ExportPlugin(Plugin):
    """Plugin interface for custom export formats."""

    @abstractmethod
    def get_export_formats(self) -> list[str]:
        """Return list of export formats this plugin provides.

        Returns:
            List of export format names.
        """
        pass

    @abstractmethod
    def export_component(
        self,
        component: Component,
        format_name: str,
        **options: Any
    ) -> str:
        """Export a component to a custom format.

        Args:
            component: The component to export.
            format_name: The export format name.
            **options: Export options.

        Returns:
            Exported content as string.

        Raises:
            ValueError: If export format is not supported.
        """
        pass
