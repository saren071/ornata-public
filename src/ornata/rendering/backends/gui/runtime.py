"""GUI runtime for surface management and frame presentation.

Provides a process-scoped runtime that manages per-window surfaces,
schedules frame presentation, and exposes hooks for rendering backends.
"""

from __future__ import annotations

import io
import threading
import time
from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.definitions import GuiNode
    from ornata.rendering.backends.gui.platform.win32.window import Win32Window

logger = get_logger(__name__)

_runtime_lock = threading.Lock()
_runtime: GuiRuntime | None = None


def get_runtime(create: bool = True) -> GuiRuntime | None:
    """Get or create the singleton GUI runtime."""
    global _runtime
    with _runtime_lock:
        if _runtime is None and create:
            _runtime = GuiRuntime()
        return _runtime


class Surface:
    """GUI surface with GPU backing and compositing support."""

    def __init__(self, width: int, height: int) -> None:
        from ornata.rendering.backends.gui.compositor import Compositor
        self.width = width
        self.height = height
        self.compositor = Compositor(width, height)
        self._last_frame_time = 0.0
        self._frame_count = 0

    def resize(self, width: int, height: int) -> None:
        """Resize the surface."""
        self.width = width
        self.height = height
        self.compositor.resize(width, height)

    def render_gui_node(self, node: GuiNode, gpu_context: Any | None) -> None:
        """Render a GUI node tree to this surface."""
        from ornata.api.exports.gpu import Canvas
        from ornata.rendering.backends.gui.renderer import render_tree
        if gpu_context:
            # Render the GUI tree directly to the current render target
            canvas = Canvas(gpu_context, self.width, self.height)
            render_tree(canvas, node)
            
            # Only use compositor if there are actually layers to composite
            # This prevents the compositor from clearing the render target
            # when no layers are present, which would wipe out the render_tree output
            if self.compositor.layers:
                self.compositor.composite(gpu_context)
        else:
            self._render_text_fallback(node)

        self._frame_count += 1
        self._last_frame_time = time.perf_counter()

    def _render_text_fallback(self, node: GuiNode) -> None:
        """Render a fallback textual representation when no GPU context exists."""
        lines: list[str] = []

        def walk(current: GuiNode, depth: int) -> None:
            indent = " " * (depth * 2)
            label = current.component_name
            text = getattr(current, "text", None)
            bounds = (
                getattr(current, "x", None),
                getattr(current, "y", None),
                getattr(current, "width", None),
                getattr(current, "height", None),
            )
            bounds_repr = ""
            if all(value is not None for value in bounds):
                bounds_repr = f" [{bounds[0]}, {bounds[1]} {bounds[2]}x{bounds[3]}]"

            if text:
                summary = f"{label}{bounds_repr} :: {text}"
            else:
                summary = f"{label}{bounds_repr}"

            style = getattr(current, "style", None)
            if style is not None and hasattr(style, "display"):
                summary += f" (display={style.display})"

            lines.append(f"{indent}{summary}")
            for child in getattr(current, "children", []) or []:
                walk(child, depth + 1)

        walk(node, 0)
        fallback_frame = "\n".join(lines)
        logger.debug("GUI fallback frame rendered as text:\n%s", fallback_frame)
        runtime = get_runtime(create=False)
        if runtime is not None:
            runtime.present_text_frame(fallback_frame)


class GuiRuntime:
    """Manages per-window surfaces and frame presentation."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._windows: dict[int, Win32Window] = {}
        self._surfaces: dict[int, Surface] = {}
        self._frame_scheduler_active = False
        self._target_fps = 60.0
        self._text_stream = GuiStream(self)
        self._last_text_frame: str = ""

    def set_window(self, window: Win32Window) -> None:
        """Associate a window with this runtime."""
        with self._lock:
            window_id = id(window)
            self._windows[window_id] = window

            # Create surface for the window
            surface = Surface(window.width, window.height)
            self._surfaces[window_id] = surface

    def remove_window(self, window: Win32Window) -> None:
        """Remove a window from this runtime."""
        with self._lock:
            window_id = id(window)
            self._windows.pop(window_id, None)
            self._surfaces.pop(window_id, None)

    def get_surface_for_window(self, window: Win32Window) -> Surface | None:
        """Get the surface associated with a window."""
        with self._lock:
            return self._surfaces.get(id(window))

    def render_gui_node(self, node: GuiNode, window: Win32Window | None = None) -> None:
        """Render a GUI node to the specified window."""
        if window is None:
            # Use first available window
            with self._lock:
                if self._windows:
                    window = next(iter(self._windows.values()))

        if window:
            # Store the root node for the scheduler loop to re-render every frame
            window.root_node = node
            
            surface = self.get_surface_for_window(window)
            if surface:
                surface.render_gui_node(node, window.get_gpu_context())

    def start_frame_scheduler(self, fps: float = 60.0) -> None:
        """Start the frame presentation scheduler."""
        if self._frame_scheduler_active:
            return

        self._target_fps = fps
        self._frame_scheduler_active = True

        # Start scheduler thread
        import threading
        scheduler_thread = threading.Thread(target=self._frame_scheduler_loop, daemon=True)
        scheduler_thread.start()

    def stop_frame_scheduler(self) -> None:
        self._frame_scheduler_active = False
        with self._lock:
            for win in self._windows.values():
                handle = getattr(win, "_pump_handle", None)
                if handle:
                    thread = handle.thread
                    if thread is threading.current_thread():
                        continue
                    if thread.is_alive():
                        thread.join(timeout=0.5)

    def _frame_scheduler_loop(self) -> None:
        """Main frame scheduling loop."""
        frame_interval = 1.0 / self._target_fps

        while self._frame_scheduler_active:
            start_time = time.perf_counter()

            # Present frames for all surfaces
            with self._lock:
                for window_id, surface in self._surfaces.items():
                    window = self._windows.get(window_id)
                    if window:
                        # 1) re-render GUI tree every frame
                        node = window.root_node
                        if node:
                            surface.render_gui_node(node, window.get_gpu_context())

                        # 2) present
                        gpu_context = window.get_gpu_context()
                        if gpu_context:
                            gpu_context.present()

            # Sleep to maintain frame rate
            elapsed = time.perf_counter() - start_time
            sleep_time = max(0.0, frame_interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def create_stream(self) -> GuiStream:
        """Create a GUI stream for text output."""
        return GuiStream(self)

    def present_text_frame(self, text: str) -> None:
        """Present a fallback text frame through the GUI stream."""
        stream = self._text_stream
        stream.clear_frame()
        stream.write(text)
        stream.present_frame(text)
        print(text)
        self._last_text_frame = text

    # Legacy compatibility methods
    def append_text(self, chunk: str) -> None:
        """Legacy text appending (for compatibility)."""
        if not chunk:
            return
        self._text_stream.write(chunk)

    def present_frame(self, text: str) -> None:
        """Legacy frame presentation (for compatibility)."""
        combined = text
        if self._text_stream.buffer:
            self._text_stream.buffer.append(text)
            combined = "".join(self._text_stream.buffer)
        self.present_text_frame(combined)

    def clear(self) -> None:
        """Clear all surfaces."""
        with self._lock:
            for surface in self._surfaces.values():
                surface.compositor.clear_dirty_regions()
        self._last_text_frame = ""


class GuiStream(io.TextIOBase):
    """GUI stream for text-based output compatibility."""

    def __init__(self, runtime: GuiRuntime) -> None:
        super().__init__()
        self._runtime = runtime
        self.buffer: list[str] = []
        self._closed = False
    @property
    def encoding(self) -> str:
        return "utf-8"

    def writable(self) -> bool:
        return True

    def write(self, text: str) -> int:
        if self._closed:
            raise ValueError("I/O operation on closed GUI stream")
        self.buffer.append(text)
        return len(text)

    def flush(self) -> None:
        if self._closed or not self.buffer:
            return
        chunk = "".join(self.buffer)
        self.buffer.clear()
        # For compatibility, this doesn't do much in GUI mode
        logger.debug(f"GUI stream flushed: {len(chunk)} characters")

    def present_frame(self, text: str) -> None:
        """Present a text frame (legacy compatibility)."""
        if self._closed:
            return
        self.buffer.clear()
        logger.info("GUI runtime fallback frame:\n%s", text)

    def clear_frame(self) -> None:
        """Clear the current frame."""
        if self._closed:
            return
        self.buffer.clear()
        self._runtime.clear()

    def close(self) -> None:
        if self._closed:
            return
        try:
            self.flush()
        finally:
            self._closed = True
