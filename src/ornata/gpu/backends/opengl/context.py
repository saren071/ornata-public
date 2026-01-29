"""OpenGL context management and initialization."""

import threading
from typing import Any

from ornata.api.exports.utils import get_logger

logger = get_logger(__name__)


class OpenGLContextManager:
    """Manages OpenGL context initialization and availability checking."""

    def __init__(self) -> None:
        """Initialize the context manager."""
        self._initialized = False
        self._context: Any = None
        self._lock = threading.RLock()

    def is_available(self) -> bool:
        """Check if OpenGL is available on this system.

        Returns:
            True if OpenGL 3.3+ is available, False otherwise.
        """
        try:
            import importlib.util

            return importlib.util.find_spec("OpenGL.GL") is not None
        except Exception:
            return False

    def supports_instancing(self) -> bool:
        """Check if OpenGL instancing is supported.

        Returns:
            True if instancing is supported (OpenGL 3.3+), False otherwise.
        """
        if not self.is_available():
            return False

        try:
            self.ensure_initialized()

            from ornata.api.exports.interop import GL_EXTENSIONS, GL_VERSION, glGetString

            # Get OpenGL version
            version_str = glGetString(GL_VERSION).decode("utf-8", errors="ignore")
            major, minor = map(int, version_str.split(".")[0:2])

            # Instancing requires OpenGL 3.3+
            if major > 3 or (major == 3 and minor >= 3):
                return True

            # Check for ARB_instanced_arrays extension as fallback
            extensions = glGetString(GL_EXTENSIONS).decode("utf-8", errors="ignore")
            return "GL_ARB_instanced_arrays" in extensions

        except Exception:
            return False

    def ensure_initialized(self) -> None:
        """Ensure OpenGL context is initialized.

        Raises:
            RuntimeError: If OpenGL initialization fails.
        """
        if not self._initialized:
            try:
                from ornata.api.exports.interop import GL_BLEND, GL_DEPTH_TEST, GL_ONE_MINUS_SRC_ALPHA, GL_SRC_ALPHA, GL_VERSION, glBlendFunc, glEnable, glGetString

                # Verify a current context exists by probing version string first
                version_bytes = glGetString(GL_VERSION)
                if not version_bytes:
                    raise RuntimeError("No current OpenGL context")
                version = version_bytes.decode("utf-8", errors="ignore")

                # Enable necessary OpenGL features
                glEnable(GL_DEPTH_TEST)
                glEnable(GL_BLEND)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

                logger.debug(f"Initialized OpenGL {version}")
                self._initialized = True

            except Exception as e:
                logger.error(f"Failed to initialize OpenGL context: {e}")
                raise RuntimeError(f"Failed to initialize OpenGL context: {e}") from e

    def cleanup(self) -> None:
        """Clean up OpenGL context resources."""
        with self._lock:
            self._initialized = False
            logger.debug("OpenGL context cleaned up")
