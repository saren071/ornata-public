"""Auto-generated exports for ornata.rendering.core."""

from __future__ import annotations

from . import base_renderer, capabilities, compositor, frame, pipeline, render_signals
from .base_renderer import RenderableBase, Renderer
from .capabilities import (
    get_capabilities,
    get_cli_capabilities,
    get_gui_capabilities,
    get_tty_capabilities,
)
from .compositor import Compositor
from .frame import FrameBuffer
from .pipeline import RenderPipeline
from .render_signals import (
    SignalDispatcher,
    SignalEmitter,
    get_global_dispatcher,
    get_global_emitter,
)

# from .surface import Empty currently

__all__ = [
    "Compositor",
    "FrameBuffer",
    "RenderPipeline",
    "RenderableBase",
    "Renderer",
    "SignalDispatcher",
    "SignalEmitter",
    "base_renderer",
    "capabilities",
    "compositor",
    "frame",
    "get_capabilities",
    "get_cli_capabilities",
    "get_global_dispatcher",
    "get_global_emitter",
    "get_gui_capabilities",
    "get_tty_capabilities",
    "pipeline",
    "render_signals",
]
