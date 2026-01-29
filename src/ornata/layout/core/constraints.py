"""Layout constraints for advanced layout optimization."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from threading import RLock
from typing import TYPE_CHECKING, Any

from ornata.definitions.dataclasses.layout import Bounds, SpatialIndexEntry

if TYPE_CHECKING:
    from ornata.definitions.dataclasses.components import Component

logger = logging.getLogger(__name__)


class BaseLayoutConstraint(ABC):
    """Base class for layout constraints."""

    def __init__(self) -> None:
        """Initialize constraint."""
        self._lock = RLock()

    @abstractmethod
    def validate(self, component: Component, layout_result: dict[str, Any]) -> bool:
        """Validate if layout result satisfies constraint."""
        pass

    @abstractmethod
    def apply(self, component: Component, layout_result: dict[str, Any]) -> dict[str, Any]:
        """Apply constraint to layout result."""
        pass


class MinSizeConstraint(BaseLayoutConstraint):
    """Constraint for minimum size requirements."""

    def __init__(self, min_width: int | None = None, min_height: int | None = None) -> None:
        """Initialize min size constraint.

        Args:
            min_width: Minimum width requirement.
            min_height: Minimum height requirement.
        """
        super().__init__()
        self.min_width = min_width
        self.min_height = min_height

    def validate(self, component: Component, layout_result: dict[str, Any]) -> bool:
        """Validate minimum size constraint."""
        with self._lock:
            width = layout_result.get('width', 0)
            height = layout_result.get('height', 0)

            if self.min_width is not None and width < self.min_width:
                return False
            if self.min_height is not None and height < self.min_height:
                return False

            return True

    def apply(self, component: Component, layout_result: dict[str, Any]) -> dict[str, Any]:
        """Apply minimum size constraint."""
        with self._lock:
            result = layout_result.copy()

            if self.min_width is not None:
                result['width'] = max(result.get('width', 0), self.min_width)
            if self.min_height is not None:
                result['height'] = max(result.get('height', 0), self.min_height)

            logger.debug(f"Applied min size constraint: {self.min_width}x{self.min_height}")
            return result


class MaxSizeConstraint(BaseLayoutConstraint):
    """Constraint for maximum size limits."""

    def __init__(self, max_width: int | None = None, max_height: int | None = None) -> None:
        """Initialize max size constraint.

        Args:
            max_width: Maximum width limit.
            max_height: Maximum height limit.
        """
        super().__init__()
        self.max_width = max_width
        self.max_height = max_height

    def validate(self, component: Component, layout_result: dict[str, Any]) -> bool:
        """Validate maximum size constraint."""
        with self._lock:
            width = layout_result.get('width', 0)
            height = layout_result.get('height', 0)

            if self.max_width is not None and width > self.max_width:
                return False
            if self.max_height is not None and height > self.max_height:
                return False

            return True

    def apply(self, component: Component, layout_result: dict[str, Any]) -> dict[str, Any]:
        """Apply maximum size constraint."""
        with self._lock:
            result = layout_result.copy()

            if self.max_width is not None:
                result['width'] = min(result.get('width', 0), self.max_width)
            if self.max_height is not None:
                result['height'] = min(result.get('height', 0), self.max_height)

            logger.debug(f"Applied max size constraint: {self.max_width}x{self.max_height}")
            return result


class AspectRatioConstraint(BaseLayoutConstraint):
    """Constraint for maintaining aspect ratio."""

    def __init__(self, ratio: float) -> None:
        """Initialize aspect ratio constraint.

        Args:
            ratio: Width/height aspect ratio to maintain.
        """
        super().__init__()
        self.ratio = ratio

    def validate(self, component: Component, layout_result: dict[str, Any]) -> bool:
        """Validate aspect ratio constraint."""
        with self._lock:
            width = layout_result.get('width', 0)
            height = layout_result.get('height', 0)

            if height == 0:
                return True

            current_ratio = width / height
            return abs(current_ratio - self.ratio) < 0.01  # Small tolerance

    def apply(self, component: Component, layout_result: dict[str, Any]) -> dict[str, Any]:
        """Apply aspect ratio constraint."""
        with self._lock:
            result = layout_result.copy()
            width = result.get('width', 0)
            height = result.get('height', 0)

            if width > 0 and height > 0:
                # Adjust height to match width
                result['height'] = int(width / self.ratio)
            elif width > 0:
                # Calculate height from width
                result['height'] = int(width / self.ratio)
            elif height > 0:
                # Calculate width from height
                result['width'] = int(height * self.ratio)

            logger.debug(f"Applied aspect ratio constraint: {self.ratio}")
            return result


class ContainerFitConstraint(BaseLayoutConstraint):
    """Constraint for fitting content within container bounds."""

    def __init__(self, fit_mode: str = "fit") -> None:
        """Initialize container fit constraint.

        Args:
            fit_mode: How to fit content ("fit", "fill", "stretch").
        """
        super().__init__()
        self.fit_mode = fit_mode

    def validate(self, component: Component, layout_result: dict[str, Any]) -> bool:
        """Validate container fit constraint."""
        # Always valid - constraint is applied during layout
        return True

    def apply(self, component: Component, layout_result: dict[str, Any]) -> dict[str, Any]:
        """Apply container fit constraint."""
        with self._lock:
            # This constraint is primarily used during initial layout calculation
            # rather than as a post-processing step
            logger.debug(f"Applied container fit constraint: {self.fit_mode}")
            return layout_result


class SpatialIndex:
    """Spatial index for efficient layout queries and collision detection."""

    def __init__(self) -> None:
        """Initialize spatial index."""
        self._entries: list[SpatialIndexEntry] = []
        self._lock = RLock()

    def insert(self, component_id: str, bounds: Bounds, layer: int = 0) -> None:
        """Insert component into spatial index.

        Args:
            component_id: Unique component identifier.
            bounds: Component bounds.
            layer: Z-index layer.
        """
        with self._lock:
            entry = SpatialIndexEntry(component_id, bounds, layer)
            self._entries.append(entry)
            logger.debug(f"Inserted {component_id} into spatial index")

    def remove(self, component_id: str) -> None:
        """Remove component from spatial index.

        Args:
            component_id: Component identifier to remove.
        """
        with self._lock:
            self._entries = [e for e in self._entries if e.component_id != component_id]
            logger.debug(f"Removed {component_id} from spatial index")

    def query_bounds(self, bounds: Bounds, layer: int | None = None) -> list[SpatialIndexEntry]:
        """Query components that intersect with given bounds.

        Args:
            bounds: Query bounds.
            layer: Specific layer to query, or None for all layers.

        Returns:
            List of intersecting entries.
        """
        with self._lock:
            results: list[SpatialIndexEntry] = []

            for entry in self._entries:
                if layer is not None and entry.layer != layer:
                    continue

                if self._bounds_intersect(bounds, entry.bounds):
                    results.append(entry)

            return results

    def query_point(self, x: float, y: float, layer: int | None = None) -> list[SpatialIndexEntry]:
        """Query components that contain given point.

        Args:
            x: X coordinate.
            y: Y coordinate.
            layer: Specific layer to query, or None for all layers.

        Returns:
            List of entries containing the point.
        """
        with self._lock:
            results: list[SpatialIndexEntry] = []

            for entry in self._entries:
                if layer is not None and entry.layer != layer:
                    continue

                if (entry.bounds.x <= x <= entry.bounds.x + entry.bounds.width and
                    entry.bounds.y <= y <= entry.bounds.y + entry.bounds.height):
                    results.append(entry)

            return results

    def clear(self) -> None:
        """Clear all entries from spatial index."""
        with self._lock:
            self._entries.clear()
            logger.debug("Cleared spatial index")

    def _bounds_intersect(self, a: Bounds, b: Bounds) -> bool:
        """Check if two bounds rectangles intersect."""
        return (a.x < b.x + b.width and
                a.x + a.width > b.x and
                a.y < b.y + b.height and
                a.y + a.height > b.y)


class ConstraintSolver:
    """Solver for layout constraints with optimization."""

    def __init__(self) -> None:
        """Initialize constraint solver."""
        self._constraints: list[BaseLayoutConstraint] = []
        self._spatial_index = SpatialIndex()
        self._lock = RLock()

    def add_constraint(self, constraint: BaseLayoutConstraint) -> None:
        """Add a layout constraint.

        Args:
            constraint: Constraint to add.
        """
        with self._lock:
            self._constraints.append(constraint)
            logger.debug(f"Added constraint: {type(constraint).__name__}")

    def solve_constraints(self, component: Component, initial_layout: dict[str, Any]) -> dict[str, Any]:
        """Solve all constraints for a component layout.

        Args:
            component: The component being laid out.
            initial_layout: Initial layout result.

        Returns:
            Optimized layout result satisfying all constraints.
        """
        with self._lock:
            layout = initial_layout.copy()

            # Apply constraints in order
            for constraint in self._constraints:
                if not constraint.validate(component, layout):
                    layout = constraint.apply(component, layout)

            # Update spatial index
            bounds = Bounds(
                x=layout.get('x', 0),
                y=layout.get('y', 0),
                width=layout.get('width', 0),
                height=layout.get('height', 0)
            )
            self._spatial_index.insert(getattr(component, 'component_name', 'unknown'), bounds)

            return layout

    def check_collisions(self, bounds: Bounds, exclude_component: str | None = None) -> list[str]:
        """Check for collisions with existing layouts.

        Args:
            bounds: Bounds to check.
            exclude_component: Component to exclude from collision check.

        Returns:
            List of component IDs that collide with the bounds.
        """
        with self._lock:
            intersecting = self._spatial_index.query_bounds(bounds)
            collisions: list[str] = []

            for entry in intersecting:
                if exclude_component is None or entry.component_id != exclude_component:
                    collisions.append(entry.component_id)

            return collisions

    def optimize_layout(self, components: list[Component]) -> dict[str, dict[str, int | float]]:
        """Optimize layout for multiple components with constraints.

        Args:
            components: List of components to layout.

        Returns:
            Dictionary mapping component names to optimized layouts.
        """
        with self._lock:
            layouts: dict[str, dict[str, int | float]] = {}

            # Clear spatial index for fresh optimization
            self._spatial_index.clear()

            # First pass: calculate unconstrained layouts
            for component in components:
                # Get basic layout (simplified)
                layout: dict[str, int | float] = {
                    'width': getattr(component, 'width', 100),
                    'height': getattr(component, 'height', 50),
                    'x': 0,
                    'y': 0
                }
                if component.component_name is None:
                    raise ValueError(f"Component {component} has no name")
                layouts[component.component_name] = layout

            # Second pass: apply constraints and resolve collisions
            optimized_layouts: dict[str, dict[str, int | float]] = {}
            for component in components:
                if component.component_name is None:
                    raise ValueError(f"Component {component} has no name")
                layout = layouts[component.component_name]
                optimized = self.solve_constraints(component, layout)

                # Resolve collisions by adjusting position
                bounds = Bounds(
                    x=optimized.get('x', 0),
                    y=optimized.get('y', 0),
                    width=optimized.get('width', 0),
                    height=optimized.get('height', 0)
                )

                collisions = self.check_collisions(bounds, component.component_name)
                if collisions:
                    # Simple collision resolution: offset by collision count
                    optimized['x'] = bounds.x + len(collisions) * 10
                    optimized['y'] = bounds.y + len(collisions) * 10

                optimized_layouts[component.component_name] = optimized

            logger.debug(f"Optimized layout for {len(components)} components")
            return optimized_layouts
