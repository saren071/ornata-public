"""CSS Grid layout algorithm implementation."""

from __future__ import annotations

import logging
from threading import RLock
from typing import TYPE_CHECKING

from ornata.definitions.dataclasses.layout import LayoutResult
from ornata.definitions.errors import LayoutCalculationError
from ornata.definitions.protocols import LayoutAlgorithm
from ornata.layout.engine.engine import LayoutNode, component_to_layout_node

if TYPE_CHECKING:
    from ornata.definitions.dataclasses.components import Component
    from ornata.definitions.dataclasses.layout import Bounds
    from ornata.definitions.enums import BackendTarget

logger = logging.getLogger(__name__)


class GridLayout(LayoutAlgorithm):
    """CSS Grid layout algorithm implementation."""

    def __init__(self) -> None:
        """Initialize the grid layout algorithm."""
        self._lock = RLock()

    def calculate(self, component: Component, container_bounds: Bounds, backend_target: BackendTarget) -> LayoutResult:
        """Calculate CSS Grid layout for a component.

        Implements proper CSS Grid layout algorithm with support for
        grid-template-columns, grid-template-rows, grid-column-gap,
        and grid-row-gap.

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
                logger.debug(f"Calculating grid layout for node with renderer: {backend_target}")

                # Convert bounds to renderer units if needed
                if hasattr(container_bounds, "to_backend_units"):
                     bounds = container_bounds.to_backend_units(backend_target)
                else:
                     bounds = container_bounds

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

                # Calculate inner dimensions
                inner_width = available_width - padding_left - padding_right - margin_left - margin_right
                inner_height = available_height - padding_top - padding_bottom - margin_top - margin_bottom

                if inner_width < 0:
                    inner_width = 0
                if inner_height < 0:
                    inner_height = 0

                # Parse grid templates
                columns = self.parse_grid_template(style.grid_template_columns or "auto")
                rows = self.parse_grid_template(style.grid_template_rows or "auto")

                # Calculate track sizes
                column_sizes = self.calculate_track_sizes(columns, inner_width, style.grid_column_gap or 0)
                row_sizes = self.calculate_track_sizes(rows, inner_height, style.grid_row_gap or 0)

                # Determine grid dimensions
                num_columns = len(column_sizes) if column_sizes else 1
                num_rows = len(row_sizes) if row_sizes else (len(node.children) + num_columns - 1) // num_columns

                # Ensure we have enough tracks
                while len(column_sizes) < num_columns:
                    column_sizes.append(inner_width // num_columns if inner_width > 0 else 0)
                while len(row_sizes) < num_rows:
                    row_sizes.append(inner_height // num_rows if inner_height > 0 else 0)

                # Position children in grid
                child_index = 0
                y_offset = padding_top + margin_top

                for row_idx in range(num_rows):
                    x_offset = padding_left + margin_left
                    row_height = row_sizes[row_idx] if row_idx < len(row_sizes) else 0

                    for col_idx in range(num_columns):
                        col_width = column_sizes[col_idx] if col_idx < len(column_sizes) else 0

                        if child_index < len(node.children):
                            child = node.children[child_index]
                            if child.style.display != "none":
                                # Calculate child layout within grid cell
                                self.calculate_child_in_grid_cell(child, col_width, row_height)
                                child.layout.x = x_offset
                                child.layout.y = y_offset
                                child.layout.width = col_width
                                child.layout.height = row_height
                            child_index += 1

                        x_offset += col_width + (style.grid_column_gap or 0)
                        child_index += 1

                    y_offset += row_height + (style.grid_row_gap or 0)

                # Calculate container dimensions
                total_width = sum(column_sizes) + (len(column_sizes) - 1) * (style.grid_column_gap or 0)
                total_height = sum(row_sizes) + (len(row_sizes) - 1) * (style.grid_row_gap or 0)

                container_width = total_width + padding_left + padding_right
                container_height = total_height + padding_top + padding_bottom

                # Apply min/max constraints
                container_width = max(style.min_width or 0, min(style.max_width or container_width, container_width))
                container_height = max(style.min_height or 0, min(style.max_height or container_height, container_height))

                result = LayoutResult(x=margin_left, y=margin_top, width=container_width + margin_left + margin_right, height=container_height + margin_top + margin_bottom)

                # Update node layout
                node.layout = result
                return result

            except Exception as e:
                logger.error(f"Grid layout calculation failed: {e}")
                raise LayoutCalculationError(f"Failed to calculate grid layout: {e}") from e

    def parse_grid_template(self, template: str) -> list[str]:
        """Parse CSS grid-template string into track definitions."""
        if not template or template == "auto":
            return []

        tracks: list[str] = []
        i = 0
        while i < len(template):
            if template[i : i + 7] == "repeat(":
                # Parse repeat(count, pattern)
                end = template.find(")", i)
                if end != -1:
                    repeat_content = template[i + 7 : end]
                    parts = [p.strip() for p in repeat_content.split(",")]
                    if len(parts) == 2:
                        try:
                            count = int(parts[0])
                            pattern = parts[1]
                            # Expand repeat
                            for _ in range(count):
                                tracks.append(pattern)
                        except ValueError:
                            pass
                    i = end + 1
                else:
                    break
            else:
                # Find next space or end
                j = i
                while j < len(template) and template[j] != " ":
                    j += 1
                if j > i:
                    tracks.append(template[i:j])
                i = j + 1
        return tracks

    def calculate_track_sizes(self, tracks: list[str], available_size: int, gap: int) -> list[int]:
        """Calculate sizes for grid tracks."""
        if not tracks:
            return []

        sizes: list[int] = []
        remaining_size = available_size - gap * (len(tracks) - 1)
        fr_units = 0

        # First pass: handle fixed sizes and count fr units
        for track in tracks:
            track = track.strip()
            if track.endswith("px"):
                try:
                    size = int(track[:-2])
                    sizes.append(size)
                    remaining_size -= size
                except ValueError:
                    sizes.append(0)
            elif track.endswith("fr"):
                try:
                    fr_value = float(track[:-2])
                    fr_units += fr_value
                    sizes.append(0)  # Placeholder
                except ValueError:
                    sizes.append(0)
            else:
                # Default to equal distribution
                sizes.append(0)
                fr_units += 1

        # Second pass: distribute remaining space to fr units
        if fr_units > 0 and remaining_size > 0:
            fr_size = int(remaining_size // fr_units)
            for i, track in enumerate(tracks):
                if track.endswith("fr"):
                    sizes[i] = fr_size

        return sizes

    def calculate_child_in_grid_cell(self, child: LayoutNode, cell_width: int, cell_height: int) -> LayoutResult:
        """Calculate layout for a child within a grid cell."""
        # Use recursive calculation for proper layout resolution
        from ornata.layout.engine.engine import compute_layout
        return compute_layout(child, cell_width, cell_height)
