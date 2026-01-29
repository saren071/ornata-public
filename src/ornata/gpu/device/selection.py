"""Automatic backend detection and selection for GPU acceleration."""

from __future__ import annotations

import platform
from typing import TYPE_CHECKING

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.gpu.misc import GPUBackend

logger = get_logger(__name__)


class DeviceSelector:
    """REQUIRED: Automatic backend detection and selection for GPU acceleration."""

    def select_backend(self) -> GPUBackend | None:
        """CRITICAL: Complete backend detection logic for the current platform.

        Returns:
            The best available GPU backend instance, or None if none available.
        """
        system = platform.system()
        logger.info(f"Starting backend selection for platform: {system}")
        
        if system == "Windows":
            return self._select_windows_backend()
        else:
            return self._select_fallback_backend()

    def _select_windows_backend(self) -> GPUBackend | None:
        """REQUIRED: Windows backend selection with DirectX -> OpenGL -> CPU fallback."""
        # 1. Try DirectX first
        try:
            logger.debug("Attempting to import DirectX backend...")
            from ornata.gpu.backends.directx.backend import DirectXBackend

            logger.debug("Creating DirectX backend instance...")
            backend = DirectXBackend()
            logger.debug("Checking DirectX backend availability...")
            if backend.is_available():
                logger.info("Selected DirectX backend for Windows")
                return backend
            else:
                logger.debug("DirectX backend not available (is_available() returned False)")
        except (ImportError, Exception) as e:
            logger.warning(f"DirectX backend not available: {e}")

        # 2. Fallback to OpenGL
        try:
            from ornata.gpu.backends.opengl.backend import OpenGLBackend

            backend = OpenGLBackend()
            if backend.is_available():
                logger.info("Selected OpenGL backend for Windows")
                return backend
        except (ImportError, Exception) as e:
            logger.debug(f"OpenGL backend not available: {e}")

        # 3. Fallback to CPU
        logger.warning("All GPU backends failed on Windows - falling back to CPU")
        return self._select_fallback_backend()

    def _select_fallback_backend(self) -> GPUBackend | None:
        """REQUIRED: CPU fallback backend selection when all GPU backends fail."""
        try:
            logger.debug("Attempting to import CPU fallback backend...")
            from ornata.gpu.fallback.cpu_fallback import CPUFallback

            backend = CPUFallback()
            if backend.is_available():
                logger.info("Selected CPU fallback backend")
                return backend
        except (ImportError, Exception) as e:
            logger.error(f"CPU fallback backend not available: {e}")

        logger.error("No backend available - all GPU and CPU fallback options failed")
        return None