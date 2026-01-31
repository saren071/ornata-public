"""ANSI-capable CLI renderer.

Moves the legacy ANSIRenderer into the new rendering tree and trims
dependencies to match the minimal core base.
"""

from __future__ import annotations

from threading import RLock
from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger
from ornata.rendering.backends.cli.terminal import TerminalRenderer
from ornata.styling.colorkit.resolver import ColorResolver

if TYPE_CHECKING:
    from ornata.api.exports.definitions import BackendTarget, RenderOutput

logger = get_logger(__name__)


class ANSIRenderer(TerminalRenderer):
    """ANSI renderer for colored and styled CLI output."""

    def __init__(self, backend_target: BackendTarget) -> None:
        super().__init__(backend_target)
        self._render_lock = RLock()
        self._ansi_enabled = True
        self._color_resolver = ColorResolver()
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
                styled = self._apply_backend_style(tree, output)
                if styled is not None:
                    content = styled
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

    def _apply_backend_style(self, tree: Any, output: RenderOutput) -> str | None:
        """Apply backend-conditioned style (already converted) to rendered content when available."""

        try:
            root = getattr(tree, "root", tree)
            backend_payload = None
            if hasattr(root, "metadata"):
                backend_payload = getattr(root, "metadata", {}).get("backend_style")
            if backend_payload is None:
                return None

            style = getattr(backend_payload, "style", None)
            if style is None:
                return None

            fg_seq = style.color if isinstance(style.color, str) else ""
            bg_seq = style.background if isinstance(getattr(style, "background", None), str) else ""

            # Fallback: resolve non-ANSI specs into ANSI sequences
            if not fg_seq and getattr(style, "color", None) is not None:
                fg_seq = self._color_resolver.resolve_ansi(style.color)
            if not bg_seq and getattr(style, "background", None) is not None:
                bg_seq = self._color_resolver.resolve_background(str(style.background))

            if not fg_seq and not bg_seq:
                return None

            return f"{bg_seq}{fg_seq}{output.content}"
        except Exception:
            return None

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
