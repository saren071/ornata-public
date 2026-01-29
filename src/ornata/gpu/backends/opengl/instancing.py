"""Instanced rendering logic for OpenGL."""

from typing import TYPE_CHECKING

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.definitions import Geometry

logger = get_logger(__name__)


class OpenGLInstancingManager:
    """Manages OpenGL instanced rendering operations."""

    def __init__(self) -> None:
        """Initialize the instancing manager."""
        self._instance_vbos: dict[str, int] = {}

    def setup_instanced_vao(self, geometry: Geometry, shader_name: str, instance_data: list[float]) -> int:
        """Set up a VAO for instanced rendering.

        Args:
            geometry: The base geometry to instance.
            shader_name: Name of the shader program.
            instance_data: Flattened list of instance transform data.

        Returns:
            OpenGL VAO ID.
        """
        import ctypes

        from ornata.api.exports.interop import (
            GL_ARRAY_BUFFER,
            GL_DYNAMIC_DRAW,
            GL_ELEMENT_ARRAY_BUFFER,
            GL_FALSE,
            GL_FLOAT,
            GL_STATIC_DRAW,
            GLuintArray,
            glBindBuffer,
            glBindVertexArray,
            glBufferData,
            glEnableVertexAttribArray,
            glfloatArray,
            glGenBuffers,
            glGenVertexArrays,
            glVertexAttribDivisor,
            glVertexAttribPointer,
        )

        vao_key = f"{shader_name}_instanced"
        vao_id = glGenVertexArrays(1)

        glBindVertexArray(vao_id)

        # Create and setup VBO for vertex data
        vbo_id = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo_id)
        vertex_data = glfloatArray(geometry.vertices)
        glBufferData(GL_ARRAY_BUFFER, vertex_data, GL_STATIC_DRAW)

        # Set up vertex attributes (position and texcoord)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * 4, None)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * 4, ctypes.c_void_p(3 * 4))

        # Create and setup VBO for instance data (transforms)
        instance_vbo_id = glGenBuffers(1)
        self._instance_vbos[vao_key] = instance_vbo_id

        glBindBuffer(GL_ARRAY_BUFFER, instance_vbo_id)
        instance_data_array = glfloatArray(instance_data)
        glBufferData(GL_ARRAY_BUFFER, instance_data_array, GL_DYNAMIC_DRAW)

        # Set up instance attributes (location 2-6: x, y, scale_x, scale_y, rotation)
        for i in range(5):
            glEnableVertexAttribArray(2 + i)
            glVertexAttribPointer(2 + i, 1, GL_FLOAT, GL_FALSE, 5 * 4, ctypes.c_void_p(i * 4))
            glVertexAttribDivisor(2 + i, 1)  # Advance per instance

        # Create and setup IBO for index data if present
        if geometry.indices:
            ibo_id = glGenBuffers(1)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ibo_id)
            index_data = GLuintArray(geometry.indices)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, index_data, GL_STATIC_DRAW)

        glBindVertexArray(0)

        logger.debug(f"Set up instanced VAO {vao_key} with {len(geometry.vertices)} vertices")
        return vao_id

    def update_instance_data(self, vao_key: str, instance_data: list[float]) -> None:
        """Update instance data for an existing VAO.

        Args:
            vao_key: Key identifying the VAO.
            instance_data: New instance data.
        """
        from ornata.api.exports.interop import GL_ARRAY_BUFFER, glBindBuffer, glBufferSubData, glfloatArray

        instance_vbo_id = self._instance_vbos.get(vao_key)
        if instance_vbo_id is None:
            raise ValueError(f"No instance VBO found for VAO key {vao_key}")

        glBindBuffer(GL_ARRAY_BUFFER, instance_vbo_id)
        instance_data_array = glfloatArray(instance_data)
        glBufferSubData(GL_ARRAY_BUFFER, 0, instance_data_array)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def render_instances(self, vao_id: int, geometry: Geometry, instance_count: int) -> None:
        """Render instances using the specified VAO.

        Args:
            vao_id: OpenGL VAO ID to use for rendering.
            geometry: The geometry being rendered.
            instance_count: Number of instances to render.
        """
        from ornata.api.exports.interop import GL_TRIANGLES, GL_UNSIGNED_INT, glDrawArraysInstanced, glDrawElementsInstanced

        if geometry.indices:
            glDrawElementsInstanced(GL_TRIANGLES, geometry.index_count, GL_UNSIGNED_INT, None, instance_count)
        else:
            glDrawArraysInstanced(GL_TRIANGLES, 0, geometry.vertex_count, instance_count)

    def cleanup(self) -> None:
        """Clean up instance VBOs."""
        from ornata.api.exports.interop import GL_ELEMENT_ARRAY_BUFFER, glBindBuffer

        for instance_vbo_id in self._instance_vbos.values():
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, instance_vbo_id)
        self._instance_vbos.clear()

        logger.debug("Instancing manager cleaned up")
