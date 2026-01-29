"""Graphics pipeline state management for OpenGL."""

from ornata.api.exports.utils import get_logger

logger = get_logger(__name__)


class OpenGLPipelineManager:
    """Manages OpenGL graphics pipeline state."""

    def __init__(self) -> None:
        """Initialize the pipeline manager."""
        self._viewport_width = 800
        self._viewport_height = 600

    def setup_viewport(self, width: int = 800, height: int = 600) -> None:
        """Set up the OpenGL viewport.

        Args:
            width: Viewport width in pixels.
            height: Viewport height in pixels.
        """
        from ornata.api.exports.interop import GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, glClear, glClearColor, glViewport

        self._viewport_width = width
        self._viewport_height = height

        glViewport(0, 0, width, height)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        logger.debug(f"Set up viewport: {width}x{height}")

    def get_viewport_size(self) -> tuple[int, int]:
        """Get the current viewport size.

        Returns:
            Tuple of (width, height).
        """
        return (self._viewport_width, self._viewport_height)

    def enable_depth_test(self) -> None:
        """Enable depth testing."""
        from ornata.api.exports.interop import GL_DEPTH_TEST, glEnable

        glEnable(GL_DEPTH_TEST)

    def disable_depth_test(self) -> None:
        """Disable depth testing."""
        from ornata.api.exports.interop import GL_DEPTH_TEST, glDisable

        glDisable(GL_DEPTH_TEST)

    def enable_blending(self) -> None:
        """Enable alpha blending."""
        from ornata.api.exports.interop import GL_BLEND, GL_ONE_MINUS_SRC_ALPHA, GL_SRC_ALPHA, glBlendFunc, glEnable

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def disable_blending(self) -> None:
        """Disable alpha blending."""
        from ornata.api.exports.interop import GL_BLEND, glDisable

        glDisable(GL_BLEND)

    def set_clear_color(self, r: float, g: float, b: float, a: float = 1.0) -> None:
        """Set the clear color.

        Args:
            r: Red component (0.0-1.0).
            g: Green component (0.0-1.0).
            b: Blue component (0.0-1.0).
            a: Alpha component (0.0-1.0).
        """
        from ornata.api.exports.interop import glClearColor

        glClearColor(r, g, b, a)

    def clear_buffers(self, color: bool = True, depth: bool = True) -> None:
        """Clear the specified buffers.

        Args:
            color: Whether to clear the color buffer.
            depth: Whether to clear the depth buffer.
        """
        from ornata.api.exports.interop import GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, glClear

        clear_flags = 0
        if color:
            clear_flags |= GL_COLOR_BUFFER_BIT
        if depth:
            clear_flags |= GL_DEPTH_BUFFER_BIT

        if clear_flags:
            glClear(clear_flags)
