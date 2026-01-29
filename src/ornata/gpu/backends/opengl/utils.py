"""Utility functions and helpers for OpenGL."""

from ornata.api.exports.utils import get_logger

logger = get_logger(__name__)


def check_opengl_error() -> str | None:
    """Check for OpenGL errors and return error message if any.

    Returns:
        Error message string or None if no error.
    """
    from ornata.api.exports.interop import (
        GL_INVALID_ENUM,
        GL_INVALID_FRAMEBUFFER_OPERATION,
        GL_INVALID_OPERATION,
        GL_INVALID_VALUE,
        GL_NO_ERROR,
        GL_OUT_OF_MEMORY,
        GL_STACK_OVERFLOW,
        GL_STACK_UNDERFLOW,
        glGetError,
    )

    error = glGetError()
    if error == GL_NO_ERROR:
        return None

    error_messages = {
        GL_INVALID_ENUM: "GL_INVALID_ENUM",
        GL_INVALID_VALUE: "GL_INVALID_VALUE",
        GL_INVALID_OPERATION: "GL_INVALID_OPERATION",
        GL_INVALID_FRAMEBUFFER_OPERATION: "GL_INVALID_FRAMEBUFFER_OPERATION",
        GL_OUT_OF_MEMORY: "GL_OUT_OF_MEMORY",
        GL_STACK_UNDERFLOW: "GL_STACK_UNDERFLOW",
        GL_STACK_OVERFLOW: "GL_STACK_OVERFLOW",
    }

    return error_messages.get(error, f"Unknown OpenGL error: {error}")


def get_opengl_version() -> tuple[int, int]:
    """Get the current OpenGL version.

    Returns:
        Tuple of (major, minor) version numbers.
    """
    from ornata.api.exports.interop import GL_VERSION, glGetString

    version_str = glGetString(GL_VERSION).decode('utf-8', errors='ignore')
    try:
        major, minor = map(int, version_str.split('.')[0:2])
        return (major, minor)
    except (ValueError, IndexError):
        logger.warning(f"Failed to parse OpenGL version string: {version_str}")
        return (0, 0)


def get_opengl_extensions() -> set[str]:
    """Get the list of supported OpenGL extensions.

    Returns:
        Set of extension names.
    """
    from ornata.api.exports.interop import GL_EXTENSIONS, glGetString

    extensions_str = glGetString(GL_EXTENSIONS).decode('utf-8', errors='ignore')
    return set(extensions_str.split())


def has_opengl_extension(extension: str) -> bool:
    """Check if a specific OpenGL extension is supported.

    Args:
        extension: Extension name to check.

    Returns:
        True if extension is supported, False otherwise.
    """
    return extension in get_opengl_extensions()


def get_max_texture_size() -> int:
    """Get the maximum texture size supported by OpenGL.

    Returns:
        Maximum texture size in pixels.
    """
    from ornata.api.exports.interop import GL_MAX_TEXTURE_SIZE, glGetIntegerv

    max_size = glGetIntegerv(GL_MAX_TEXTURE_SIZE)
    return max_size[0] if isinstance(max_size, (list, tuple)) else max_size


def get_max_viewport_dims() -> tuple[int, int]:
    """Get the maximum viewport dimensions.

    Returns:
        Tuple of (width, height) maximum viewport size.
    """
    from ornata.api.exports.interop import GL_MAX_VIEWPORT_DIMS, glGetIntegerv

    dims = glGetIntegerv(GL_MAX_VIEWPORT_DIMS)
    return (dims[0], dims[1]) if len(dims) >= 2 else (0, 0)


def log_opengl_info() -> None:
    """Log OpenGL implementation information."""
    from ornata.api.exports.interop import GL_RENDERER, GL_VENDOR, glGetString

    version = get_opengl_version()
    vendor = glGetString(GL_VENDOR).decode('utf-8', errors='ignore')
    renderer = glGetString(GL_RENDERER).decode('utf-8', errors='ignore')
    extensions = get_opengl_extensions()

    logger.info(f"OpenGL Version: {version[0]}.{version[1]}")
    logger.info(f"OpenGL Vendor: {vendor}")
    logger.info(f"OpenGL Renderer: {renderer}")
    logger.info(f"OpenGL Extensions: {len(extensions)} available")

    # Log some key extensions
    key_extensions = [
        'GL_ARB_instanced_arrays',
        'GL_ARB_vertex_array_object',
        'GL_ARB_framebuffer_object',
        'GL_ARB_uniform_buffer_object',
    ]

    for ext in key_extensions:
        status = "supported" if ext in extensions else "not supported"
        logger.debug(f"  {ext}: {status}")