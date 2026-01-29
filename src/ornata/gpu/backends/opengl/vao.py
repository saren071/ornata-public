"""Vertex array object management for OpenGL."""

from typing import TYPE_CHECKING

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.definitions import Geometry

logger = get_logger(__name__)


class OpenGLVAOManager:
    """Manages OpenGL vertex array objects (VAOs)."""

    def __init__(self) -> None:
        """Initialize the VAO manager."""
        self._vaos: dict[str, int] = {}

    def get_or_create_vao(self, geometry: Geometry, shader_name: str) -> int:
        """Get or create a VAO for the given geometry and shader combination.

        Args:
            geometry: The geometry data.
            shader_name: Name of the shader program.

        Returns:
            OpenGL VAO ID.
        """
        vao_key = f"{shader_name}_geometry"
        if vao_key not in self._vaos:
            self._vaos[vao_key] = self._create_vao(geometry, vao_key)
        return self._vaos[vao_key]

    def _create_vao(self, geometry: Geometry, vao_key: str) -> int:
        """Create a new VAO for the geometry.

        Args:
            geometry: The geometry data.
            vao_key: Unique key for the VAO.

        Returns:
            OpenGL VAO ID.
        """
        from ornata.api.exports.interop import glBindVertexArray, glGenVertexArrays

        vao_id = glGenVertexArrays(1)
        glBindVertexArray(vao_id)

        # Note: VBO setup is handled by VBOManager
        # This VAO just tracks the binding

        glBindVertexArray(0)

        logger.debug(f"Created VAO {vao_key}")
        return vao_id

    def bind_vao(self, vao_id: int) -> None:
        """Bind a vertex array object.

        Args:
            vao_id: OpenGL VAO ID to bind.
        """
        from ornata.api.exports.interop import glBindVertexArray

        glBindVertexArray(vao_id)

    def unbind_vao(self) -> None:
        """Unbind the current vertex array object."""
        from ornata.api.exports.interop import glBindVertexArray

        glBindVertexArray(0)

    def setup_index_data(self, vao_id: int, geometry: Geometry) -> None:
        """Set up index buffer for a VAO.

        Args:
            vao_id: OpenGL VAO ID.
            geometry: The geometry containing index data.
        """
        if not geometry.indices:
            return

        from ornata.api.exports.interop import GL_ELEMENT_ARRAY_BUFFER, GL_STATIC_DRAW, GLuintArray, glBindBuffer, glBindVertexArray, glBufferData, glGenBuffers

        # Bind the VAO first
        glBindVertexArray(vao_id)

        # Create and setup IBO
        ibo_id = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ibo_id)
        index_data = GLuintArray(geometry.indices)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, index_data, GL_STATIC_DRAW)

        # Note: IBO is automatically unbound when VAO is unbound
        glBindVertexArray(0)

    def draw_arrays(self, vertex_count: int) -> None:
        """Draw arrays using the current VAO.

        Args:
            vertex_count: Number of vertices to draw.
        """
        from ornata.api.exports.interop import GL_TRIANGLES, glDrawArrays

        glDrawArrays(GL_TRIANGLES, 0, vertex_count)

    def draw_indexed(self, index_count: int) -> None:
        """Draw indexed geometry using the current VAO.

        Args:
            index_count: Number of indices to draw.
        """
        from ornata.api.exports.interop import GL_TRIANGLES, GL_UNSIGNED_INT, glDrawElements

        glDrawElements(GL_TRIANGLES, index_count, GL_UNSIGNED_INT, None)

    def cleanup(self) -> None:
        """Clean up all VAOs."""
        from ornata.api.exports.interop import glDeleteVertexArrays

        for vao_id in self._vaos.values():
            glDeleteVertexArrays(1, [vao_id])
        self._vaos.clear()

        logger.debug("VAO manager cleaned up")
