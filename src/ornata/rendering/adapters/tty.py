"""TTY renderer implementation.

Provides low-level terminal rendering using VT100 escape sequences and
direct terminal control for maximum performance and compatibility.
"""

from __future__ import annotations

import sys
from threading import RLock
from typing import TYPE_CHECKING, Any, TextIO

from ornata.api.exports.utils import get_logger
from ornata.rendering.adapters.base import VDOMAdapter

if TYPE_CHECKING:
    from types import TracebackType

    from ornata.api.exports.definitions import BackendTarget, RenderOutput

logger = get_logger(__name__)


class TTYAdapter(VDOMAdapter):
    """Low-level TTY renderer using VT100 escape sequences."""

    def __init__(
        self,
        backend_target: BackendTarget,
        renderer_instance: Any,
        stream: TextIO = sys.stdout,
        use_alt_screen: bool = True,
    ) -> None:
        from ornata.rendering.backends.tty.termios import TerminalController
        super().__init__(backend_target, renderer_instance)
        self.stream = stream
        self.use_alt_screen = use_alt_screen
        self._term_controller = TerminalController(stream)
        self._render_lock = RLock()
        self._initialized = False
        self._cursor_visible = True
        self._last_size: tuple[int, int] = (0, 0)

    def initialize(self) -> None:
        from ornata.api.exports.definitions import EraseMode
        from ornata.rendering.backends.tty.vt100 import VT100
        if self._initialized:
            return

        with self._render_lock:
            self._term_controller.save_state()
            if self.use_alt_screen:
                self.stream.write(VT100.alternate_screen_enable())
            self.stream.write(VT100.cursor_hide())
            self._cursor_visible = False
            self.stream.write(VT100.erase_display(EraseMode.ALL))
            self.stream.write(VT100.cursor_position(1, 1))
            self.stream.flush()
            self._last_size = self._term_controller.get_size()
            self._initialized = True

    def shutdown(self) -> None:
        from ornata.rendering.backends.tty.vt100 import VT100
        if not self._initialized:
            return

        with self._render_lock:
            if not self._cursor_visible:
                self.stream.write(VT100.cursor_show())
            if self.use_alt_screen:
                self.stream.write(VT100.alternate_screen_disable())
            self.stream.write(VT100.reset())
            self.stream.flush()
            self._term_controller.restore_state()
            self._initialized = False

    def render_tree(self, tree: Any, layout_result: Any) -> RenderOutput:
        from ornata.api.exports.definitions import RenderOutput
        from ornata.rendering.backends.tty.vt100 import VT100
        
        if not self._initialized:
            self.initialize()

        with self._render_lock:
            current_size = self._term_controller.get_size()
            if current_size != self._last_size:
                self.clear_screen()
                self._last_size = current_size

            content = self._render_node(getattr(tree, "root", None))
            self.stream.write(VT100.cursor_position(1, 1))
            self.stream.write(content)
            self.stream.flush()

            return RenderOutput(
                content=content,
                backend_target=self.backend_target,
                metadata={"terminal_size": current_size},
            )

    def apply_patches(self, patches: list[Any]) -> None:
        """Apply patches to the terminal."""
        with self._render_lock:
            if not self._initialized:
                self.initialize()
            
            # For TTY, ensuring correctness is prioritized over complex incremental updates.
            # Structural changes trigger a full redraw to prevent artifacts.
            self._full_redraw()

    def _full_redraw(self) -> None:
        self.clear_screen()
        # The next render_tree call will repopulate the screen

    def clear_screen(self) -> None:
        from ornata.api.exports.definitions import EraseMode
        from ornata.rendering.backends.tty.vt100 import VT100
        with self._render_lock:
            self.stream.write(VT100.erase_display(EraseMode.ALL))
            self.stream.write(VT100.cursor_position(1, 1))
            self.stream.flush()

    def _render_node(self, node: Any) -> str:
        if node is None:
            return ""
        text = ""
        props: dict[str, Any] | None = getattr(node, "props", None)
        if props:
            content = props.get("content")
            if content:
                text += str(content)
        for child in getattr(node, "children", []) or []:
            text += self._render_node(child)
        return text

    def __enter__(self) -> TTYAdapter:
        self.initialize()
        return self

    def __exit__(self, exc_type: type[BaseException], exc_val: BaseException, exc_tb: TracebackType) -> None:
        self.shutdown()