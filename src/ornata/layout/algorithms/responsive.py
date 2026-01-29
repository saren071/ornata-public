"""Responsive layout logic for adaptive UI design."""

from __future__ import annotations

import logging
from threading import RLock
from typing import TYPE_CHECKING

from ornata.layout.engine.engine import LayoutNode, LayoutStyle

if TYPE_CHECKING:
    from ornata.definitions.dataclasses.layout import Bounds, LayoutResult
    from ornata.definitions.enums import BackendTarget

logger = logging.getLogger(__name__)


class ResponsiveBreakpoint:
    """Represents a responsive breakpoint for layout adaptation."""

    def __init__(self, name: str, min_width: int | None = None, max_width: int | None = None, min_height: int | None = None, max_height: int | None = None) -> None:
        """Initialize a responsive breakpoint.

        Args:
            name: Name of the breakpoint (e.g., "mobile", "tablet", "desktop").
            min_width: Minimum width for this breakpoint.
            max_width: Maximum width for this breakpoint.
            min_height: Minimum height for this breakpoint.
            max_height: Maximum height for this breakpoint.
        """
        self.name = name
        self.min_width = min_width
        self.max_width = max_width
        self.min_height = min_height
        self.max_height = max_height

    def matches(self, bounds: Bounds, backend_target: BackendTarget) -> bool:
        """Check if the current bounds match this breakpoint.

        Args:
            bounds: The current bounds.
            backend_target: The backend target.

        Returns:
            True if the bounds match this breakpoint.
        """
        # Convert bounds to logical units for comparison
        if hasattr(bounds, "to_backend_units"):
             logical_bounds = bounds.to_backend_units(backend_target)
        else:
             logical_bounds = bounds

        width_ok = True
        height_ok = True

        if self.min_width is not None:
            width_ok = width_ok and logical_bounds.width >= self.min_width
        if self.max_width is not None:
            width_ok = width_ok and logical_bounds.width <= self.max_width
        if self.min_height is not None:
            height_ok = height_ok and logical_bounds.height >= self.min_height
        if self.max_height is not None:
            height_ok = height_ok and logical_bounds.height <= self.max_height

        return width_ok and height_ok


class ResponsiveLayoutManager:
    """Manages responsive layout adaptations."""

    def __init__(self) -> None:
        """Initialize the responsive layout manager."""
        self._breakpoints: dict[str, ResponsiveBreakpoint] = {}
        self._lock = RLock()

        # Add default breakpoints
        self.add_breakpoint(ResponsiveBreakpoint("mobile", max_width=768))
        self.add_breakpoint(ResponsiveBreakpoint("tablet", min_width=769, max_width=1024))
        self.add_breakpoint(ResponsiveBreakpoint("desktop", min_width=1025))

    def add_breakpoint(self, breakpoint: ResponsiveBreakpoint) -> None:
        """Add a responsive breakpoint.

        Args:
            breakpoint: The breakpoint to add.
        """
        with self._lock:
            self._breakpoints[breakpoint.name] = breakpoint

    def get_active_breakpoints(self, bounds: Bounds, backend_target: BackendTarget) -> list[ResponsiveBreakpoint]:
        """Get active breakpoints for the current bounds.

        Args:
            bounds: The current bounds.
            backend_target: The backend target.

        Returns:
            List of active breakpoints.
        """
        with self._lock:
            return [bp for bp in self._breakpoints.values() if bp.matches(bounds, backend_target)]

    def adapt_layout_for_breakpoints(self, node: LayoutNode, bounds: Bounds, backend_target: BackendTarget) -> LayoutResult:
        """Adapt layout based on active breakpoints.

        Args:
            node: The layout node to adapt.
            bounds: The container bounds.
            backend_target: The backend target.

        Returns:
            Adapted layout result.
        """
        with self._lock:
            active_breakpoints = self.get_active_breakpoints(bounds, backend_target)

            if not active_breakpoints:
                # Fall back to default layout calculation
                from ornata.layout.engine.engine import compute_layout

                return compute_layout(node, int(bounds.width), int(bounds.height))

            # Apply breakpoint-specific adaptations
            adapted_style = self._adapt_style_for_breakpoints(node.style, active_breakpoints)

            # Create adapted node and calculate layout
            adapted_node = LayoutNode(style=adapted_style, measure=node.measure, children=node.children)
            from ornata.layout.engine.engine import compute_layout

            result = compute_layout(adapted_node, int(bounds.width), int(bounds.height))

            logger.debug(f"Applied responsive adaptations for breakpoints: {[bp.name for bp in active_breakpoints]}")
            return result

    def _adapt_style_for_breakpoints(self, style: LayoutStyle, breakpoints: list[ResponsiveBreakpoint]) -> LayoutStyle:
        """Adapt style properties based on breakpoints.

        Args:
            style: Original style.
            breakpoints: Active breakpoints.

        Returns:
            Adapted style.
        """
        # For now, implement simple adaptations
        # In a full implementation, this would check for breakpoint-specific style overrides

        adapted = LayoutStyle(**style.__dict__)

        # Example adaptations:
        # - Reduce gaps on mobile
        # - Change direction on small screens
        # - Adjust flex properties

        for breakpoint in breakpoints:
            if breakpoint.name == "mobile":
                # Reduce gaps and padding on mobile
                adapted.gap = max(1, style.gap // 2) if style.gap > 1 else style.gap
                adapted.padding = max(0, style.padding - 1) if style.padding > 0 else style.padding
            elif breakpoint.name == "tablet":
                # Moderate adjustments for tablet
                adapted.gap = style.gap
                adapted.padding = style.padding
            elif breakpoint.name == "desktop":
                # Full-size layout for desktop
                adapted.gap = style.gap
                adapted.padding = style.padding

        return adapted


# Global responsive manager instance
_responsive_manager: ResponsiveLayoutManager | None = None


def get_responsive_manager() -> ResponsiveLayoutManager:
    """Get the global responsive layout manager instance.

    Returns:
        The global responsive layout manager.
    """
    global _responsive_manager
    if _responsive_manager is None:
        _responsive_manager = ResponsiveLayoutManager()
    return _responsive_manager


def adapt_layout_responsive(node: LayoutNode, bounds: Bounds, backend_target: BackendTarget) -> LayoutResult:
    """Adapt layout responsively based on container bounds.

    Args:
        node: The layout node to adapt.
        bounds: The container bounds.
        backend_target: The backend target.

    Returns:
        Adapted layout result.
    """
    manager = get_responsive_manager()
    return manager.adapt_layout_for_breakpoints(node, bounds, backend_target)
