"""Index buffer object management for OpenGL."""

from ornata.api.exports.utils import get_logger

logger = get_logger(__name__)


class OpenGLIBOManager:
    """Manages OpenGL index buffer objects (IBOs)."""

    def __init__(self) -> None:
        """Initialize the IBO manager."""
        self._ibos: dict[str, int] = {}

    def create_ibo(self, name: str, indices: list[int]) -> int:
        """Create an index buffer object.

        Args:
            name: Unique name for the IBO.
            indices: List of index data.

        Returns:
            OpenGL IBO ID.
        """
        from ornata.api.exports.interop import GL_ELEMENT_ARRAY_BUFFER, GL_STATIC_DRAW, GLuintArray, glBindBuffer, glBufferData, glGenBuffers

        ibo_id = glGenBuffers(1)
        self._ibos[name] = ibo_id

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ibo_id)
        index_data = GLuintArray(indices)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, index_data, GL_STATIC_DRAW)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

        logger.debug(f"Created IBO {name} with {len(indices)} indices")
        return ibo_id

    def get_ibo(self, name: str) -> int | None:
        """Get an IBO by name.

        Args:
            name: Name of the IBO.

        Returns:
            OpenGL IBO ID or None if not found.
        """
        return self._ibos.get(name)

    def bind_ibo(self, ibo_id: int) -> None:
        """Bind an index buffer object.

        Args:
            ibo_id: OpenGL IBO ID to bind.
        """
        from ornata.api.exports.interop import GL_ELEMENT_ARRAY_BUFFER, glBindBuffer

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ibo_id)

    def unbind_ibo(self) -> None:
        """Unbind the current index buffer object."""
        from ornata.api.exports.interop import GL_ELEMENT_ARRAY_BUFFER, glBindBuffer

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

    def cleanup(self) -> None:
        """Clean up all IBOs."""
        from ornata.api.exports.interop import GL_ELEMENT_ARRAY_BUFFER, glBindBuffer

        for ibo_id in self._ibos.values():
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ibo_id)
        self._ibos.clear()

        logger.debug("IBO manager cleaned up")
