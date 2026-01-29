"""Immediate-mode GUI renderer helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ornata.api.exports.definitions import Color
from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable

    from ornata.api.exports.definitions import Canvas, DrawFunc, GuiNodeLike

logger = get_logger(__name__)

_DRAW_REGISTRY: dict[str, DrawFunc] = {}


def register(kind: str) -> Callable[[DrawFunc], DrawFunc]:
    def _wrap(fn: DrawFunc) -> DrawFunc:
        _DRAW_REGISTRY[kind] = fn
        return fn
    return _wrap


def render_tree(canvas: Canvas, root: Any, runtime: Any | None = None) -> None:
    """Render a GuiNode tree or GuiNode-like structure to the canvas."""
    if hasattr(canvas, "viewport_w") and hasattr(canvas, "viewport_h"):
        canvas.fill_rect(0, 0, int(canvas.viewport_w), int(canvas.viewport_h), (0, 0, 0, 255))
    _render_node(canvas, root, runtime)


def _render_node(canvas: Canvas, node: GuiNodeLike, runtime: Any | None = None) -> None:
    fn = _DRAW_REGISTRY.get(getattr(node, "component_name", ""))
    if fn:
        try:
            fn(canvas, node)
        except Exception as e:
            logger.error(f"GUI draw error for {node.component_name}: {e}")
    
    for child in getattr(node, "children", []) or []:
        _render_node(canvas, child, runtime)


def _safe_fill_rect(canvas: Canvas, node: GuiNodeLike, color: tuple[int, int, int, int]) -> None:
    w = max(int(getattr(node, "width", 0)), 1)
    h = max(int(getattr(node, "height", 0)), 1)
    canvas.fill_rect(int(node.x), int(node.y), w, h, color)


@register("text")
def _draw_text(canvas: Canvas, node: GuiNodeLike, runtime: Any | None = None) -> None:
    text = getattr(node, "text", None) or ""
    # Default white text
    color = (255, 255, 255, 255)

    # Use mapped foreground color from GUI adapter metadata when available
    metadata: dict[str, Any] = node.metadata
    fg_raw = metadata.get("fg")
    fg: Color | None = fg_raw if isinstance(fg_raw, Color) else None
    if fg is not None:
        try:
            color = fg.to_tuple()
        except Exception:
            logger.debug("Failed to convert foreground color from metadata", exc_info=True)

    canvas.draw_text(int(node.x), int(node.y), text, color=color, font_face="Arial", px=14, weight=400)


@register("box")
def _draw_box(canvas: Canvas, node: GuiNodeLike, runtime: Any | None = None) -> None:
    color = (50, 50, 50, 255)
    metadata: dict[str, Any] = node.metadata
    bg_raw = metadata.get("bg")
    bg: Color | None = bg_raw if isinstance(bg_raw, Color) else None
    if bg is not None:
        try:
            color = bg.to_tuple()
        except Exception:
            logger.debug("Failed to convert background color from metadata", exc_info=True)

    _safe_fill_rect(canvas, node, color)
    canvas.stroke_rect(int(node.x), int(node.y), int(node.width), int(node.height), (100, 100, 100, 255), 1)


@register("panel")
def _draw_panel(canvas: Canvas, node: GuiNodeLike, runtime: Any | None = None) -> None:
    _safe_fill_rect(canvas, node, (30, 30, 40, 255))
    canvas.stroke_rect(int(node.x), int(node.y), int(node.width), int(node.height), (60, 60, 70, 255), 2)

_ = (_draw_text, _draw_box, _draw_panel)