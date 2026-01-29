"""Layout debugging and visualization tools."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ornata.definitions.dataclasses.layout import LayoutDebugInfo

if TYPE_CHECKING:
    from ornata.layout.engine.engine import LayoutNode, LayoutResult


class LayoutDebugger:
    """Debug and visualize layout computations."""

    def __init__(self):
        self._debug_info: list[LayoutDebugInfo] = []
        self._enabled = False

    def enable(self) -> None:
        """Enable layout debugging."""
        self._enabled = True

    def disable(self) -> None:
        """Disable layout debugging."""
        self._enabled = False

    def clear(self) -> None:
        """Clear debug information."""
        self._debug_info.clear()

    def record_layout(self, node: LayoutNode, result: LayoutResult, cache_hit: bool = False, computation_time: float = 0.0) -> None:
        """Record layout computation information."""
        if not self._enabled:
            return

        depth = self._calculate_depth(node)
        child_count = len([c for c in node.children if c.style.display != "none"])

        info = LayoutDebugInfo(
            node=node,
            result=result,
            cache_hit=cache_hit,
            computation_time=computation_time,
            child_count=child_count,
            depth=depth,
        )
        self._debug_info.append(info)

    def _calculate_depth(self, node: LayoutNode) -> int:
        """Calculate the depth of a node in the layout tree."""
        # This is a simplified calculation - in practice you'd need to track parent relationships
        return 0

    def get_performance_stats(self) -> dict[str, float]:
        """Get performance statistics from debug info."""
        if not self._debug_info:
            return {}

        total_time = sum(info.computation_time for info in self._debug_info)
        cache_hits = sum(1 for info in self._debug_info if info.cache_hit)
        total_computations = len(self._debug_info)

        return {
            "total_computation_time": total_time,
            "average_computation_time": total_time / total_computations if total_computations > 0 else 0,
            "cache_hit_rate": cache_hits / total_computations if total_computations > 0 else 0,
            "total_layouts_computed": total_computations,
        }

    def visualize_layout_tree(self, root: LayoutNode) -> str:
        """Generate a text visualization of the layout tree."""
        lines: list[str] = []
        self._visualize_node(root, lines, 0)
        return "\n".join(lines)

    def _visualize_node(self, node: LayoutNode, lines: list[str], indent: int) -> None:
        """Recursively visualize a layout node."""
        prefix = "  " * indent
        layout = node.layout
        style = node.style

        # Node info
        node_info = f"{prefix}Node: {layout.width}x{layout.height} at ({layout.x},{layout.y})"
        if style.display and style.display != "block":
            node_info += f" [{style.display}]"
        if style.position and style.position != "static":
            node_info += f" pos:{style.position}"

        lines.append(node_info)

        # Style info
        style_parts: list[str] = []
        if style.direction:
            style_parts.append(f"dir:{style.direction}")
        if style.wrap:
            style_parts.append("wrap")
        if style.justify and style.justify != "start":
            style_parts.append(f"justify:{style.justify}")
        if style.align and style.align != "stretch":
            style_parts.append(f"align:{style.align}")

        if style_parts:
            lines.append(f"{prefix}  Style: {' '.join(style_parts)}")

        # Children
        visible_children = [c for c in node.children if c.style.display != "none"]
        if visible_children:
            lines.append(f"{prefix}  Children ({len(visible_children)}):")
            for child in visible_children:
                self._visualize_node(child, lines, indent + 1)
        else:
            lines.append(f"{prefix}  (leaf node)")


# Global debugger instance
_layout_debugger = LayoutDebugger()


def get_layout_debugger() -> LayoutDebugger:
    """Get the global layout debugger instance."""
    return _layout_debugger
