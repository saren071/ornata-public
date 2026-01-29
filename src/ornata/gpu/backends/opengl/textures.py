"""Texture operations for OpenGL (initially minimal)."""

from ornata.api.exports.utils import get_logger

logger = get_logger(__name__)


class OpenGLTextureManager:
    """Manages OpenGL texture operations (minimal implementation)."""

    def __init__(self) -> None:
        """Initialize the texture manager."""
        self._textures: dict[str, int] = {}

    def create_texture_2d(self, name: str, width: int, height: int, data: bytes | None = None) -> int:
        """Create a 2D texture.

        Args:
            name: Unique name for the texture.
            width: Texture width.
            height: Texture height.
            data: Optional texture data.

        Returns:
            OpenGL texture ID.
        """
        from ornata.api.exports.interop import GL_CLAMP_TO_EDGE, GL_LINEAR, GL_RGBA, GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_TEXTURE_MIN_FILTER, GL_TEXTURE_WRAP_S, GL_TEXTURE_WRAP_T, GL_UNSIGNED_BYTE, glBindTexture, glGenTextures, glTexImage2D, glTexParameteri

        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)

        # Set texture parameters
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

        # Upload texture data (placeholder - assumes RGBA format)
        if data:
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
        else:
            # Create empty texture
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)

        glBindTexture(GL_TEXTURE_2D, 0)

        self._textures[name] = texture_id
        logger.debug(f"Created texture: {name} ({width}x{height})")
        return texture_id

    def get_texture(self, name: str) -> int | None:
        """Get a texture by name.

        Args:
            name: Name of the texture.

        Returns:
            OpenGL texture ID or None if not found.
        """
        return self._textures.get(name)

    def bind_texture(self, texture_id: int, unit: int = 0) -> None:
        """Bind a texture to a texture unit.

        Args:
            texture_id: OpenGL texture ID to bind.
            unit: Texture unit to bind to.
        """
        from ornata.api.exports.interop import GL_TEXTURE0, GL_TEXTURE_2D, glActiveTexture, glBindTexture

        glActiveTexture(GL_TEXTURE0 + unit)
        glBindTexture(GL_TEXTURE_2D, texture_id)

    def unbind_texture(self, unit: int = 0) -> None:
        """Unbind texture from a texture unit.

        Args:
            unit: Texture unit to unbind from.
        """
        from ornata.api.exports.interop import GL_TEXTURE0, GL_TEXTURE_2D, glActiveTexture, glBindTexture

        glActiveTexture(GL_TEXTURE0 + unit)
        glBindTexture(GL_TEXTURE_2D, 0)

    def cleanup(self) -> None:
        """Clean up all textures."""
        from ornata.api.exports.interop import glDeleteTextures

        for texture_id in self._textures.values():
            glDeleteTextures(1, [texture_id])
        self._textures.clear()

        logger.debug("Texture manager cleaned up")
