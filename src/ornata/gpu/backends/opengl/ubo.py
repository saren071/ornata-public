"""Uniform buffer objects for OpenGL (initially minimal)."""

from ornata.api.exports.utils import get_logger

logger = get_logger(__name__)


class OpenGLUBOManager:
    """Manages OpenGL uniform buffer objects (minimal implementation)."""

    def __init__(self) -> None:
        """Initialize the UBO manager."""
        self._ubos: dict[str, int] = {}

    def create_ubo(self, name: str, size: int, data: bytes | None = None) -> int:
        """Create a uniform buffer object.

        Args:
            name: Unique name for the UBO.
            size: Size of the buffer in bytes.
            data: Optional initial data.

        Returns:
            OpenGL UBO ID.
        """
        from ornata.api.exports.interop import GL_DYNAMIC_DRAW, GL_UNIFORM_BUFFER, glBindBuffer, glBufferData, glGenBuffers

        ubo_id = glGenBuffers(1)
        glBindBuffer(GL_UNIFORM_BUFFER, ubo_id)

        if data:
            glBufferData(GL_UNIFORM_BUFFER, data, GL_DYNAMIC_DRAW)
        else:
            # Create empty buffer
            glBufferData(GL_UNIFORM_BUFFER, size, None, GL_DYNAMIC_DRAW)

        glBindBuffer(GL_UNIFORM_BUFFER, 0)

        self._ubos[name] = ubo_id
        logger.debug(f"Created UBO: {name} ({size} bytes)")
        return ubo_id

    def get_ubo(self, name: str) -> int | None:
        """Get a UBO by name.

        Args:
            name: Name of the UBO.

        Returns:
            OpenGL UBO ID or None if not found.
        """
        return self._ubos.get(name)

    def bind_ubo(self, ubo_id: int, binding_point: int) -> None:
        """Bind a UBO to a binding point.

        Args:
            ubo_id: OpenGL UBO ID to bind.
            binding_point: Binding point index.
        """
        from ornata.api.exports.interop import GL_UNIFORM_BUFFER, glBindBufferBase

        glBindBufferBase(GL_UNIFORM_BUFFER, binding_point, ubo_id)

    def update_ubo_data(self, ubo_id: int, data: bytes, offset: int = 0) -> None:
        """Update UBO data.

        Args:
            ubo_id: OpenGL UBO ID.
            data: New data to upload.
            offset: Offset in bytes from start of buffer.
        """
        from ornata.api.exports.interop import GL_UNIFORM_BUFFER, glBindBuffer, glBufferSubData

        glBindBuffer(GL_UNIFORM_BUFFER, ubo_id)
        glBufferSubData(GL_UNIFORM_BUFFER, offset, data)
        glBindBuffer(GL_UNIFORM_BUFFER, 0)

    def cleanup(self) -> None:
        """Clean up all UBOs."""
        from ornata.api.exports.interop import glDeleteBuffers

        for ubo_id in self._ubos.values():
            glDeleteBuffers(1, [ubo_id])
        self._ubos.clear()

        logger.debug("UBO manager cleaned up")
