"""Vertex buffer object management for OpenGL."""

from typing import TYPE_CHECKING

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.definitions import Geometry

logger = get_logger(__name__)


class OpenGLVBOManager:
    """Manages OpenGL vertex buffer objects (VBOs)."""

    def __init__(self) -> None:
        """Initialize the VBO manager."""
        self._vbos: dict[str, int] = {}

    def setup_vertex_data(self, vao_id: int, geometry: Geometry) -> None:
        """Set up vertex buffer data for a VAO.

        Args:
            vao_id: OpenGL VAO ID to set up.
            geometry: The geometry containing vertex data.
        """
        import ctypes

        from ornata.api.exports.interop import GL_ARRAY_BUFFER, GL_FALSE, GL_FLOAT, GL_STATIC_DRAW, glBindBuffer, glBindVertexArray, glBufferData, glEnableVertexAttribArray, glfloatArray, glGenBuffers, glVertexAttribPointer

        # Bind the VAO first
        glBindVertexArray(vao_id)

        # Create and setup VBO for vertex data
        vbo_key = f"vao_{vao_id}_vertices"
        vbo_id = glGenBuffers(1)
        self._vbos[vbo_key] = vbo_id

        glBindBuffer(GL_ARRAY_BUFFER, vbo_id)
        vertex_data = glfloatArray(geometry.vertices)
        glBufferData(GL_ARRAY_BUFFER, vertex_data, GL_STATIC_DRAW)

        # Set up vertex attributes
        # Position attribute (location 0) - first 3 floats
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * 4, None)

        # Texture coordinate attribute (location 1) - next 2 floats
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * 4, ctypes.c_void_p(3 * 4))

        # Unbind VBO (VAO keeps the binding)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

        logger.debug(f"Set up vertex data for VAO {vao_id} with {len(geometry.vertices)} vertices")

    def get_vbo(self, name: str) -> int | None:
        """Get a VBO by name.

        Args:
            name: Name of the VBO.

        Returns:
            OpenGL VBO ID or None if not found.
        """
        return self._vbos.get(name)

    def bind_vbo(self, vbo_id: int) -> None:
        """Bind a vertex buffer object.

        Args:
            vbo_id: OpenGL VBO ID to bind.
        """
        from ornata.api.exports.interop import GL_ARRAY_BUFFER, glBindBuffer

        glBindBuffer(GL_ARRAY_BUFFER, vbo_id)

    def unbind_vbo(self) -> None:
        """Unbind the current vertex buffer object."""
        from ornata.api.exports.interop import GL_ARRAY_BUFFER, glBindBuffer

        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def update_vertex_data(self, vbo_id: int, data: list[float]) -> None:
        """Update vertex buffer data.

        Args:
            vbo_id: OpenGL VBO ID.
            data: New vertex data.
        """
        from ornata.api.exports.interop import GL_ARRAY_BUFFER, glBindBuffer, glBufferSubData, glfloatArray

        glBindBuffer(GL_ARRAY_BUFFER, vbo_id)
        vertex_data = glfloatArray(data)
        glBufferSubData(GL_ARRAY_BUFFER, 0, vertex_data)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def cleanup(self) -> None:
        """Clean up all VBOs."""
        from ornata.api.exports.interop import GL_ARRAY_BUFFER, glBindBuffer, glDeleteBuffers

        for vbo_id in self._vbos.values():
            glBindBuffer(GL_ARRAY_BUFFER, vbo_id)
            glDeleteBuffers(1, [vbo_id])
        self._vbos.clear()

        logger.debug("VBO manager cleaned up")
