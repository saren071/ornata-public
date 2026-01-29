"""Shader program management for OpenGL."""

from ornata.api.exports.utils import get_logger

logger = get_logger(__name__)


class OpenGLProgramManager:
    """Manages OpenGL shader programs."""

    def __init__(self) -> None:
        """Initialize the program manager."""
        self._programs: dict[str, int] = {}

    def create_program(self, name: str, vertex_src: str, fragment_src: str) -> int:
        """Create and link a shader program.

        Args:
            name: Unique name for the program.
            vertex_src: Vertex shader source code.
            fragment_src: Fragment shader source code.

        Returns:
            OpenGL program ID.

        Raises:
            RuntimeError: If program creation or linking fails.
        """
        from ornata.api.exports.interop import (
            GL_COMPILE_STATUS,
            GL_FRAGMENT_SHADER,
            GL_LINK_STATUS,
            GL_VERTEX_SHADER,
            glAttachShader,
            glCompileShader,
            glCreateProgram,
            glCreateShader,
            glDeleteProgram,
            glDeleteShader,
            glDetachShader,
            glGetProgramInfoLog,
            glGetProgramiv,
            glGetShaderInfoLog,
            glGetShaderiv,
            glLinkProgram,
            glShaderSource,
        )

        # Create vertex shader
        vertex_shader = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vertex_shader, vertex_src)
        glCompileShader(vertex_shader)

        # Check vertex shader compilation
        if not glGetShaderiv(vertex_shader, GL_COMPILE_STATUS):
            error = glGetShaderInfoLog(vertex_shader)
            glDeleteShader(vertex_shader)
            raise RuntimeError(f"Vertex shader compilation failed: {error}")

        # Create fragment shader
        fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fragment_shader, fragment_src)
        glCompileShader(fragment_shader)

        # Check fragment shader compilation
        if not glGetShaderiv(fragment_shader, GL_COMPILE_STATUS):
            error = glGetShaderInfoLog(fragment_shader)
            glDeleteShader(vertex_shader)
            glDeleteShader(fragment_shader)
            raise RuntimeError(f"Fragment shader compilation failed: {error}")

        # Create and link program
        program = glCreateProgram()
        glAttachShader(program, vertex_shader)
        glAttachShader(program, fragment_shader)
        glLinkProgram(program)

        # Check program linking
        if not glGetProgramiv(program, GL_LINK_STATUS):
            error = glGetProgramInfoLog(program)
            glDeleteProgram(program)
            glDeleteShader(vertex_shader)
            glDeleteShader(fragment_shader)
            raise RuntimeError(f"Shader program linking failed: {error}")

        # Clean up shaders (they're linked into the program now)
        glDetachShader(program, vertex_shader)
        glDetachShader(program, fragment_shader)
        glDeleteShader(vertex_shader)
        glDeleteShader(fragment_shader)

        # Store program
        self._programs[name] = program

        logger.debug(f"Created OpenGL program: {name}")
        return program

    def get_program(self, name: str) -> int | None:
        """Get a program by name.

        Args:
            name: Name of the program.

        Returns:
            OpenGL program ID or None if not found.
        """
        return self._programs.get(name)

    def use_program(self, program_id: int) -> None:
        """Use a shader program.

        Args:
            program_id: OpenGL program ID to use.
        """
        from ornata.api.exports.interop import glUseProgram

        glUseProgram(program_id)

    def unbind_program(self) -> None:
        """Unbind the current shader program."""
        from ornata.api.exports.interop import glUseProgram

        glUseProgram(0)

    def cleanup(self) -> None:
        """Clean up all programs."""
        from ornata.api.exports.interop import glDeleteProgram

        for program_id in self._programs.values():
            glDeleteProgram(program_id)
        self._programs.clear()

        logger.debug("Program manager cleaned up")
