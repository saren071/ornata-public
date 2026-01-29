"""Auto-generated exports for ornata.rendering.backends.gui."""

from __future__ import annotations

from . import app, compositor, contexts, input, platform, renderer, runtime, window
from .app import (
    GuiApplication,
    create_application,
    get_default_application,
)
from .compositor import Compositor
from .renderer import (
    _draw_box,  # type: ignore [private]
    _draw_panel,  # type: ignore [private]
    _draw_text,  # type: ignore [private]
    _render_node,  # type: ignore [private]
    _safe_fill_rect,  # type: ignore [private]
    register,
    render_tree,
)
from .runtime import (
    GuiRuntime,
    GuiStream,
    Surface,
    get_runtime,
)
from .window import WindowRenderer

__all__ = [
    "Compositor",
    "GuiApplication",
    "GuiRuntime",
    "GuiStream",
    "Surface",
    "WindowRenderer",
    "_draw_box",
    "_draw_panel",
    "_draw_text",
    "_render_node",
    "_safe_fill_rect",
    "app",
    "compositor",
    "contexts",
    "create_application",
    "get_default_application",
    "get_runtime",
    "input",
    "platform",
    "register",
    "render_tree",
    "renderer",
    "runtime",
    "window",
]
