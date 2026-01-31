"""Cell-based terminal renderer for CLI output.

This module provides the concrete CLI renderer using Rich-inspired cell-based
rendering. Every cell is fully specified - no terminal state is trusted.
"""

from __future__ import annotations

from threading import RLock
from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger
from ornata.rendering.core.base_renderer import Renderer

if TYPE_CHECKING:
    from ornata.api.exports.definitions import BackendTarget, GuiNode, LayoutResult, RenderOutput
    from ornata.definitions.dataclasses.styling import ANSIColor

logger = get_logger(__name__)


class TerminalRenderer(Renderer):
    """Cell-based terminal renderer for text UIs.

    This renderer implements the Rich-inspired model where every cell is fully
    specified with character, foreground, background, and attributes. No
    terminal state is trusted - complete style codes are emitted for each cell.

    Parameters
    ----------
    backend_target : BackendTarget
        The target backend (should be CLI).
    default_bg : ANSIColor | None
        Default background color for the terminal.
    use_truecolor : bool
        Use 24-bit RGB colors instead of 256-color palette.

    Attributes
    ----------
    _lock : RLock
        Thread lock for renderer access.
    _cell_buffer : CellBuffer | None
        The current cell buffer being rendered.
    _min_width : int
        Minimum terminal width.
    _min_height : int
        Minimum terminal height.
    _max_width : int
        Maximum terminal width.
    _max_height : int
        Maximum terminal height.
    """

    def __init__(
        self,
        backend_target: BackendTarget,
        *,
        default_bg: ANSIColor | None = None,
        use_truecolor: bool = True,
    ) -> None:
        super().__init__(backend_target)
        self._lock = RLock()
        self._cell_buffer: Any | None = None
        self._min_width = 60
        self._min_height = 20
        self._max_width = 200
        self._max_height = 80
        self._default_bg = default_bg
        self._use_truecolor = use_truecolor
        self._ansi_renderer: Any | None = None

    def render_tree(self, tree: Any, layout_result: Any) -> RenderOutput:
        """Render a tree into a cell-based buffer and convert to ANSI.

        Parameters
        ----------
        tree : Any
            VDOM-like tree or GuiNode hierarchy.
        layout_result : Any
            Precomputed layout information.

        Returns
        -------
        RenderOutput
            ANSI-encoded text content and metadata.
        """
        from ornata.api.exports.definitions import RenderOutput
        from ornata.rendering.backends.cli.ansi_renderer import ANSIRenderer
        from ornata.rendering.backends.cli.cells import CellBuffer
        from ornata.rendering.backends.cli.rasterizer import NodeRasterizer

        with self._lock:
            try:
                # Determine canvas size from layout or use defaults
                layout_width = max(1, int(getattr(layout_result, "width", 0) or self._min_width))
                layout_height = max(1, int(getattr(layout_result, "height", 0) or self._min_height))

                canvas_width = min(self._max_width, max(layout_width, self._min_width))
                canvas_height = min(self._max_height, max(layout_height, self._min_height))

                # Get the root node
                root = getattr(tree, "root", tree)

                # Handle simple string/bytes content
                if isinstance(root, (str, bytes)):
                    content = root.decode("utf-8", errors="replace") if isinstance(root, bytes) else root
                    output = RenderOutput(content=content, backend_target=self.backend_target, metadata={})
                    return self._set_last_output(output)

                # Check if it's a GuiNode hierarchy
                if self._is_gui_node(root):
                    # Create rasterizer and generate cell buffer
                    rasterizer = NodeRasterizer(
                        width=canvas_width,
                        height=canvas_height,
                        default_bg=self._default_bg,
                    )
                    self._cell_buffer = rasterizer.rasterize(root)

                    # Render to ANSI
                    ansi_renderer = ANSIRenderer(use_truecolor=self._use_truecolor)
                    ansi_output = ansi_renderer.render(self._cell_buffer)

                    output = RenderOutput(
                        content=ansi_output.text,
                        backend_target=self.backend_target,
                        metadata={
                            "canvas_size": (canvas_width, canvas_height),
                            "has_colors": ansi_output.has_colors,
                        },
                    )
                    return self._set_last_output(output)

                # Fallback for other tree types
                fallback = self._render_fallback(root, (0, 0, canvas_width, canvas_height))
                output = RenderOutput(content=fallback, backend_target=self.backend_target, metadata={})
                return self._set_last_output(output)

            except Exception as exc:
                logger.error(f"Terminal render failed: {exc}")
                from ornata.api.exports.definitions import RenderingError
                raise RenderingError(str(exc)) from exc

    def apply_patches(self, patches: list[Any]) -> None:
        """Apply patches by invalidating buffer for now.

        In the future, this will support incremental cell updates for dirty regions.

        Parameters
        ----------
        patches : list[Any]
            VDOM patches to apply.
        """
        with self._lock:
            # For now, invalidate the buffer - next render_tree will rebuild
            # Future: implement incremental updates based on patch regions
            logger.debug(f"Received {len(patches)} patches, invalidating buffer")
            self._cell_buffer = None

    def _is_gui_node(self, node: Any) -> bool:
        """Check if node is a GuiNode."""
        return hasattr(node, "component_name") and hasattr(node, "children")

    def _render_fallback(self, node: Any, bounds: tuple[int, int, int, int]) -> str:
        """Fallback renderer for non-GuiNode trees."""
        from ornata.rendering.backends.cli.ansi_renderer import ANSIRenderer
        from ornata.rendering.backends.cli.cells import CellBuffer, Segment
        from ornata.definitions.dataclasses.styling import ANSIColor

        x, y, width, height = bounds

        # Create a simple cell buffer
        buffer = CellBuffer(width, height, default_bg=self._default_bg)
        buffer.clear(self._default_bg)

        # Extract text content
        text = self._extract_text(node)
        if text:
            # Write text to buffer
            lines = text.splitlines()[:height]
            for row_idx, line in enumerate(lines):
                segment = Segment(text=line[:width])
                buffer.write_segment(x, y + row_idx, segment)

        # Render to ANSI
        renderer = ANSIRenderer(use_truecolor=self._use_truecolor)
        return renderer.render(buffer).text

    def _extract_text(self, node: Any) -> str:
        """Extract text from a node."""
        if node is None:
            return ""

        # Direct text
        if isinstance(node, str):
            return node

        # Props content
        props = getattr(node, "props", None)
        if isinstance(props, dict):
            content = props.get("content")
            if content:
                return str(content)

        # Component name as placeholder
        comp_name = getattr(node, "component_name", None)
        if comp_name:
            return f"[{comp_name}]"

        # Recurse children
        parts = []
        for child in getattr(node, "children", []) or []:
            parts.append(self._extract_text(child))
        return "\n".join(parts) if parts else ""

    def get_buffer(self) -> Any | None:
        """Get the current cell buffer (for debugging/testing)."""
        with self._lock:
            return self._cell_buffer

    def clear_buffer(self) -> None:
        """Clear the current cell buffer."""
        with self._lock:
            self._cell_buffer = None


__all__ = ["TerminalRenderer"]
