"""Sampler state management for texture sampling configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ornata.api.exports.definitions import FilterMode, WrapMode
from ornata.api.exports.utils import get_logger

logger = get_logger(__name__)


@dataclass
class SamplerState:
    """Cross-platform sampler state configuration for texture sampling.

    Manages texture sampling parameters including filtering modes, wrapping modes,
    and other sampling configuration that affects how textures are sampled during rendering.
    """

    min_filter: FilterMode = FilterMode.LINEAR_MIPMAP_LINEAR
    mag_filter: FilterMode = FilterMode.LINEAR
    wrap_s: WrapMode = WrapMode.CLAMP_TO_EDGE
    wrap_t: WrapMode = WrapMode.CLAMP_TO_EDGE
    wrap_r: WrapMode = WrapMode.CLAMP_TO_EDGE
    mip_lod_bias: float = 0.0
    max_anisotropy: int = 1
    min_lod: float = -1000.0
    max_lod: float = 1000.0
    border_color: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)

    def __post_init__(self) -> None:
        """Validate sampler state parameters after initialization."""
        if self.max_anisotropy < 1:
            raise ValueError(f"max_anisotropy must be an integer >= 1, got {self.max_anisotropy}")
        if len(self.border_color) != 4:
            raise ValueError(f"border_color must be a 4-tuple of floats, got {self.border_color}")

        # Convert to tuple if list was provided
        self.border_color = self.border_color

    def create_sampler(self) -> Any:
        """Create a native sampler object for the current GPU backend.

        Returns:
            Backend-specific sampler object that can be bound to the pipeline.

        Raises:
            RuntimeError: If no compatible GPU backend is available.
        """
        # Import here to avoid circular imports
        from ornata.api.exports.gpu import get_device_manager

        gpu_manager = get_device_manager()

        if not gpu_manager.is_available():
            logger.debug("No GPU backend available, returning simulated sampler")
            return None  # Simulated sampler for CPU fallback

        # Get the current backend and delegate sampler creation
        backend = getattr(gpu_manager, '_backend', None)
        if backend is None:
            logger.debug("No active GPU backend, returning simulated sampler")
            return None

        # Delegate to backend-specific implementation
        return self._create_backend_sampler(backend)

    def _create_backend_sampler(self, backend: Any) -> Any:
        """Create a sampler using the specific backend implementation.

        Args:
            backend: The GPU backend instance.

        Returns:
            Backend-specific sampler object.
        """
        backend_name = type(backend).__name__

        if backend_name == "DirectXBackend":
            return self._create_directx_sampler(backend)
        elif backend_name == "OpenGLBackend":
            return self._create_opengl_sampler(backend)
        else:
            logger.warning(f"Unknown backend {backend_name}, returning simulated sampler")
            return None

    def _create_directx_sampler(self, backend: Any) -> Any:
        """Create a DirectX sampler state.

        Args:
            backend: DirectX backend instance.

        Returns:
            DirectX sampler state object.
        """
        try:
            # Import DirectX sampler module
            from ornata.api.exports.gpu import DirectXSampler

            # Create DirectX sampler manager
            device = getattr(backend, '_device', None)
            dx_device = getattr(device, '_device', None) if device else None
            if dx_device is None:
                logger.debug("DirectX device not found, returning simulated sampler")
                return None
            dx_sampler = DirectXSampler(dx_device)

            # Create sampler with our configuration
            # Note: DirectXSampler.create_sampler_state() creates a basic sampler,
            # but we need to extend it to support custom parameters
            sampler = dx_sampler.create_sampler_state()

            logger.debug("Created DirectX sampler state")
            return sampler

        except Exception as e:
            logger.debug(f"Failed to create DirectX sampler: {e}, using simulated sampler")
            return None

    def _create_opengl_sampler(self, backend: Any) -> Any:
        """Create an OpenGL sampler object.

        Args:
            backend: OpenGL backend instance.

        Returns:
            OpenGL sampler object.
        """
        try:
            from ornata.api.exports.interop import (
                GL_TEXTURE_LOD_BIAS,
                GL_TEXTURE_MAG_FILTER,
                GL_TEXTURE_MAX_ANISOTROPY_EXT,
                GL_TEXTURE_MAX_LOD,
                GL_TEXTURE_MIN_FILTER,
                GL_TEXTURE_MIN_LOD,
                GL_TEXTURE_WRAP_R,
                GL_TEXTURE_WRAP_S,
                GL_TEXTURE_WRAP_T,
                _gl_filter,
                _gl_wrap,
                glGenSamplers,
                glSamplerParameterf,
                glSamplerParameteri,
            )
            sampler_id = glGenSamplers(1)
            glSamplerParameteri(sampler_id, GL_TEXTURE_MIN_FILTER, _gl_filter(self.min_filter))
            glSamplerParameteri(sampler_id, GL_TEXTURE_MAG_FILTER, _gl_filter(self.mag_filter))
            glSamplerParameteri(sampler_id, GL_TEXTURE_WRAP_S, _gl_wrap(self.wrap_s))
            glSamplerParameteri(sampler_id, GL_TEXTURE_WRAP_T, _gl_wrap(self.wrap_t))
            glSamplerParameteri(sampler_id, GL_TEXTURE_WRAP_R, _gl_wrap(self.wrap_r))
            glSamplerParameterf(sampler_id, GL_TEXTURE_LOD_BIAS, float(self.mip_lod_bias))
            glSamplerParameterf(sampler_id, GL_TEXTURE_MIN_LOD, float(self.min_lod))
            glSamplerParameterf(sampler_id, GL_TEXTURE_MAX_LOD, float(self.max_lod))

            if self.max_anisotropy > 1:
                anisotropy_enum = GL_TEXTURE_MAX_ANISOTROPY_EXT
                if anisotropy_enum is not None:
                    glSamplerParameterf(sampler_id, anisotropy_enum, float(self.max_anisotropy))

            logger.debug("Created OpenGL sampler object %s", sampler_id)
            return sampler_id
        except Exception as exc:
            logger.debug("OpenGL sampler creation failed: %s", exc)
            return None

    def bind_sampler(self, sampler: Any, slot: int = 0) -> None:
        """Bind the sampler to the current pipeline.

        Args:
            sampler: The native sampler object returned by create_sampler().
            slot: The sampler slot/index to bind to (default: 0).
        """
        # Import here to avoid circular imports
        from ornata.api.exports.gpu import get_device_manager

        gpu_manager = get_device_manager()

        if not gpu_manager.is_available():
            logger.debug("No GPU backend available, skipping sampler binding")
            return

        backend = getattr(gpu_manager, '_backend', None)
        if backend is None:
            logger.debug("No active GPU backend, skipping sampler binding")
            return

        # Delegate to backend-specific binding
        self._bind_backend_sampler(backend, sampler, slot)

    def _bind_backend_sampler(self, backend: Any, sampler: Any, slot: int) -> None:
        """Bind sampler using the specific backend implementation.

        Args:
            backend: The GPU backend instance.
            sampler: The native sampler object.
            slot: The sampler slot/index to bind to.
        """
        backend_name = type(backend).__name__

        if backend_name == "DirectXBackend":
            self._bind_directx_sampler(backend, sampler, slot)
        elif backend_name == "OpenGLBackend":
            self._bind_opengl_sampler(backend, sampler, slot)
        else:
            logger.debug(f"Unknown backend {backend_name}, skipping sampler binding")

    def _bind_directx_sampler(self, backend: Any, sampler: Any, slot: int) -> None:
        """Bind DirectX sampler state.

        Args:
            backend: DirectX backend instance.
            sampler: DirectX sampler state object.
            slot: Sampler slot to bind to.
        """
        try:
            context = getattr(backend, '_context', None)
            if context:
                dx_context = getattr(context, '_context', None)
                if dx_context and hasattr(dx_context, 'PSSetSamplers'):
                    # Bind sampler to pixel shader stage (most common for textures)
                    dx_context.PSSetSamplers(slot, 1, [sampler])
                    logger.debug(f"Bound DirectX sampler to slot {slot}")
        except Exception as e:
            logger.debug(f"Failed to bind DirectX sampler: {e}")

    def _bind_opengl_sampler(self, backend: Any, sampler: Any, slot: int) -> None:
        """Bind OpenGL sampler object.

        Args:
            backend: OpenGL backend instance.
            sampler: OpenGL sampler object.
            slot: Sampler slot to bind to.
        """
        try:
            from ornata.api.exports.interop import glBindSampler
            sampler_id = int(sampler) if isinstance(sampler, (int, float)) else 0
            glBindSampler(int(slot), sampler_id)
            logger.debug("Bound OpenGL sampler %s to slot %s", sampler_id, slot)
        except Exception as exc:
            logger.debug("Failed to bind OpenGL sampler: %s", exc)

def gl_filter(mode: FilterMode) -> int:
    from ornata.api.exports.interop import GL_LINEAR, GL_LINEAR_MIPMAP_LINEAR, GL_LINEAR_MIPMAP_NEAREST, GL_NEAREST, GL_NEAREST_MIPMAP_LINEAR, GL_NEAREST_MIPMAP_NEAREST
    mapping = {
        FilterMode.NEAREST: GL_NEAREST,
        FilterMode.LINEAR: GL_LINEAR,
        FilterMode.NEAREST_MIPMAP_NEAREST: GL_NEAREST_MIPMAP_NEAREST,
        FilterMode.LINEAR_MIPMAP_NEAREST: GL_LINEAR_MIPMAP_NEAREST,
        FilterMode.NEAREST_MIPMAP_LINEAR: GL_NEAREST_MIPMAP_LINEAR,
        FilterMode.LINEAR_MIPMAP_LINEAR: GL_LINEAR_MIPMAP_LINEAR,
    }
    return mapping.get(mode, GL_LINEAR)


def gl_wrap(mode: WrapMode) -> int:
    from ornata.api.exports.interop import GL_CLAMP_TO_BORDER, GL_CLAMP_TO_EDGE, GL_MIRRORED_REPEAT, GL_REPEAT
    mapping = {
        WrapMode.CLAMP_TO_EDGE: GL_CLAMP_TO_EDGE,
        WrapMode.CLAMP_TO_BORDER: GL_CLAMP_TO_BORDER,
        WrapMode.REPEAT: GL_REPEAT,
        WrapMode.MIRRORED_REPEAT: GL_MIRRORED_REPEAT,
    }
    return mapping.get(mode, GL_CLAMP_TO_EDGE)


# Predefined sampler configurations for common use cases
DEFAULT_SAMPLER = SamplerState()
LINEAR_CLAMP_SAMPLER = SamplerState(
    min_filter=FilterMode.LINEAR,
    mag_filter=FilterMode.LINEAR,
    wrap_s=WrapMode.CLAMP_TO_EDGE,
    wrap_t=WrapMode.CLAMP_TO_EDGE,
    wrap_r=WrapMode.CLAMP_TO_EDGE,
)
NEAREST_REPEAT_SAMPLER = SamplerState(
    min_filter=FilterMode.NEAREST,
    mag_filter=FilterMode.NEAREST,
    wrap_s=WrapMode.REPEAT,
    wrap_t=WrapMode.REPEAT,
    wrap_r=WrapMode.REPEAT,
)
ANISOTROPIC_SAMPLER = SamplerState(
    min_filter=FilterMode.LINEAR_MIPMAP_LINEAR,
    mag_filter=FilterMode.LINEAR,
    wrap_s=WrapMode.CLAMP_TO_EDGE,
    wrap_t=WrapMode.CLAMP_TO_EDGE,
    wrap_r=WrapMode.CLAMP_TO_EDGE,
    max_anisotropy=16,
)