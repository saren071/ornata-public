"""Terminal renderer for CLI output.

This module hosts the concrete CLI renderer under the new
`ornata.rendering` hierarchy.
"""

from __future__ import annotations

from threading import RLock
from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger
from ornata.rendering.core.base_renderer import Renderer

if TYPE_CHECKING:
    from ornata.api.exports.definitions import BackendTarget, GuiNode, LayoutResult, RenderOutput, UnicodeCanvas

logger = get_logger(__name__)


class TerminalRenderer(Renderer):
    """Basic terminal renderer for text UIs."""

    def __init__(self, backend_target: BackendTarget) -> None:
        super().__init__(backend_target)
        self._lock = RLock()
        self._buffer: list[str] = []
        self._min_width = 60
        self._min_height = 20
        self._max_width = 200
        self._max_height = 80

    def render_tree(self, tree: Any, layout_result: Any) -> RenderOutput:
        """Render a tree into a plain-text buffer.

        Parameters
        ----------
        tree : Any
            VDOM-like tree whose nodes expose `props` and `children`.
        layout_result : Any
            Precomputed layout information (opaque here).

        Returns
        -------
        RenderOutput
            Text content and metadata.
        """
        from ornata.api.exports.definitions import RenderOutput
        with self._lock:
            try:
                self._buffer.clear()
                root = getattr(tree, "root", tree)
                if isinstance(root, (str, bytes)):
                    content = root.decode("utf-8", errors="replace") if isinstance(root, bytes) else root
                    output = RenderOutput(content=content, backend_target=self.backend_target, metadata={})
                    return self._set_last_output(output)

                if self._is_gui_node(root):
                    content = self._render_gui_snapshot(root, layout_result)
                    output = RenderOutput(
                        content=content,
                        backend_target=self.backend_target,
                        metadata={
                            "canvas_size": (
                                getattr(layout_result, "width", self._min_width),
                                getattr(layout_result, "height", self._min_height),
                            ),
                        },
                    )
                    return self._set_last_output(output)

                fallback = self._render_node(root, (0, 0, 80, 24))
                output = RenderOutput(content=fallback, backend_target=self.backend_target, metadata={})
                return self._set_last_output(output)
            except Exception as exc:
                logger.error(f"Terminal render failed: {exc}")
                from ornata.api.exports.definitions import RenderingError
                raise RenderingError(str(exc)) from exc

    def apply_patches(self, patches: list[Any]) -> None:
        """Apply patches by invalidating buffer.

        Parameters
        ----------
        patches : list[Any]
            Not used here yet; included for API parity.
        """
        _ = patches
        with self._lock:
            # Simplest behavior for now: clear buffer; next render_tree will rebuild
            self._buffer.clear()

    # -- internals ---------------------------------------------------------------
    def _is_gui_node(self, node: Any) -> bool:
        """Return ``True`` when ``node`` looks like a GuiNode snapshot."""

        return hasattr(node, "component_name") and hasattr(node, "children")

    def _render_gui_snapshot(self, root: GuiNode, layout_result: LayoutResult | Any) -> str:
        """Render a GuiNode hierarchy to a Unicode canvas."""
        from ornata.api.exports.definitions import UnicodeCanvas

        layout_width = max(1, int(getattr(layout_result, "width", 0) or self._min_width))
        layout_height = max(1, int(getattr(layout_result, "height", 0) or self._min_height))

        canvas_width = min(self._max_width, max(layout_width, self._min_width))
        canvas_height = min(self._max_height, max(layout_height, self._min_height))

        scale_x = canvas_width / layout_width if layout_width > canvas_width else 1.0
        scale_y = canvas_height / layout_height if layout_height > canvas_height else 1.0

        canvas = UnicodeCanvas(canvas_width, canvas_height)
        self._draw_gui_node(canvas, root, depth=0, scale_x=scale_x, scale_y=scale_y)
        return canvas.render()

    def _draw_gui_node(
        self,
        canvas: UnicodeCanvas,
        node: GuiNode,
        *,
        depth: int,
        scale_x: float,
        scale_y: float,
    ) -> None:
        """Draw ``node`` onto ``canvas`` and recurse into children."""

        if not getattr(node, "visible", True):
            return
        rect = self._scale_rect(node, scale_x, scale_y, canvas.width, canvas.height)
        if rect is None:
            return
        metadata = (getattr(node, "metadata", None) or {})
        border_width = 0.0
        border_from_style = getattr(getattr(node, "style", None), "border", None)
        if border_from_style is not None:
            border_width = max(border_width, getattr(border_from_style, "width", 0.0) or 0.0)
        metadata_border_width = metadata.get("border_width")
        if isinstance(metadata_border_width, (int, float)):
            border_width = max(border_width, float(metadata_border_width))
        emphasize_border = False
        if isinstance(metadata.get("border_emphasize"), bool):
            emphasize_border = metadata["border_emphasize"]
        elif border_width >= 2.0:
            emphasize_border = True
        if border_width > 0.0:
            canvas.draw_panel(rect, emphasize=emphasize_border)

        children = getattr(node, "children", []) or []
        if not children:
            self._render_leaf_content(canvas, node, rect)

        for child in children:
            self._draw_gui_node(canvas, child, depth=depth + 1, scale_x=scale_x, scale_y=scale_y)

    def _render_leaf_content(self, canvas: UnicodeCanvas, node: GuiNode, rect: tuple[int, int, int, int]) -> None:
        """Render textual content or table data within ``rect``."""

        inner = (
            rect[0] + 1,
            rect[1] + 1,
            max(1, rect[2] - 2),
            max(1, rect[3] - 2),
        )
        if inner[2] <= 0 or inner[3] <= 0:
            return

        columns, rows = self._node_table_data(node)
        if columns and rows:
            canvas.draw_table(inner, columns, rows)
            return

        text = self._node_body_text(node)
        if text:
            canvas.draw_text_block(inner, text)

    def _node_table_data(self, node: GuiNode) -> tuple[list[str], list[list[str]]]:
        """Return table rows/columns for ``node`` when available."""

        columns = [str(col) for col in getattr(node, "columns", []) or []]
        rows: list[list[str]] = []
        raw_rows = getattr(node, "rows", []) or []
        for raw_row in raw_rows:
            str_row = [str(value) for value in raw_row]
            rows.append(str_row)
        if columns and rows:
            return columns, rows
        return [], []

    def _node_label(self, node: GuiNode) -> str:
        """Compose a label showing the component and prominent text."""

        comp_name = getattr(node, "component_name", None) or "component"
        primary_text = self._content_text(node)
        if primary_text:
            label = f"{comp_name} · {primary_text}"
        else:
            label = comp_name
        if len(label) > 70:
            return f"{label[:67]}..."
        return label

    def _node_body_text(self, node: GuiNode) -> str | None:
        """Return descriptive text for ``node`` body content."""

        text = self._content_text(node)
        if text:
            return text
        placeholder = getattr(getattr(node, "content", None), "placeholder", None)
        if placeholder:
            return f"[{placeholder}]"
        placeholder_value = getattr(node, "placeholder_value", None)
        if placeholder_value:
            return f"[{placeholder_value}]"
        status = getattr(node, "status", None)
        if status:
            return status
        selection = getattr(node, "selection", None) or []
        if selection:
            return f"Selected: {', '.join(str(idx) for idx in selection[:4])}"
        return None

    def _content_text(self, node: GuiNode) -> str | None:
        """Extract the most relevant text snippet for ``node``."""

        candidates: list[str | None] = [getattr(node, "text", None)]
        content = getattr(node, "content", None)
        if content is not None:
            for attr in ("title", "subtitle", "body", "text", "caption"):
                candidates.append(getattr(content, attr, None))
        for candidate in candidates:
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        return None

    def _scale_rect(
        self,
        node: GuiNode,
        scale_x: float,
        scale_y: float,
        canvas_width: int,
        canvas_height: int,
    ) -> tuple[int, int, int, int] | None:
        """Scale layout bounds from pixels into canvas coordinates."""

        raw_width = max(1, int(getattr(node, "width", 0) or 1))
        raw_height = max(1, int(getattr(node, "height", 0) or 1))
        scaled_w = max(2, int(round(raw_width * scale_x)))
        scaled_h = max(2, int(round(raw_height * scale_y)))
        x = int(round(getattr(node, "x", 0) * scale_x))
        y = int(round(getattr(node, "y", 0) * scale_y))

        if x >= canvas_width or y >= canvas_height:
            return None
        scaled_w = min(scaled_w, canvas_width - x)
        scaled_h = min(scaled_h, canvas_height - y)
        if scaled_w <= 0 or scaled_h <= 0:
            return None
        return x, y, scaled_w, scaled_h

    def _render_node(self, node: Any, bounds: tuple[int, int, int, int]) -> str:
        """Recursively render a node to text.

        Parameters
        ----------
        node : Any
            Node expected to expose `props` and `children` like a VDOM node.
        bounds : tuple[int, int, int, int]
            Rendering bounds; currently unused placeholder.

        Returns
        -------
        str
            Concatenated textual content.
        """
        if node is None:
            return ""

        # Support GuiNode instances directly
        if hasattr(node, "component_name"):
            return self._render_gui_node(node, bounds, depth=0)

        text = ""
        props: dict[str, Any] | None = getattr(node, "props", None)
        if isinstance(props, dict):
            content = props.get("content")
            if content:
                text += str(content)
        for child in getattr(node, "children", []) or []:
            text += self._render_node(child, bounds)
        return text

    def _render_gui_node(self, node: Any, bounds: tuple[int, int, int, int], depth: int) -> str:
        """Render a GuiNode hierarchy to textual output."""

        indent = "  " * depth
        width = getattr(node, "width", 0)
        height = getattr(node, "height", 0)
        x = getattr(node, "x", 0)
        y = getattr(node, "y", 0)
        lines = [
            f"{indent}({x},{y}) {width}x{height}"
        ]
        text_content = getattr(node, "text", None)
        if text_content:
            lines.append(f"{indent}  text: {text_content}")
        children = getattr(node, "children", []) or []
        for child in children:
            lines.append(self._render_gui_node(child, bounds, depth + 1))
        return "\n".join(lines) + ("\n" if lines else "")
