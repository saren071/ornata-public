"""Live session rendering for CLI.

Ported minimally from the legacy renderer and adapted to the new core base.
"""

from __future__ import annotations

import time
from threading import RLock, Thread
from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger
from ornata.rendering.backends.cli.terminal import TerminalRenderer

if TYPE_CHECKING:
    from ornata.api.exports.definitions import BackendTarget, RenderOutput

logger = get_logger(__name__)


class LiveSessionRenderer(TerminalRenderer):
    """CLI renderer variant with simple live-session cadence controls."""

    def __init__(self, backend_target: BackendTarget) -> None:
        super().__init__(backend_target)
        self._render_lock = RLock()
        self._session_active = False
        self._update_thread: Thread | None = None
        self._last_render_time = 0.0
        self._target_fps = 30
        self._frame_interval = 1.0 / self._target_fps
        logger.debug("Initialized LiveSessionRenderer")

    def render_tree(self, tree: Any, layout_result: Any) -> RenderOutput:
        from ornata.api.exports.definitions import RenderOutput
        with self._render_lock:
            try:
                output = super().render_tree(tree, layout_result)
                self._last_render_time = time.perf_counter()
                meta = dict(output.metadata or {})
                meta.update({"live_session": True, "timestamp": self._last_render_time})
                return self._set_last_output(
                    RenderOutput(
                        content=output.content,
                        backend_target=output.backend_target,
                        metadata=meta,
                    )
                )
            except Exception as e:
                logger.error(f"Live session rendering failed: {e}")
                from ornata.api.exports.definitions import RenderingError
                raise RenderingError(f"Failed to render live session output: {e}") from e

    def apply_patches(self, patches: list[Any]) -> None:
        with self._render_lock:
            try:
                # For now, just invalidate like base terminal renderer
                super().apply_patches(patches)
                # Schedule an immediate re-render if active
                if self._session_active:
                    self._schedule_render()
            except Exception as e:
                logger.error(f"Live session patch application failed: {e}")
                from ornata.api.exports.definitions import RenderingError
                raise RenderingError(f"Failed to apply live session patches: {e}") from e

    def start_session(self) -> None:
        with self._render_lock:
            if self._session_active:
                return
            self._session_active = True
            self._update_thread = Thread(target=self._live_update_loop, daemon=True, name="LiveSessionRenderer")
            self._update_thread.start()

    def stop_session(self) -> None:
        with self._render_lock:
            if not self._session_active:
                return
            self._session_active = False
            if self._update_thread and self._update_thread.is_alive():
                self._update_thread.join(timeout=2.0)
            self._update_thread = None

    def is_session_active(self) -> bool:
        with self._render_lock:
            return self._session_active

    def set_target_fps(self, fps: int) -> None:
        if not 1 <= fps <= 60:
            raise ValueError("FPS must be between 1 and 60")
        with self._render_lock:
            self._target_fps = fps
            self._frame_interval = 1.0 / fps

    # -- internals ---------------------------------------------------------------
    def _live_update_loop(self) -> None:
        while self._session_active:
            time.sleep(self._frame_interval)
            # App-integrated re-render loop can be wired via the API layer
            # leaving this as a cadence keeper for now.

    def _schedule_render(self) -> None:
        # Reset last render time to encourage the next cycle promptly
        self._last_render_time = 0.0
