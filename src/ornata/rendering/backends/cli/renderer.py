"""ANSI-capable CLI renderer.

Moves the legacy ANSIRenderer into the new rendering tree and trims
dependencies to match the minimal core base.
"""

from __future__ import annotations

from threading import RLock
from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger
from ornata.rendering.backends.cli.terminal import TerminalRenderer

if TYPE_CHECKING:
    from ornata.api.exports.definitions import BackendTarget, RenderOutput

logger = get_logger(__name__)


class ANSIRenderer(TerminalRenderer):
    """ANSI renderer for colored and styled CLI output."""

    def __init__(self, backend_target: BackendTarget) -> None:
        super().__init__(backend_target)
        self._render_lock = RLock()
        self._ansi_enabled = True
        logger.debug("Initialized ANSIRenderer")

    def render_tree(self, tree: Any, layout_result: Any) -> RenderOutput:
        """Render with ANSI styling and metadata."""
        from ornata.api.exports.definitions import RenderOutput
        with self._render_lock:
            try:
                output = super().render_tree(tree, layout_result)
                if not isinstance(output.content, str):
                    return output
                content = output.content
                # no-op styling hook; can be wired to Styling later
                if self._ansi_enabled:
                    content = self._wrap_reset(content)
                return self._set_last_output(
                    RenderOutput(content=content, backend_target=output.backend_target, metadata=output.metadata)
                )
            except Exception as e:
                logger.error(f"ANSI rendering failed: {e}")
                from ornata.api.exports.definitions import RenderingError
                raise RenderingError(f"Failed to render ANSI output: {e}") from e

    def _wrap_reset(self, content: str) -> str:
        """Wrap content with a reset code to prevent color bleed."""
        return f"{content}\x1b[0m" if content else content

    def apply_vdom_patches(self, patches: list[Any]) -> None:
        """Apply VDOM patches to the CLI renderer.
        
        Parameters
        ----------
        patches : list[Any]
            VDOM patches to apply.
        """
        from ornata.api.exports.definitions import Patch, PatchType
        
        with self._render_lock:
            logger.debug(f"Applying {len(patches)} VDOM patches to CLI renderer")
            
            # Apply patches through the base method first
            if hasattr(self, 'apply_patches'):
                self.apply_patches(patches)
            
            # CLI-specific optimizations
            for patch in patches:
                if not isinstance(patch, Patch):
                    continue
                    
                if patch.patch_type == PatchType.UPDATE_PROPS and patch.key:
                    # For content updates, optimize CLI rendering
                    if 'content' in patch.data:
                        logger.debug(f"CLI content update for key {patch.key}")
                        # TODO: Implement partial update optimization for CLI
