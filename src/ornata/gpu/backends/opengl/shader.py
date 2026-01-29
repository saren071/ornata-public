"""Individual shader compilation for OpenGL."""

from ornata.api.exports.utils import get_logger

logger = get_logger(__name__)


class OpenGLShaderCompiler:
    """Compiles individual OpenGL shaders."""

    def __init__(self) -> None:
        """Initialize the shader compiler."""
        self._shaders: dict[str, int] = {}

    def compile_vertex_shader(self, name: str, source: str) -> int:
        """Compile a vertex shader.

        Args:
            name: Unique name for the shader.
            source: GLSL source code.

        Returns:
            OpenGL shader ID.

        Raises:
            RuntimeError: If compilation fails.
        """
        from ornata.api.exports.interop import GL_COMPILE_STATUS, GL_VERTEX_SHADER, glCompileShader, glCreateShader, glDeleteShader, glGetShaderInfoLog, glGetShaderiv, glShaderSource

        shader_id = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(shader_id, source)
        glCompileShader(shader_id)

        if not glGetShaderiv(shader_id, GL_COMPILE_STATUS):
            error = glGetShaderInfoLog(shader_id)
            glDeleteShader(shader_id)
            raise RuntimeError(f"Vertex shader compilation failed: {error}")

        self._shaders[name] = shader_id
        logger.debug(f"Compiled vertex shader: {name}")
        return shader_id

    def compile_fragment_shader(self, name: str, source: str) -> int:
        """Compile a fragment shader.

        Args:
            name: Unique name for the shader.
            source: GLSL source code.

        Returns:
            OpenGL shader ID.

        Raises:
            RuntimeError: If compilation fails.
        """
        from ornata.api.exports.interop import GL_COMPILE_STATUS, GL_FRAGMENT_SHADER, glCompileShader, glCreateShader, glDeleteShader, glGetShaderInfoLog, glGetShaderiv, glShaderSource

        shader_id = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(shader_id, source)
        glCompileShader(shader_id)

        if not glGetShaderiv(shader_id, GL_COMPILE_STATUS):
            error = glGetShaderInfoLog(shader_id)
            glDeleteShader(shader_id)
            raise RuntimeError(f"Fragment shader compilation failed: {error}")

        self._shaders[name] = shader_id
        logger.debug(f"Compiled fragment shader: {name}")
        return shader_id

    def get_shader(self, name: str) -> int | None:
        """Get a shader by name.

        Args:
            name: Name of the shader.

        Returns:
            OpenGL shader ID or None if not found.
        """
        return self._shaders.get(name)

    def cleanup(self) -> None:
        """Clean up all shaders."""
        from ornata.api.exports.interop import glDeleteShader

        for shader_id in self._shaders.values():
            glDeleteShader(shader_id)
        self._shaders.clear()

        logger.debug("Shader compiler cleaned up")
