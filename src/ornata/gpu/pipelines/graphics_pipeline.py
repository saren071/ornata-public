"""Graphics pipeline management for GPU rendering operations.

This module provides the GraphicsPipeline class for managing graphics pipeline state,
rendering configuration, and shader program management across different GPU backends.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.gpu.misc import Shader

logger = get_logger(__name__)


class GraphicsPipeline:
    """Manages graphics pipeline state and rendering operations.

    This class provides a high-level interface for configuring graphics pipelines,
    managing shader programs, and controlling rendering state across different
    GPU backends with cross-platform compatibility.
    """

    def __init__(self, backend: Any) -> None:
        """Initialize graphics pipeline with GPU backend.

        Args:
            backend: The GPU backend implementation to use for graphics operations.
        """
        self._backend = backend
        self._vertex_shader: Shader | None = None
        self._fragment_shader: Shader | None = None
        self._is_bound = False
        self._viewport = (0, 0, 800, 600)  # Default viewport
        self._scissor = (0, 0, 800, 600)   # Default scissor rect

    def bind_vertex_shader(self, shader: Shader) -> None:
        """Bind a vertex shader to the graphics pipeline.

        Args:
            shader: The vertex shader to bind for rendering operations.

        Raises:
            GPUPipelineError: If shader binding fails.
        """
        if not shader.compiled:
            from ornata.api.exports.definitions import GPUPipelineError
            raise GPUPipelineError(f"Cannot bind uncompiled vertex shader: {shader.name}")

        try:
            self._vertex_shader = shader
            self._update_pipeline_state()
            logger.debug(f"Bound vertex shader: {shader.name}")
        except Exception as e:
            from ornata.api.exports.definitions import GPUPipelineError
            raise GPUPipelineError(f"Failed to bind vertex shader {shader.name}: {e}") from e

    def bind_fragment_shader(self, shader: Shader) -> None:
        """Bind a fragment shader to the graphics pipeline.

        Args:
            shader: The fragment shader to bind for rendering operations.

        Raises:
            GPUPipelineError: If shader binding fails.
        """
        if not shader.compiled:
            from ornata.api.exports.definitions import GPUPipelineError
            raise GPUPipelineError(f"Cannot bind uncompiled fragment shader: {shader.name}")

        try:
            self._fragment_shader = shader
            self._update_pipeline_state()
            logger.debug(f"Bound fragment shader: {shader.name}")
        except Exception as e:
            from ornata.api.exports.definitions import GPUPipelineError
            raise GPUPipelineError(f"Failed to bind fragment shader {shader.name}: {e}") from e

    def set_viewport(self, x: int, y: int, width: int, height: int) -> None:
        """Set the viewport dimensions for rendering.

        Args:
            x: X coordinate of viewport origin.
            y: Y coordinate of viewport origin.
            width: Width of viewport.
            height: Height of viewport.

        Raises:
            ValueError: If viewport dimensions are invalid.
        """
        if width <= 0 or height <= 0:
            raise ValueError("Viewport width and height must be positive")

        self._viewport = (x, y, width, height)
        logger.debug(f"Set viewport to: {self._viewport}")

    def set_scissor(self, x: int, y: int, width: int, height: int) -> None:
        """Set the scissor rectangle for rendering.

        Args:
            x: X coordinate of scissor rectangle origin.
            y: Y coordinate of scissor rectangle origin.
            width: Width of scissor rectangle.
            height: Height of scissor rectangle.

        Raises:
            ValueError: If scissor dimensions are invalid.
        """
        if width <= 0 or height <= 0:
            raise ValueError("Scissor width and height must be positive")

        self._scissor = (x, y, width, height)
        logger.debug(f"Set scissor rectangle to: {self._scissor}")

    def draw_arrays(self, mode: str, first: int, count: int) -> None:
        """Draw primitives from array data.

        Args:
            mode: Drawing mode (e.g., 'triangles', 'lines', 'points').
            first: Starting index in the array.
            count: Number of vertices to draw.

        Raises:
            GPUPipelineError: If drawing fails or pipeline is not properly configured.
        """
        if not self._is_bound:
            from ornata.api.exports.definitions import GPUPipelineError
            raise GPUPipelineError("Graphics pipeline not bound for rendering")

        if count <= 0:
            raise ValueError("Draw count must be positive")

        try:
            draw_arrays = getattr(self._backend, "draw_arrays", None)
            if callable(draw_arrays):
                draw_arrays(mode, first, count, self._vertex_shader, self._fragment_shader)
                logger.debug("Delegated draw_arrays to backend for %s vertices", count)
            else:
                from ornata.api.exports.definitions import GPUPipelineError
                raise GPUPipelineError("Backend does not implement draw_arrays")
        except Exception as e:
            from ornata.api.exports.definitions import GPUPipelineError
            raise GPUPipelineError(f"Draw arrays operation failed: {e}") from e

    def draw_elements(self, mode: str, count: int, offset: int = 0) -> None:
        """Draw primitives from element array data.

        Args:
            mode: Drawing mode (e.g., 'triangles', 'lines', 'points').
            count: Number of elements to draw.
            offset: Starting offset in the element array.

        Raises:
            GPUPipelineError: If drawing fails or pipeline is not properly configured.
        """
        if not self._is_bound:
            from ornata.api.exports.definitions import GPUPipelineError
            raise GPUPipelineError("Graphics pipeline not bound for rendering")

        if count <= 0:
            raise ValueError("Draw count must be positive")

        try:
            draw_elements = getattr(self._backend, "draw_elements", None)
            if callable(draw_elements):
                draw_elements(mode, count, offset, self._vertex_shader, self._fragment_shader)
                logger.debug("Delegated draw_elements to backend for %s elements", count)
            else:
                from ornata.api.exports.definitions import GPUPipelineError
                raise GPUPipelineError("Backend does not implement draw_elements")
        except Exception as e:
            from ornata.api.exports.definitions import GPUPipelineError
            raise GPUPipelineError(f"Draw elements operation failed: {e}") from e

    def unbind(self) -> None:
        """Unbind all shaders from the graphics pipeline."""
        self._vertex_shader = None
        self._fragment_shader = None
        self._is_bound = False
        logger.debug("Unbound all shaders from graphics pipeline")

    def _update_pipeline_state(self) -> None:
        """Update pipeline binding state based on current shaders."""
        self._is_bound = self._vertex_shader is not None and self._fragment_shader is not None

    @property
    def is_bound(self) -> bool:
        """Check if the graphics pipeline is properly bound for rendering.

        Returns:
            True if both vertex and fragment shaders are bound, False otherwise.
        """
        return self._is_bound

    @property
    def vertex_shader(self) -> Shader | None:
        """Get the currently bound vertex shader.

        Returns:
            The bound vertex shader or None if no shader is bound.
        """
        return self._vertex_shader

    @property
    def fragment_shader(self) -> Shader | None:
        """Get the currently bound fragment shader.

        Returns:
            The bound fragment shader or None if no shader is bound.
        """
        return self._fragment_shader

    @property
    def viewport(self) -> tuple[int, int, int, int]:
        """Get the current viewport dimensions.

        Returns:
            Tuple of (x, y, width, height) viewport coordinates.
        """
        return self._viewport

    @property
    def scissor(self) -> tuple[int, int, int, int]:
        """Get the current scissor rectangle.

        Returns:
            Tuple of (x, y, width, height) scissor coordinates.
        """
        return self._scissor