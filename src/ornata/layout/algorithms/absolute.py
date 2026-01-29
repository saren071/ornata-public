"""Absolute positioning layout algorithm implementation."""

from __future__ import annotations

import logging
from threading import RLock
from typing import TYPE_CHECKING

from ornata.definitions.errors import LayoutCalculationError
from ornata.definitions.protocols import LayoutAlgorithm
from ornata.layout.engine.engine import LayoutResult, component_to_layout_node

if TYPE_CHECKING:
    from ornata.definitions.dataclasses.components import Component
    from ornata.definitions.dataclasses.layout import Bounds
    from ornata.definitions.enums import BackendTarget

logger = logging.getLogger(__name__)


class AbsoluteLayout(LayoutAlgorithm):
    """Absolute positioning layout algorithm implementation."""

    def __init__(self) -> None:
        """Initialize the absolute layout algorithm."""
        self._lock = RLock()

    def calculate(self, component: Component, container_bounds: Bounds, backend_target: BackendTarget) -> LayoutResult:
        """Calculate absolute positioning layout for a component.

        Implements proper absolute positioning with support for top, right,
        bottom, left properties relative to the containing block.

        Args:
            component: The renderable component to calculate.
            container_bounds: The bounds of the container.
            backend_target: The target backend type.

        Returns:
            The calculated layout result.

        Raises:
            LayoutCalculationError: If layout calculation fails.
        """
        with self._lock:
            try:
                logger.debug(f"Calculating absolute layout for node with backend: {backend_target}")

                # Convert bounds to renderer units if needed
                bounds = container_bounds.to_backend_units(backend_target)
                available_width = int(bounds.width)
                available_height = int(bounds.height)

                node = component_to_layout_node(component)
                style = node.style

                # Calculate padding and margin
                padding_top = style.padding_top if style.padding_top is not None else style.padding
                padding_right = style.padding_right if style.padding_right is not None else style.padding
                padding_bottom = style.padding_bottom if style.padding_bottom is not None else style.padding
                padding_left = style.padding_left if style.padding_left is not None else style.padding

                margin_top = style.margin_top if style.margin_top is not None else style.margin
                margin_right = style.margin_right if style.margin_right is not None else style.margin
                margin_bottom = style.margin_bottom if style.margin_bottom is not None else style.margin
                margin_left = style.margin_left if style.margin_left is not None else style.margin

                # For absolute positioning, first calculate the natural size
                natural_width = style.width if style.width is not None else 0
                natural_height = style.height if style.height is not None else 0

                if node.measure is not None:
                    measured_width, measured_height = node.measure(available_width, available_height)
                    if style.width is None:
                        natural_width = measured_width
                    if style.height is None:
                        natural_height = measured_height

                # Apply constraints
                natural_width = max(style.min_width or 0, min(style.max_width or natural_width, natural_width))
                natural_height = max(style.min_height or 0, min(style.max_height or natural_height, natural_height))

                # Add padding to content dimensions
                content_width = natural_width + padding_left + padding_right
                content_height = natural_height + padding_top + padding_bottom

                # Position based on absolute properties
                x = margin_left
                y = margin_top

                if style.left is not None:
                    x = style.left
                if style.top is not None:
                    y = style.top
                if style.right is not None:
                    if style.left is not None:
                        # Both left and right specified - stretch
                        content_width = available_width - style.left - style.right - margin_left - margin_right
                    else:
                        x = available_width - content_width - style.right
                if style.bottom is not None:
                    if style.top is not None:
                        # Both top and bottom specified - stretch
                        content_height = available_height - style.top - style.bottom - margin_top - margin_bottom
                    else:
                        y = available_height - content_height - style.bottom

                # Ensure non-negative dimensions
                content_width = max(0, content_width)
                content_height = max(0, content_height)

                result = LayoutResult(x=x, y=y, width=content_width + margin_left + margin_right, height=content_height + margin_top + margin_bottom)

                # Update node layout
                node.layout = result
                return result

            except Exception as e:
                logger.error(f"Absolute layout calculation failed: {e}")
                raise LayoutCalculationError(f"Failed to calculate absolute layout: {e}") from e
