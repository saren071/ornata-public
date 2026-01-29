"""Flexbox layout algorithm implementation."""

from __future__ import annotations

import logging
from threading import RLock
from typing import TYPE_CHECKING

from ornata.definitions.dataclasses.layout import LayoutResult
from ornata.definitions.errors import LayoutCalculationError
from ornata.definitions.protocols import LayoutAlgorithm
from ornata.layout.engine.engine import LayoutNode, component_to_layout_node

if TYPE_CHECKING:
    from ornata.api.exports.definitions import BackendTarget, Bounds
    from ornata.definitions.dataclasses.components import Component

logger = logging.getLogger(__name__)


class FlexLayout(LayoutAlgorithm):
    """Flexbox layout algorithm implementation."""

    def __init__(self) -> None:
        """Initialize the flex layout algorithm."""
        self._lock = RLock()

    def calculate(self, component: "Component", container_bounds: Bounds, backend_target: BackendTarget) -> LayoutResult:
        """Calculate flex layout for a component.

        Implements proper flexbox layout algorithm with support for flex-grow,
        flex-shrink, justify-content, align-items, and wrapping.

        Args:
            component: The renderable component to calculate.
            container_bounds: The bounds of the container.
            renderer_type: The target renderer type.

        Returns:
            The calculated layout result.

        Raises:
            LayoutCalculationError: If layout calculation fails.
        """
        with self._lock:
            try:
                logger.debug(f"Calculating flex layout for node with backend: {backend_target}")

                node = component_to_layout_node(component)

                if hasattr(container_bounds, "to_backend_units"):
                     bounds = container_bounds.to_backend_units(backend_target)
                else:
                     bounds = container_bounds

                available_width = int(bounds.width)
                available_height = int(bounds.height)

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

                # Handle leaf nodes
                if not node.children:
                    return self.calculate_leaf_layout(
                        node, inner_width, inner_height, padding_left, padding_right,
                        padding_top, padding_bottom, margin_left, margin_right, margin_top, margin_bottom
                    )

                # Calculate child layouts
                child_layouts: list[LayoutResult] = []
                total_main_size = 0
                total_cross_size = 0
                flex_grow_total = 0.0
                flex_shrink_total = 0.0

                is_row = style.direction == "row"

                for child in node.children:
                    if child.style.display == "none":
                        continue

                    child_result = self.calculate_child_layout(child, inner_width if is_row else inner_width, inner_height if not is_row else inner_height)
                    child_layouts.append(child_result)

                    main_size = child_result.width if is_row else child_result.height
                    cross_size = child_result.height if is_row else child_result.width

                    total_main_size += main_size
                    total_cross_size = max(total_cross_size, cross_size)

                    flex_grow_total += max(0.0, child.style.flex_grow)
                    flex_shrink_total += max(0.0, child.style.flex_shrink)

                # Add gaps
                gaps = style.gap * (len(child_layouts) - 1) if child_layouts else 0
                total_main_size += gaps

                # Apply flex-grow and flex-shrink
                if flex_grow_total > 0 and total_main_size < inner_width:
                    extra_space = inner_width - total_main_size
                    for i, _ in enumerate(child_layouts):
                        grow = max(0.0, node.children[i].style.flex_grow)
                        if grow > 0:
                            delta = int(extra_space * (grow / flex_grow_total))
                            if is_row:
                                child_layouts[i] = self.calculate_child_layout(node.children[i], child_layouts[i].width + delta, inner_height)
                            else:
                                child_layouts[i] = self.calculate_child_layout(node.children[i], inner_width, child_layouts[i].height + delta)

                elif flex_shrink_total > 0 and total_main_size > inner_width:
                    deficit = total_main_size - inner_width
                    for i, _ in enumerate(child_layouts):
                        shrink = max(0.0, node.children[i].style.flex_shrink)
                        if shrink > 0:
                            reduce_amount = int(deficit * (shrink / flex_shrink_total))
                            if is_row:
                                child_layouts[i] = self.calculate_child_layout(node.children[i], max(0, child_layouts[i].width - reduce_amount), inner_height)
                            else:
                                child_layouts[i] = self.calculate_child_layout(node.children[i], inner_width, max(0, child_layouts[i].height - reduce_amount))

                # Handle wrapping if enabled
                if style.wrap and is_row and child_layouts:
                    child_layouts, total_main_size, total_cross_size = self.handle_row_wrapping(child_layouts, inner_width, style.gap, style.align)

                elif style.wrap and not is_row and child_layouts:
                    child_layouts, total_main_size, total_cross_size = self.handle_column_wrapping(child_layouts, inner_height, style.gap, style.align)

                # Position children
                self.position_children(node, child_layouts, inner_width, inner_height, padding_left, padding_top, style.justify, style.align, is_row)

                # Calculate final dimensions
                container_width = inner_width + padding_left + padding_right
                container_height = total_cross_size + padding_top + padding_bottom

                # Apply min/max constraints
                container_width = max(style.min_width or 0, min(style.max_width or container_width, container_width))
                container_height = max(style.min_height or 0, min(style.max_height or container_height, container_height))

                result = LayoutResult(x=margin_left, y=margin_top, width=container_width + margin_left + margin_right, height=container_height + margin_top + margin_bottom)

                # Update node layout
                node.layout = result
                return result

            except Exception as e:
                logger.error(f"Flex layout calculation failed: {e}")
                raise LayoutCalculationError(f"Failed to calculate flex layout: {e}") from e

    def calculate_leaf_layout(
        self,
        component: LayoutNode,
        inner_width: int | None,
        inner_height: int | None,
        padding_left: int,
        padding_right: int,
        padding_top: int,
        padding_bottom: int,
        margin_left: int,
        margin_right: int,
        margin_top: int,
        margin_bottom: int,
    ) -> LayoutResult:
        """Calculate layout for a leaf node."""
        style = component.style

        # Use explicit dimensions or measure content
        width = style.width if style.width is not None else (style.flex_basis if style.flex_basis is not None else 0)
        height = style.height if style.height is not None else 0

        if component.measure is not None:
            measured_width, measured_height = component.measure(inner_width, inner_height)
            if style.width is None:
                width = measured_width
            if style.height is None:
                height = measured_height

        # Apply constraints
        width = max(style.min_width or 0, min(style.max_width or width, width))
        height = max(style.min_height or 0, min(style.max_height or height, height))

        content_width = width + padding_left + padding_right
        content_height = height + padding_top + padding_bottom

        return LayoutResult(x=margin_left, y=margin_top, width=content_width + margin_left + margin_right, height=content_height + margin_top + margin_bottom)

    def calculate_child_layout(self, child: LayoutNode, available_width: int | None, available_height: int | None) -> LayoutResult:
        """Calculate layout for a child node."""
        # Use recursive calculation for proper layout resolution
        from ornata.layout.engine.engine import compute_layout
        return compute_layout(child, available_width, available_height)

    def handle_row_wrapping(self, child_layouts: list[LayoutResult], inner_width: int | None, gap: int, align: str) -> tuple[list[LayoutResult], int, int]:
        """Handle row wrapping for flex layout."""
        if inner_width is None or not child_layouts:
            return child_layouts, sum(layout.width for layout in child_layouts) + gap * (len(child_layouts) - 1), max((layout.height for layout in child_layouts), default=0)

        lines: list[list[LayoutResult]] = []
        current_line = []
        current_width = 0
        max_height = 0

        for layout in child_layouts:
            if current_line and current_width + layout.width + gap > inner_width:
                lines.append(current_line)
                current_line = [layout]
                current_width = layout.width
                max_height = max(max_height, max(line.height for line in current_line))
            else:
                if current_line:
                    current_width += gap
                current_line.append(layout)
                current_width += layout.width

        if current_line:
            lines.append(current_line)
            max_height = max(max_height, max(line.height for line in current_line))

        # Update layout positions for wrapping
        y_offset = 0
        for line in lines:
            line_width = sum(layout.width for layout in line) + gap * (len(line) - 1)
            remaining_space = max(0, inner_width - line_width)
            x_offset = 0

            # Apply alignment
            if align == "center":
                x_offset = remaining_space // 2
            elif align == "end":
                x_offset = remaining_space

            for layout in line:
                layout.x = x_offset
                layout.y = y_offset
                x_offset += layout.width + gap

            y_offset += max(layout.height for layout in line) + gap

        total_width = inner_width
        total_height = y_offset - gap if lines else 0

        return child_layouts, total_width, total_height

    def handle_column_wrapping(self, child_layouts: list[LayoutResult], inner_height: int | None, gap: int, align: str) -> tuple[list[LayoutResult], int, int]:
        """Handle column wrapping for flex layout."""
        if inner_height is None or not child_layouts:
            return child_layouts, max((layout.width for layout in child_layouts), default=0), sum(layout.height for layout in child_layouts) + gap * (len(child_layouts) - 1)

        columns: list[list[LayoutResult]] = []
        current_column = []
        current_height = 0
        max_width = 0

        for layout in child_layouts:
            if current_column and current_height + layout.height + gap > inner_height:
                columns.append(current_column)
                current_column = [layout]
                current_height = layout.height
                max_width = max(max_width, max(layout.width for layout in current_column))
            else:
                if current_column:
                    current_height += gap
                current_column.append(layout)
                current_height += layout.height

        if current_column:
            columns.append(current_column)
            max_width = max(max_width, max(layout.width for layout in current_column))

        # Update layout positions for wrapping
        x_offset = 0
        for column in columns:
            column_height = sum(layout.height for layout in column) + gap * (len(column) - 1)
            remaining_space = max(0, inner_height - column_height)
            y_offset = 0

            # Apply alignment
            if align == "center":
                y_offset = remaining_space // 2
            elif align == "end":
                y_offset = remaining_space

            for layout in column:
                layout.x = x_offset
                layout.y = y_offset
                y_offset += layout.height + gap

            x_offset += max(layout.width for layout in column) + gap

        total_height = inner_height
        total_width = x_offset - gap if columns else 0

        return child_layouts, total_width, total_height

    def position_children(
        self, component: LayoutNode, child_layouts: list[LayoutResult], inner_width: int | None, inner_height: int | None, padding_left: int, padding_top: int, justify: str, align: str, is_row: bool
    ) -> None:
        """Position children within the container."""
        if not child_layouts:
            return

        if is_row:
            total_width = sum(layout.width for layout in child_layouts) + component.style.gap * (len(child_layouts) - 1)
            remaining_space = max(0, (inner_width or total_width) - total_width)

            # Calculate main axis positioning
            if justify == "center":
                main_offset = remaining_space // 2
            elif justify == "end":
                main_offset = remaining_space
            elif justify == "space-between" and len(child_layouts) > 1:
                gap_extra = remaining_space // (len(child_layouts) - 1)
                # Update gap in child positioning
                component.style.gap += gap_extra
                main_offset = 0
            elif justify == "space-around" and child_layouts:
                gap_extra = remaining_space // len(child_layouts)
                component.style.gap += gap_extra
                main_offset = gap_extra // 2
            elif justify == "space-evenly" and child_layouts:
                gap_extra = remaining_space // (len(child_layouts) + 1)
                component.style.gap += gap_extra
                main_offset = gap_extra
            else:
                main_offset = 0

            x_cursor = padding_left + main_offset
            for i, layout in enumerate(child_layouts):
                child = component.children[i]
                child_margin_top = child.style.margin_top if child.style.margin_top is not None else child.style.margin
                child_margin_bottom = child.style.margin_bottom if child.style.margin_bottom is not None else child.style.margin

                layout.x = x_cursor + (child.style.margin_left if child.style.margin_left is not None else child.style.margin)

                # Cross axis alignment
                cross_space = (inner_height or layout.height) - layout.height
                if align == "center":
                    layout.y = padding_top + child_margin_top + cross_space // 2
                elif align == "end":
                    layout.y = padding_top + child_margin_top + cross_space
                elif align == "stretch":
                    layout.y = padding_top + child_margin_top
                    layout.height = (inner_height or layout.height) - child_margin_top - child_margin_bottom
                else:
                    layout.y = padding_top + child_margin_top

                x_cursor += layout.width + component.style.gap
        else:
            # Column direction
            total_height = sum(layout.height for layout in child_layouts) + component.style.gap * (len(child_layouts) - 1)
            remaining_space = max(0, (inner_height or total_height) - total_height)

            # Calculate main axis positioning
            if justify == "center":
                main_offset = remaining_space // 2
            elif justify == "end":
                main_offset = remaining_space
            elif justify == "space-between" and len(child_layouts) > 1:
                gap_extra = remaining_space // (len(child_layouts) - 1)
                component.style.gap += gap_extra
                main_offset = 0
            elif justify == "space-around" and child_layouts:
                gap_extra = remaining_space // len(child_layouts)
                component.style.gap += gap_extra
                main_offset = gap_extra // 2
            elif justify == "space-evenly" and child_layouts:
                gap_extra = remaining_space // (len(child_layouts) + 1)
                component.style.gap += gap_extra
                main_offset = gap_extra
            else:
                main_offset = 0

            y_cursor = padding_top + main_offset
            for i, layout in enumerate(child_layouts):
                child = component.children[i]
                child_margin_left = child.style.margin_left if child.style.margin_left is not None else child.style.margin
                child_margin_right = child.style.margin_right if child.style.margin_right is not None else child.style.margin

                layout.y = y_cursor + (child.style.margin_top if child.style.margin_top is not None else child.style.margin)

                # Cross axis alignment
                cross_space = (inner_width or layout.width) - layout.width
                if align == "center":
                    layout.x = padding_left + child_margin_left + cross_space // 2
                elif align == "end":
                    layout.x = padding_left + child_margin_left + cross_space
                elif align == "stretch":
                    layout.x = padding_left + child_margin_left
                    layout.width = (inner_width or layout.width) - child_margin_left - child_margin_right
                else:
                    layout.x = padding_left + child_margin_left

                y_cursor += layout.height + component.style.gap
