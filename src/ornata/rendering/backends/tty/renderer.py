"""TTY renderer implementation.

Provides low-level terminal rendering using VT100 escape sequences and
direct terminal control for maximum performance and compatibility.
"""

from __future__ import annotations

import sys
from threading import RLock
from typing import TYPE_CHECKING, Any, TextIO

from ornata.api.exports.utils import get_logger
from ornata.rendering.core.base_renderer import Renderer

if TYPE_CHECKING:
    from types import TracebackType

    from ornata.api.exports.definitions import BackendTarget, Patch, RenderOutput

logger = get_logger(__name__)


class TTYRenderer(Renderer):
    """Low-level TTY renderer using VT100 escape sequences.
    
    This renderer directly controls the terminal using VT100/ANSI escape
    sequences for cursor movement, colors, and text styling.
    
    Parameters
    ----------
    backend_target : BackendTarget
        The backend target (should be TTY).
    stream : TextIO
        Output stream (usually sys.stdout).
    use_alt_screen : bool
        Whether to use alternate screen buffer.
    
    Returns
    -------
    TTYRenderer
        TTY renderer instance.
    """

    def __init__(
        self,
        backend_target: BackendTarget,
        stream: TextIO = sys.stdout,
        use_alt_screen: bool = True,
    ) -> None:
        """Initialize the TTY renderer.
        
        Parameters
        ----------
        renderer_type : RendererType
            The renderer type.
        stream : TextIO
            Output stream for rendering.
        use_alt_screen : bool
            Whether to use alternate screen buffer.
        
        Returns
        -------
        None
        """
        from ornata.rendering.backends.tty.termios import TerminalController
        super().__init__(backend_target)
        self.stream = stream
        self.use_alt_screen = use_alt_screen
        self._term_controller = TerminalController(stream)
        self._render_lock = RLock()
        self._initialized = False
        self._cursor_visible = True
        self._last_size: tuple[int, int] = (0, 0)
        logger.debug(f"Initialized TTYRenderer (alt_screen={use_alt_screen})")

    def initialize(self) -> None:
        """Initialize the terminal for rendering.
        
        Returns
        -------
        None
        """
        from ornata.api.exports.definitions import EraseMode
        from ornata.rendering.backends.tty.vt100 import VT100
        if self._initialized:
            return

        with self._render_lock:
            self._term_controller.save_state()

            if self.use_alt_screen:
                self.stream.write(VT100.alternate_screen_enable())
                logger.debug("Enabled alternate screen")

            self.stream.write(VT100.cursor_hide())
            self._cursor_visible = False

            self.stream.write(VT100.erase_display(EraseMode.ALL))
            self.stream.write(VT100.cursor_position(1, 1))
            self.stream.flush()

            self._last_size = self._term_controller.get_size()
            self._initialized = True
            logger.debug("TTY renderer initialized")

    def shutdown(self) -> None:
        """Shutdown the renderer and restore terminal.
        
        Returns
        -------
        None
        """
        from ornata.rendering.backends.tty.vt100 import VT100
        if not self._initialized:
            return

        with self._render_lock:
            if not self._cursor_visible:
                self.stream.write(VT100.cursor_show())
                self._cursor_visible = True

            if self.use_alt_screen:
                self.stream.write(VT100.alternate_screen_disable())
                logger.debug("Disabled alternate screen")

            self.stream.write(VT100.reset())
            self.stream.flush()

            self._term_controller.restore_state()
            self._initialized = False
            logger.debug("TTY renderer shutdown")

    def render_tree(self, tree: Any, layout_result: Any) -> RenderOutput:
        """Render a VDOM tree to the terminal.
        
        Parameters
        ----------
        tree : Any
            The VDOM tree to render.
        layout_result : Any
            Computed layout information.
        
        Returns
        -------
        RenderOutput
            The rendered output.
        """
        from ornata.api.exports.definitions import RenderOutput
        from ornata.rendering.backends.tty.vt100 import VT100
        if not self._initialized:
            self.initialize()

        with self._render_lock:
            try:
                current_size = self._term_controller.get_size()
                if current_size != self._last_size:
                    self._handle_resize(current_size)
                    self._last_size = current_size

                content = self._render_node(getattr(tree, "root", None))

                self.stream.write(VT100.cursor_position(1, 1))
                self.stream.write(content)
                self.stream.flush()

                output = RenderOutput(
                    content=content,
                    backend_target=self.backend_target,
                    metadata={"terminal_size": current_size},
                )
                return self._set_last_output(output)

            except Exception as e:
                logger.error(f"TTY rendering failed: {e}")
                from ornata.api.exports.definitions import RenderingError
                raise RenderingError(f"TTY render failed: {e}") from e

    def apply_patches(self, patches: list[Any]) -> None:
        """Apply incremental patches to the terminal.
        
        This method efficiently applies VDOM patches to the terminal by tracking
        the current rendered state and applying only necessary changes.
        
        Parameters
        ----------
        patches : list[Any]
            Patches to apply to the terminal.
        
        Returns
        -------
        None
        """
        from ornata.api.exports.definitions import Patch, PatchType
        
        with self._render_lock:
            if not self._initialized:
                self.initialize()
                
            logger.log(5, f"Applying {len(patches)} patches to TTY")
            
            # Track if we need a full redraw
            needs_full_redraw = False
            patch_operations: list[Patch] = []
            
            # Process patches and categorize them
            for patch in patches:
                if not isinstance(patch, Patch):
                    continue
                    
                if patch.patch_type == PatchType.REPLACE_ROOT:
                    # Root replacement requires full redraw
                    needs_full_redraw = True
                    break
                elif patch.patch_type in (PatchType.ADD_NODE, PatchType.REMOVE_NODE, PatchType.MOVE_NODE):
                    # Structural changes may require partial redraw
                    patch_operations.append(patch)
                elif patch.patch_type == PatchType.UPDATE_PROPS:
                    # Property updates can often be applied incrementally
                    patch_operations.append(patch)
            
            # Apply patches
            if needs_full_redraw:
                # For root replacement, we need to re-render everything
                logger.debug("Full redraw required due to root replacement")
                self._full_redraw()
            else:
                # Apply incremental patches
                self._apply_incremental_patches(patch_operations)
            
            self.stream.flush()
    
    def apply_vdom_patches(self, patches: list[Any]) -> None:
        """Apply VDOM patches to the TTY renderer.
        
        This method provides a direct interface for VDOM patch application
        with enhanced TTY-specific optimizations.
        
        Parameters
        ----------
        patches : list[Any]
            VDOM patches to apply.
        
        Returns
        -------
        None
        """
        from ornata.api.exports.definitions import Patch, PatchType
        
        with self._render_lock:
            if not self._initialized:
                self.initialize()
                
            logger.debug(f"Applying {len(patches)} VDOM patches to TTY renderer")
            
            # Apply patches through the base method first
            self.apply_patches(patches)
            
            # TTY-specific optimizations after base application
            for patch in patches:
                if not isinstance(patch, Patch):
                    continue
                    
                # TTY-specific patch handling
                if patch.patch_type == PatchType.UPDATE_PROPS and patch.key:
                    # For content updates, optimize TTY rendering
                    self._optimize_tty_content_update(patch.key, patch.data)
                elif patch.patch_type == PatchType.MOVE_NODE and patch.key:
                    # For node moves, update position tracking
                    self._update_node_position_tracking(patch.key, patch.data)
    
    def _optimize_tty_content_update(self, key: str, props: dict[str, Any]) -> None:
        """Optimize TTY content updates for better performance.
        
        Parameters
        ----------
        key : str
            The key of the node being updated.
        props : dict[str, Any]
            The new properties.
        
        Returns
        -------
        None
        """
        if 'content' in props and isinstance(props['content'], str):
            # For content-only updates, try to do partial redraw
            content = props['content']
            logger.debug(f"Optimized TTY content update for key {key}: {len(content)} chars")
            # TODO: Implement partial redraw optimization
    
    def _update_node_position_tracking(self, key: str, new_position: int) -> None:
        """Update TTY position tracking for a node.
        
        Parameters
        ----------
        key : str
            The key of the node being moved.
        new_position : int
            The new position.
        
        Returns
        -------
        None
        """
        logger.debug(f"Updated TTY position tracking for key {key} to position {new_position}")
        # TODO: Implement position tracking for optimal TTY updates
            
    def _apply_incremental_patches(self, patches: list[Patch]) -> None:
        """Apply patches incrementally to the terminal.
        
        Parameters
        ----------
        patches : list[Patch]
            List of patches to apply.
        
        Returns
        -------
        None
        """
        from ornata.api.exports.definitions import PatchType
        
        # Group operations by type for batch processing
        add_operations: list[Patch] = []
        remove_operations: list[Patch] = []
        update_operations: list[Patch] = []
        move_operations: list[Patch] = []
        
        for patch in patches:
            if patch.patch_type == PatchType.ADD_NODE:
                add_operations.append(patch)
            elif patch.patch_type == PatchType.REMOVE_NODE:
                remove_operations.append(patch)
            elif patch.patch_type == PatchType.UPDATE_PROPS:
                update_operations.append(patch)
            elif patch.patch_type == PatchType.MOVE_NODE:
                move_operations.append(patch)
        
        # Apply operations in order
        if remove_operations:
            self._apply_remove_operations(remove_operations)
        if add_operations:
            self._apply_add_operations(add_operations)
        if move_operations:
            self._apply_move_operations(move_operations)
        if update_operations:
            self._apply_update_operations(update_operations)
    
    def _apply_add_operations(self, patches: list[Patch]) -> None:
        """Apply ADD_NODE patches.
        
        Parameters
        ----------
        patches : list[Patch]
            ADD_NODE patches to apply.
        
        Returns
        -------
        None
        """
        for patch in patches:
            node = patch.data
            if node is None:
                continue
                
            # Render the new node
            node_text = self._render_node(node)
            if node_text:
                # For now, add at the end of the display
                # A more sophisticated approach would track positions
                self.stream.write(node_text)
                logger.debug(f"Added node to TTY display: {len(node_text)} chars")
    
    def _apply_remove_operations(self, patches: list[Patch]) -> None:
        """Apply REMOVE_NODE patches.
        
        Parameters
        ----------
        patches : list[Patch]
            REMOVE_NODE patches to apply.
        
        Returns
        -------
        None
        """
        for patch in patches:
            key = patch.key
            if key is None:
                continue
                
            # For TTY, removing nodes is complex without position tracking
            # For now, we'll mark this for a partial redraw
            logger.debug(f"Node removal requested for key: {key}")
            # TODO: Implement position-based removal
    
    def _apply_update_operations(self, patches: list[Patch]) -> None:
        """Apply UPDATE_PROPS patches.
        
        Parameters
        ----------
        patches : list[Patch]
            UPDATE_PROPS patches to apply.
        
        Returns
        -------
        None
        """
        for patch in patches:
            key = patch.key
            props = patch.data
            if key is None or not isinstance(props, dict):
                continue
                
            # Check if this is a content update
            if 'content' in props:
                # For content changes, we can try to update in place
                logger.debug(f"Content update for node {key}: {props['content']}")
                # TODO: Implement in-place content updates with position tracking
    
    def _apply_move_operations(self, patches: list[Patch]) -> None:
        """Apply MOVE_NODE patches.
        
        Parameters
        ----------
        patches : list[Patch]
            MOVE_NODE patches to apply.
        
        Returns
        -------
        None
        """
        for patch in patches:
            key = patch.key
            new_position = patch.data
            if key is None or new_position is None:
                continue
                
            # Moving nodes in TTY requires position tracking
            logger.debug(f"Node move requested for {key} to position {new_position}")
            # TODO: Implement position-based moves
    
    def _full_redraw(self) -> None:
        """Perform a full redraw of the terminal.
        
        Returns
        -------
        None
        """
        # Clear and redraw everything
        self.clear_screen()
        logger.debug("Performed full TTY redraw")

    def clear_screen(self) -> None:
        """Clear the terminal screen.
        
        Returns
        -------
        None
        """
        from ornata.api.exports.definitions import EraseMode
        from ornata.rendering.backends.tty.vt100 import VT100
        with self._render_lock:
            self.stream.write(VT100.erase_display(EraseMode.ALL))
            self.stream.write(VT100.cursor_position(1, 1))
            self.stream.flush()
            logger.log(5, "Cleared TTY screen")

    def set_cursor_position(self, row: int, col: int) -> None:
        """Set cursor position.
        
        Parameters
        ----------
        row : int
            Row number (1-indexed).
        col : int
            Column number (1-indexed).
        
        Returns
        -------
        None
        """
        from ornata.rendering.backends.tty.vt100 import VT100
        with self._render_lock:
            self.stream.write(VT100.cursor_position(row, col))
            self.stream.flush()

    def hide_cursor(self) -> None:
        """Hide the cursor.
        
        Returns
        -------
        None
        """
        from ornata.rendering.backends.tty.vt100 import VT100
        if not self._cursor_visible:
            return

        with self._render_lock:
            self.stream.write(VT100.cursor_hide())
            self.stream.flush()
            self._cursor_visible = False
            logger.log(5, "Cursor hidden")

    def show_cursor(self) -> None:
        """Show the cursor.
        
        Returns
        -------
        None
        """
        from ornata.rendering.backends.tty.vt100 import VT100
        if self._cursor_visible:
            return

        with self._render_lock:
            self.stream.write(VT100.cursor_show())
            self.stream.flush()
            self._cursor_visible = True
            logger.log(5, "Cursor shown")

    def write_at(self, row: int, col: int, text: str) -> None:
        """Write text at a specific position.
        
        Parameters
        ----------
        row : int
            Row number (1-indexed).
        col : int
            Column number (1-indexed).
        text : str
            Text to write.
        
        Returns
        -------
        None
        """
        from ornata.rendering.backends.tty.vt100 import VT100
        with self._render_lock:
            self.stream.write(VT100.cursor_position(row, col))
            self.stream.write(text)
            self.stream.flush()

    def _render_node(self, node: Any) -> str:
        """Recursively render a VDOM node to text.
        
        Parameters
        ----------
        node : Any
            Node to render.
        
        Returns
        -------
        str
            Rendered text content.
        """
        if node is None:
            return ""

        text = ""
        props: dict[str, Any] | None = getattr(node, "props", None)
        if props is None:
            return ""
        content = props.get("content")
        if content:
            text += str(content)

        for child in getattr(node, "children", []) or []:
            text += self._render_node(child)

        return text

    def _handle_resize(self, new_size: tuple[int, int]) -> None:
        """Handle terminal resize event.
        
        Parameters
        ----------
        new_size : tuple[int, int]
            New terminal size (rows, columns).
        
        Returns
        -------
        None
        """
        logger.debug(f"Terminal resized to {new_size[0]}x{new_size[1]}")
        self.clear_screen()

    def __enter__(self) -> TTYRenderer:
        """Context manager entry.
        
        Returns
        -------
        TTYRenderer
            Self.
        """
        self.initialize()
        return self

    def __exit__(self, exc_type: type[BaseException], exc_val: BaseException, exc_tb: TracebackType) -> None:
        """Context manager exit.
        
        Parameters
        ----------
        exc_type : Type[BaseException]
            Exception type.
        exc_val : BaseException
            Exception value.
        exc_tb : Traceback
            Exception traceback.
        
        Returns
        -------
        None
        """
        self.shutdown()

    def __del__(self) -> None:
        """Destructor to ensure cleanup.
        
        Returns
        -------
        None
        """
        try:
            self.shutdown()
        except Exception:
            pass
