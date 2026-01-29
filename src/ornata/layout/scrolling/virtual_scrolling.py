"""Virtual scrolling implementation for efficient rendering of large datasets."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from ornata.definitions.dataclasses.layout import VirtualScrollState
from ornata.layout.engine.engine import LayoutNode

if TYPE_CHECKING:
    from ornata.definitions.dataclasses.layout import LayoutStyle, VirtualScrollConfig

# Type hints
ItemRenderer = Callable[[Any, int], LayoutNode]
ItemMeasurer = Callable[[Any], tuple[int, int]]


class VirtualScrollContainer:
    """Container that efficiently renders large lists using virtual scrolling."""

    def __init__(
        self,
        config: VirtualScrollConfig,
        item_renderer: ItemRenderer,
        item_measurer: ItemMeasurer | None = None,
    ):
        self.config = config
        self.item_renderer = item_renderer
        self.item_measurer = item_measurer
        self.state = VirtualScrollState()

        # Performance optimization: pre-allocate height cache if we know total items
        if config.total_items > 0 and config.item_height is None:
            self.state.item_heights = [0] * config.total_items

    def update_config(self, **updates: Any) -> None:
        """Update configuration and recalculate visible range."""
        for key, value in updates.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

        # Invalidate cached heights if total_items changed
        if "total_items" in updates and self.config.item_height is None:
            old_total = len(self.state.item_heights)
            new_total = self.config.total_items
            if new_total > old_total:
                self.state.item_heights.extend([0] * (new_total - old_total))
            elif new_total < old_total:
                self.state.item_heights = self.state.item_heights[:new_total]

        self._update_visible_range()

    def scroll_to(self, item_index: int) -> None:
        """Scroll to make the specified item visible."""
        self.config.scroll_offset = max(0, min(item_index, max(0, self.config.total_items - 1)))
        self._update_visible_range()

    def scroll_by(self, delta: int) -> None:
        """Scroll by the specified number of items."""
        self.scroll_to(self.config.scroll_offset + delta)

    def get_visible_range(self) -> tuple[int, int]:
        """Get the range of currently visible items."""
        return (self.state.visible_start, self.state.visible_end)

    def get_rendered_nodes(self) -> list[LayoutNode]:
        """Get the nodes that should be rendered for the current viewport."""
        return [node for _, node in self.state.rendered_items]

    def _update_visible_range(self) -> None:
        """Calculate which items should be visible based on current scroll position."""
        if self.config.total_items == 0:
            self.state.visible_start = 0
            self.state.visible_end = 0
            self.state.rendered_items = []
            return

        # Calculate visible range with overscan
        start = max(0, self.config.scroll_offset - self.config.overscan)
        end = min(self.config.total_items, self.config.scroll_offset + self._calculate_visible_count() + self.config.overscan)

        self.state.visible_start = start
        self.state.visible_end = end

        # Update rendered items
        self._update_rendered_items()

    def _calculate_visible_count(self) -> int:
        """Calculate how many items fit in the viewport."""
        if self.config.item_height and self.config.item_height > 0:
            # Fixed height items
            return max(1, self.config.viewport_height // self.config.item_height)
        else:
            # Variable height - estimate based on average height
            if self.state.item_heights:
                measured_heights = [h for h in self.state.item_heights if h > 0]
                if measured_heights:
                    avg_height = sum(measured_heights) / len(measured_heights)
                    return max(1, int(self.config.viewport_height / avg_height))
            # Fallback estimate
            return max(1, self.config.viewport_height // 2)

    def _update_rendered_items(self) -> None:
        """Update the list of rendered items for the current visible range."""
        new_items: list[tuple[int, LayoutNode]] = []

        for i in range(self.state.visible_start, self.state.visible_end):
            # Check if we already have this item rendered
            existing = next((node for idx, node in self.state.rendered_items if idx == i), None)

            if existing is not None:
                new_items.append((i, existing))
            else:
                # Render new item
                try:
                    item_node = self.item_renderer(None, i)  # Pass None as data, let renderer handle indexing
                    new_items.append((i, item_node))

                    # Cache height for variable-height items
                    if self.config.item_height is None and i < len(self.state.item_heights):
                        # Estimate height from rendered node
                        height = getattr(item_node.layout, "height", 1)
                        self.state.item_heights[i] = height

                except Exception:
                    # Skip items that fail to render
                    continue

        self.state.rendered_items = new_items

    def get_total_height(self) -> int:
        """Get the total height of all items."""
        if self.config.item_height:
            return self.config.total_items * self.config.item_height
        else:
            # Sum cached heights
            return sum(h for h in self.state.item_heights if h > 0)

    def get_scroll_position(self) -> float:
        """Get scroll position as a fraction (0.0 to 1.0)."""
        if self.config.total_items <= self._calculate_visible_count():
            return 0.0

        max_scroll = max(0, self.config.total_items - self._calculate_visible_count())
        if max_scroll == 0:
            return 0.0

        return self.config.scroll_offset / max_scroll

    def set_scroll_position(self, fraction: float) -> None:
        """Set scroll position from a fraction (0.0 to 1.0)."""
        if self.config.total_items <= self._calculate_visible_count():
            self.scroll_to(0)
            return

        max_scroll = max(0, self.config.total_items - self._calculate_visible_count())
        target_offset = int(fraction * max_scroll)
        self.scroll_to(target_offset)

    def get_scroll_offset_height(self) -> int:
        """Get the height offset for scrolling in variable-height mode."""
        if self.config.item_height:
            return self.config.scroll_offset * self.config.item_height
        else:
            # Calculate cumulative height up to scroll offset
            height = 0
            for i in range(min(self.config.scroll_offset, len(self.state.item_heights))):
                height += self.state.item_heights[i]
            return height


def create_virtual_scroll_node(container: VirtualScrollContainer, style: LayoutStyle | None = None) -> LayoutNode:
    """Create a LayoutNode that represents the virtual scroll container."""
    from ornata.definitions.dataclasses.layout import LayoutStyle
    from ornata.layout.engine.engine import LayoutNode

    if style is None:
        style = LayoutStyle()

    # Set container dimensions
    style.width = container.config.viewport_width
    style.height = container.config.viewport_height

    # Create container node
    container_node = LayoutNode(style=style)

    # Add visible child nodes
    for item_index, item_node in container.state.rendered_items:
        # Position the item relative to the scroll offset
        if container.config.item_height:
            # Fixed height positioning
            item_node.layout.y = (item_index - container.config.scroll_offset) * container.config.item_height
        else:
            # Variable height - calculate cumulative height
            y_offset = 0
            for i in range(item_index):
                if i < len(container.state.item_heights):
                    y_offset += container.state.item_heights[i]
            item_node.layout.y = y_offset - container.get_scroll_offset_height()

        item_node.layout.x = 0  # Items fill the full width
        container_node.add(item_node)

    return container_node


def create_simple_item_renderer(items: list[Any], render_func: Callable[[Any], str] | None = None) -> ItemRenderer:
    """Create a simple item renderer for a list of items."""

    def renderer(data: Any, index: int) -> LayoutNode:
        from ornata.definitions.dataclasses.layout import LayoutStyle
        from ornata.layout.engine.engine import LayoutNode

        if index >= len(items):
            # Return empty node for out-of-bounds
            return LayoutNode(style=LayoutStyle(width=1, height=1))

        item = items[index]
        text = str(item) if render_func is None else render_func(item)

        # Create a text node
        style = LayoutStyle(width=80, height=1)  # Will be overridden by measurement
        node = LayoutNode(style=style, measure=lambda w, h: (len(text), 1))

        return node

    return renderer