"""Docking layout algorithm implementation."""

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


class DockingLayout(LayoutAlgorithm):
    """Docking layout algorithm implementation."""

    def __init__(self) -> None:
        """Initialize the docking layout algorithm."""
        self._lock = RLock()

    def calculate(self, component: Component, container_bounds: Bounds, backend_target: BackendTarget) -> LayoutResult:
        """Calculate docking layout for a component.

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
                logger.debug(f"Calculating docking layout for node with backend: {backend_target}")

                bounds = container_bounds.to_backend_units(backend_target)
                available_width = int(bounds.width)
                available_height = int(bounds.height)
                
                node = component_to_layout_node(component)
                
                # Remaining space for 'fill' content
                remaining_x = 0
                remaining_y = 0
                remaining_w = available_width
                remaining_h = available_height

                # Process children
                for child in node.children:
                    if child.style.display == "none":
                        continue
                    
                    # Determine dock position from style (e.g., using a custom property or 'align_self')
                    # For simplicity, we check a hypothetical 'dock' property in component_extras
                    dock = "fill"
                    if child.style.component_extras:
                        dock = child.style.component_extras.get("dock", "fill")
                    
                    # Measure child
                    w, h = 0, 0
                    if child.measure:
                        w, h = child.measure(remaining_w, remaining_h)
                    
                    # Apply dock logic
                    child_x, child_y, child_w, child_h = 0, 0, 0, 0
                    
                    if dock == "top":
                        child_x, child_y = remaining_x, remaining_y
                        child_w, child_h = remaining_w, h
                        remaining_y += h
                        remaining_h -= h
                    elif dock == "bottom":
                        child_h = h
                        child_w = remaining_w
                        child_x = remaining_x
                        child_y = remaining_y + remaining_h - h
                        remaining_h -= h
                    elif dock == "left":
                        child_x, child_y = remaining_x, remaining_y
                        child_w, child_h = w, remaining_h
                        remaining_x += w
                        remaining_w -= w
                    elif dock == "right":
                        child_w = w
                        child_h = remaining_h
                        child_x = remaining_x + remaining_w - w
                        child_y = remaining_y
                        remaining_w -= w
                    else: # fill
                        child_x, child_y = remaining_x, remaining_y
                        child_w, child_h = remaining_w, remaining_h
                        # Fill consumes remaining space, usually last item
                    
                    child.layout = LayoutResult(x=child_x, y=child_y, width=child_w, height=child_h)

                # Container size matches available space for docking
                result = LayoutResult(x=0, y=0, width=available_width, height=available_height)
                node.layout = result
                return result

            except Exception as e:
                logger.error(f"Docking layout calculation failed: {e}")
                raise LayoutCalculationError(f"Failed to calculate docking layout: {e}") from e