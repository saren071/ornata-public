"""GUI Window renderer.

This module provides the concrete implementation of the WindowRenderer,
which acts as the primary entry point for the VDOM bridge to render
GUI trees into a native window managed by the GuiApplication.
"""

from __future__ import annotations

from threading import RLock
from typing import TYPE_CHECKING, Any

from ornata.api.exports.rendering import Renderer
from ornata.api.exports.utils import get_logger
from ornata.rendering.backends.gui.app import get_default_application

if TYPE_CHECKING:
    from ornata.api.exports.definitions import BackendTarget, RendererType, RenderOutput

logger = get_logger(__name__)


class WindowRenderer(Renderer):
    """Renderer for window-based GUI applications.
    
    This renderer bridges the VDOM adapter output (GuiNode tree) to the
    GuiApplication and its managed windows. It ensures that the application
    loop is running and updates the window content.
    """

    def __init__(self, backend_target: BackendTarget, renderer_type: RendererType) -> None:
        super().__init__(backend_target)
        self.renderer_type: RendererType = renderer_type
        self._app = get_default_application()
        self._main_window: Any | None = None
        self._render_lock = RLock()
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the renderer and create the main window."""
        with self._render_lock:
            if self._initialized:
                return
            
            # Create the main window if it doesn't exist
            if not self._app.windows:
                self._main_window = self._app.create_window("Ornata App", 800, 600)
            else:
                self._main_window = self._app.windows[0]
            
            # Start the app loop in a separate thread if not running
            if not self._app.is_running:
                self._app.run_async()
            
            self._initialized = True
            logger.info("WindowRenderer initialized")

    def render_tree(self, tree: Any, layout_result: Any) -> RenderOutput:
        """Render the GuiNode tree to the window.
        
        Parameters
        ----------
        tree : GuiNode
            The root of the GUI node tree.
        layout_result : Any
            Layout information (unused here as GuiNode contains layout).
            
        Returns
        -------
        RenderOutput
            The render output containing metadata.
        """
        from ornata.api.exports.definitions import RenderOutput
        
        if not self._initialized:
            self.initialize()

        with self._render_lock:
            if self._main_window:
                # Pass the tree to the application to render on the window
                self._app.render_gui_node(tree, self._main_window)
            
            return self._set_last_output(
                RenderOutput(
                    content=b"GUI Rendered", 
                    backend_target=str(getattr(self, "backend_target", "gui")), 
                    metadata={"window": self._main_window, "renderer_type": self.renderer_type}
                )
            )

    def apply_patches(self, patches: list[Any]) -> None:
        """Apply patches to the renderer.
        
        For the GUI backend, we typically re-render the affected parts of the tree.
        Since the VDOM adapter handles the tree structure updates, this method
        is a signal to refresh the window content.
        """
        # In a retained mode system, we might update specific widgets.
        # Here, we rely on the next render_tree call or trigger a refresh.
        # The VDOM bridge calls render_tree after patching, so we don't need
        # to do much here unless we implement fine-grained invalidation.
        pass

    def create_window(self, title: str, width: int, height: int) -> None:
        """Create a new window explicitly."""
        with self._render_lock:
            self._main_window = self._app.create_window(title, width, height)

    def destroy_window(self) -> None:
        """Destroy the main window."""
        with self._render_lock:
            if self._main_window:
                self._app.destroy_window(self._main_window)
                self._main_window = None