"""OpenGL state management."""

from ornata.api.exports.utils import get_logger

logger = get_logger(__name__)


class OpenGLStateManager:
    """Manages OpenGL rendering state."""

    def __init__(self) -> None:
        """Initialize the state manager."""
        self._current_program = 0
        self._current_vao = 0
        self._current_vbo = 0
        self._current_ibo = 0

    def setup_render_state(self) -> None:
        """Set up the default OpenGL render state."""
        from ornata.api.exports.interop import GL_BLEND, GL_DEPTH_TEST, GL_ONE_MINUS_SRC_ALPHA, GL_SRC_ALPHA, glBlendFunc, glClearColor, glEnable

        # Enable depth testing and blending
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Set clear color
        glClearColor(0.0, 0.0, 0.0, 1.0)

        logger.debug("Set up OpenGL render state")

    def save_state(self) -> dict[str, int]:
        """Save the current OpenGL state.

        Returns:
            Dictionary containing current state values.
        """
        return {
            "program": self._current_program,
            "vao": self._current_vao,
            "vbo": self._current_vbo,
            "ibo": self._current_ibo,
        }

    def restore_state(self, state: dict[str, int]) -> None:
        """Restore OpenGL state from saved values.

        Args:
            state: State dictionary returned by save_state().
        """
        from ornata.api.exports.interop import GL_ARRAY_BUFFER, GL_ELEMENT_ARRAY_BUFFER, glBindBuffer, glBindVertexArray, glUseProgram

        if state.get("program") != self._current_program:
            glUseProgram(state["program"])
            self._current_program = state["program"]

        if state.get("vao") != self._current_vao:
            glBindVertexArray(state["vao"])
            self._current_vao = state["vao"]

        if state.get("vbo") != self._current_vbo:
            glBindBuffer(GL_ARRAY_BUFFER, state["vbo"])
            self._current_vbo = state["vbo"]

        if state.get("ibo") != self._current_ibo:
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, state["ibo"])
            self._current_ibo = state["ibo"]

    def enable_vertex_attrib_array(self, index: int) -> None:
        """Enable a vertex attribute array.

        Args:
            index: Attribute index to enable.
        """
        from ornata.api.exports.interop import glEnableVertexAttribArray

        glEnableVertexAttribArray(index)

    def disable_vertex_attrib_array(self, index: int) -> None:
        """Disable a vertex attribute array.

        Args:
            index: Attribute index to disable.
        """
        from ornata.api.exports.interop import glDisableVertexAttribArray

        glDisableVertexAttribArray(index)

    def set_vertex_attrib_divisor(self, index: int, divisor: int) -> None:
        """Set vertex attribute divisor for instancing.

        Args:
            index: Attribute index.
            divisor: Divisor value (0 = per vertex, 1 = per instance).
        """
        from ornata.api.exports.interop import glVertexAttribDivisor

        glVertexAttribDivisor(index, divisor)
