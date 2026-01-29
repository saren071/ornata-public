"""2D texture implementation for the GPU system with multi-backend support."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ornata.api.exports.definitions import TextureFormat, TextureUsage

if TYPE_CHECKING:
    from ornata.gpu.textures.sampler_state import SamplerState


class Texture2D:
    """2D texture implementation with comprehensive multi-backend support.

    Supports DirectX, OpenGL, with automatic fallback to CPU-side storage when GPU is unavailable.
    """

    def __init__(
        self,
        width: int,
        height: int,
        data: bytes | bytearray | memoryview | list[int] | None = None,
        format: str = "rgba8",
        usage: str = "shader_read",
        mip_levels: int = 1,
        samples: int = 1,
        sampler_state: SamplerState | None = None,
    ) -> None:
        """Initialize 2D texture.

        Args:
            width: Texture width in pixels.
            height: Texture height in pixels.
            data: Initial pixel data (row-major, tightly packed).
            format: Texture format string (e.g., 'rgba8', 'rgb8', 'rgba16f').
            usage: Texture usage flags.
            mip_levels: Number of mipmap levels (1 for no mipmaps).
            samples: MSAA sample count (1 for no MSAA).
            sampler_state: Custom sampler state configuration.
        """
        self.width = width
        self.height = height
        self.format = TextureFormat(format.lower())
        self.usage = TextureUsage(usage.lower())
        self.mip_levels = mip_levels
        self.samples = samples
        
        self._data: bytes | bytearray | memoryview | list[int] | None = data
        self._texture_id: Any | None = None
        self._backend_type: str | None = None
        from ornata.gpu.textures.sampler_state import DEFAULT_SAMPLER
        self._sampler_state = sampler_state or DEFAULT_SAMPLER
        self._is_dirty = True
        
        # Platform-specific texture handles
        self._directx_texture: Any | None = None
        self._opengl_texture: int | None = None

        self._create_texture_if_available()

    def _create_texture_if_available(self) -> None:
        """Create GPU texture using available backend."""
        # Try DirectX first on Windows
        if self._try_create_directx_texture():
            return
        
        # Try OpenGL
        if self._try_create_opengl_texture():
            return
            
        # Fallback to CPU-side only
        self._texture_id = None
        self._backend_type = "cpu"

    def _try_create_directx_texture(self) -> bool:
        """Try to create DirectX texture."""
        try:
            import platform
            if platform.system() != "Windows":
                return False
                
            # Try to import DirectX modules
            try:
                from ornata.gpu.backends.directx.backend import DirectXBackend
                from ornata.gpu.backends.directx.texture import DirectXTexture
                
                backend = DirectXBackend()
                if not backend.is_available():
                    return False
                    
                # Create DirectX texture using the actual API
                texture_manager = DirectXTexture(backend._device)
                texture = texture_manager.create_texture_2d(
                    width=self.width,
                    height=self.height
                )
                srv = texture_manager.create_shader_resource_view(texture)
                
                self._directx_texture = texture
                self._texture_id = srv  # Use SRV as the texture identifier
                self._backend_type = "directx"
                return True
                
            except ImportError:
                return False
                
        except Exception:
            return False

    def _try_create_opengl_texture(self) -> bool:
        """Try to create OpenGL texture."""
        try:
            from ornata.api.exports.interop import GL_TEXTURE_2D, glBindTexture, glGenTextures
            
            # Generate and bind texture
            self._opengl_texture = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, self._opengl_texture)

            # Configure sampler state
            self._apply_opengl_sampler_state()
            
            # Upload initial data if provided
            if self._data is not None:
                self._upload_opengl_data()
            else:
                # Allocate empty texture
                self._allocate_opengl_texture()

            glBindTexture(GL_TEXTURE_2D, 0)
            
            self._texture_id = self._opengl_texture
            self._backend_type = "opengl"
            return True
            
        except Exception:
            # Clean up on failure
            if hasattr(self, '_opengl_texture') and self._opengl_texture:
                try:
                    from ornata.api.exports.interop import glDeleteTextures
                    glDeleteTextures(1, [self._opengl_texture])
                except Exception:
                    pass
            return False

    def _apply_opengl_sampler_state(self) -> None:
        """Apply sampler state settings for OpenGL."""
        try:
            from ornata.api.exports.interop import (
                GL_TEXTURE_2D,
                GL_TEXTURE_MAG_FILTER,
                GL_TEXTURE_MAX_ANISOTROPY_EXT,
                GL_TEXTURE_MIN_FILTER,
                GL_TEXTURE_WRAP_S,
                GL_TEXTURE_WRAP_T,
                glTexParameterf,
                glTexParameteri,
            )
            
            # Wrap modes
            wrap_s = self._get_opengl_wrap_mode(self._sampler_state.wrap_s)
            wrap_t = self._get_opengl_wrap_mode(self._sampler_state.wrap_t)
            
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, wrap_s)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, wrap_t)
            
            # Filter modes
            min_filter = self._get_opengl_filter_mode(self._sampler_state.min_filter)
            mag_filter = self._get_opengl_filter_mode(self._sampler_state.mag_filter)
            
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, min_filter)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, mag_filter)
            
            # Anisotropy
            if self._sampler_state.max_anisotropy > 1:
                glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAX_ANISOTROPY_EXT, 
                                 float(self._sampler_state.max_anisotropy))
                                 
        except Exception:
            pass  # Use defaults if settings fail

    def _get_opengl_wrap_mode(self, wrap_mode: Any) -> int:
        """Convert wrap mode to OpenGL constant."""
        from ornata.api.exports.interop import GL_CLAMP_TO_BORDER, GL_CLAMP_TO_EDGE, GL_MIRRORED_REPEAT, GL_REPEAT
        from ornata.gpu.textures.sampler_state import WrapMode
        
        if isinstance(wrap_mode, str):
            wrap_mode = WrapMode(wrap_mode)
            
        match wrap_mode:
            case WrapMode.CLAMP_TO_EDGE:
                return GL_CLAMP_TO_EDGE
            case WrapMode.CLAMP_TO_BORDER:
                return GL_CLAMP_TO_BORDER
            case WrapMode.REPEAT:
                return GL_REPEAT
            case WrapMode.MIRRORED_REPEAT:
                return GL_MIRRORED_REPEAT
            case _:
                return GL_CLAMP_TO_EDGE

    def _get_opengl_filter_mode(self, filter_mode: Any) -> int:
        """Convert filter mode to OpenGL constant."""
        from ornata.api.exports.interop import GL_LINEAR, GL_LINEAR_MIPMAP_LINEAR, GL_LINEAR_MIPMAP_NEAREST, GL_NEAREST, GL_NEAREST_MIPMAP_LINEAR, GL_NEAREST_MIPMAP_NEAREST
        from ornata.gpu.textures.sampler_state import FilterMode
        
        if isinstance(filter_mode, str):
            filter_mode = FilterMode(filter_mode)
            
        match filter_mode:
            case FilterMode.NEAREST:
                return GL_NEAREST
            case FilterMode.LINEAR:
                return GL_LINEAR
            case FilterMode.NEAREST_MIPMAP_NEAREST:
                return GL_NEAREST_MIPMAP_NEAREST
            case FilterMode.LINEAR_MIPMAP_NEAREST:
                return GL_LINEAR_MIPMAP_NEAREST
            case FilterMode.NEAREST_MIPMAP_LINEAR:
                return GL_NEAREST_MIPMAP_LINEAR
            case FilterMode.LINEAR_MIPMAP_LINEAR:
                return GL_LINEAR_MIPMAP_LINEAR
            case _:
                return GL_LINEAR

    def _upload_opengl_data(self) -> None:
        """Upload texture data to OpenGL."""
        from ornata.api.exports.interop import GL_TEXTURE_2D, glTexImage2D
        
        internal_format, pixel_format, pixel_type = self._get_opengl_format()
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            internal_format,
            self.width,
            self.height,
            0,
            pixel_format,
            pixel_type,
            self._data,
        )

    def _allocate_opengl_texture(self) -> None:
        """Allocate empty OpenGL texture."""
        from ornata.api.exports.interop import GL_TEXTURE_2D, glTexImage2D
        
        internal_format, pixel_format, pixel_type = self._get_opengl_format()
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            internal_format,
            self.width,
            self.height,
            0,
            pixel_format,
            pixel_type,
            None,
        )

    def _get_opengl_format(self) -> tuple[int, int, int]:
        """Get OpenGL format constants for texture format."""
        from ornata.api.exports.interop import (
            GL_DEPTH_COMPONENT,
            GL_DEPTH_COMPONENT24,
            GL_DEPTH_COMPONENT32F,
            GL_FLOAT,
            GL_HALF_FLOAT,
            GL_RGB,
            GL_RGB8,
            GL_RGB16F,
            GL_RGB32F,
            GL_RGBA,
            GL_RGBA8,
            GL_RGBA16F,
            GL_RGBA32F,
            GL_STENCIL_INDEX,
            GL_STENCIL_INDEX8,
            GL_UNSIGNED_BYTE,
            GL_UNSIGNED_INT,
        )
        
        match self.format:
            case TextureFormat.RGBA8:
                return (GL_RGBA8, GL_RGBA, GL_UNSIGNED_BYTE)
            case TextureFormat.RGB8:
                return (GL_RGB8, GL_RGB, GL_UNSIGNED_BYTE)
            case TextureFormat.RGBA16F:
                return (GL_RGBA16F, GL_RGBA, GL_HALF_FLOAT)
            case TextureFormat.RGB16F:
                return (GL_RGB16F, GL_RGB, GL_HALF_FLOAT)
            case TextureFormat.RGBA32F:
                return (GL_RGBA32F, GL_RGBA, GL_FLOAT)
            case TextureFormat.RGB32F:
                return (GL_RGB32F, GL_RGB, GL_FLOAT)
            case TextureFormat.DEPTH24:
                return (GL_DEPTH_COMPONENT24, GL_DEPTH_COMPONENT, GL_UNSIGNED_INT)
            case TextureFormat.DEPTH32F:
                return (GL_DEPTH_COMPONENT32F, GL_DEPTH_COMPONENT, GL_FLOAT)
            case TextureFormat.STENCIL8:
                return (GL_STENCIL_INDEX8, GL_STENCIL_INDEX, GL_UNSIGNED_BYTE)
            case _:
                return (GL_RGBA8, GL_RGBA, GL_UNSIGNED_BYTE)

    def bind(self, slot: int = 0) -> None:
        """Bind 2D texture to texture slot."""
        if self._backend_type == "directx" and self._directx_texture:
            self._directx_texture.bind(slot)
        elif self._backend_type == "opengl" and self._opengl_texture:
            try:
                from ornata.api.exports.interop import GL_TEXTURE0, GL_TEXTURE_2D, glActiveTexture, glBindTexture
                glActiveTexture(GL_TEXTURE0 + slot)
                glBindTexture(GL_TEXTURE_2D, self._opengl_texture)
            except Exception:
                pass  # CPU fallback
        # CPU fallback - no-op

    def unbind(self) -> None:
        """Unbind 2D texture."""
        if self._backend_type == "directx" and self._directx_texture:
            self._directx_texture.unbind()
        elif self._backend_type == "opengl" and self._opengl_texture:
            try:
                from ornata.api.exports.interop import GL_TEXTURE_2D, glBindTexture
                glBindTexture(GL_TEXTURE_2D, 0)
            except Exception:
                pass

    def update_data(self, data: bytes | bytearray | memoryview | list[int]) -> None:
        """Update complete texture data.

        Args:
            data: Pixel data matching the texture format and size.
        """
        self._data = data
        self._is_dirty = True
        
        if self._backend_type == "directx" and self._directx_texture:
            self._directx_texture.update_data(data)
        elif self._backend_type == "opengl" and self._opengl_texture:
            try:
                from ornata.api.exports.interop import GL_TEXTURE_2D, glBindTexture, glTexSubImage2D
                glBindTexture(GL_TEXTURE_2D, self._opengl_texture)
                _, pixel_format, pixel_type = self._get_opengl_format()
                glTexSubImage2D(
                    GL_TEXTURE_2D,
                    0,
                    0,
                    0,
                    self.width,
                    self.height,
                    pixel_format,
                    pixel_type,
                    data,
                )
                glBindTexture(GL_TEXTURE_2D, 0)
            except Exception:
                pass  # CPU fallback

    def update_region(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        data: bytes | bytearray | memoryview | list[int],
    ) -> None:
        """Update a region of the texture.

        Args:
            x: X offset in pixels.
            y: Y offset in pixels.
            width: Width of region in pixels.
            height: Height of region in pixels.
            data: Pixel data for the region.
        """
        if self._backend_type == "directx" and self._directx_texture:
            self._directx_texture.update_region(x, y, width, height, data)
        elif self._backend_type == "opengl" and self._opengl_texture:
            try:
                from ornata.api.exports.interop import GL_TEXTURE_2D, glBindTexture, glTexSubImage2D
                glBindTexture(GL_TEXTURE_2D, self._opengl_texture)
                _, pixel_format, pixel_type = self._get_opengl_format()
                glTexSubImage2D(
                    GL_TEXTURE_2D,
                    0,
                    x,
                    y,
                    width,
                    height,
                    pixel_format,
                    pixel_type,
                    data,
                )
                glBindTexture(GL_TEXTURE_2D, 0)
            except Exception:
                pass  # CPU fallback

    def generate_mipmaps(self) -> None:
        """Generate mipmaps for the texture."""
        if self.mip_levels <= 1:
            return
            
        if self._backend_type == "directx" and self._directx_texture:
            self._directx_texture.generate_mipmaps()
        elif self._backend_type == "opengl" and self._opengl_texture:
            try:
                from ornata.api.exports.interop import GL_TEXTURE_2D, glBindTexture, glGenerateMipmap
                glBindTexture(GL_TEXTURE_2D, self._opengl_texture)
                glGenerateMipmap(GL_TEXTURE_2D)
                glBindTexture(GL_TEXTURE_2D, 0)
            except Exception:
                pass  # CPU fallback

    def set_sampler_state(self, sampler_state: SamplerState) -> None:
        """Set the sampler state for this texture.

        Args:
            sampler_state: New sampler state configuration.
        """
        self._sampler_state = sampler_state
        
        if self._backend_type == "opengl" and self._opengl_texture:
            try:
                from ornata.api.exports.interop import GL_TEXTURE_2D, glBindTexture
                glBindTexture(GL_TEXTURE_2D, self._opengl_texture)
                self._apply_opengl_sampler_state()
                glBindTexture(GL_TEXTURE_2D, 0)
            except Exception:
                pass

    @property
    def texture_id(self) -> Any:
        """Get the GPU texture identifier."""
        return self._texture_id

    @property
    def backend_type(self) -> str:
        """Get the backend type used for this texture."""
        return self._backend_type or "unknown"

    @property
    def is_gpu_texture(self) -> bool:
        """Check if this is a GPU texture (not CPU fallback)."""
        return self._backend_type is not None and self._backend_type != "cpu"

    @property
    def is_dirty(self) -> bool:
        """Check if texture data needs to be uploaded to GPU."""
        return self._is_dirty

    def cleanup(self) -> None:
        """Clean up GPU resources."""
        if self._backend_type == "directx" and self._directx_texture:
            self._directx_texture.cleanup()
        elif self._backend_type == "opengl" and self._opengl_texture:
            try:
                from ornata.api.exports.interop import glDeleteTextures
                glDeleteTextures(1, [self._opengl_texture])
            except Exception:
                pass

    def __del__(self) -> None:
        """Destructor to ensure cleanup."""
        self.cleanup()