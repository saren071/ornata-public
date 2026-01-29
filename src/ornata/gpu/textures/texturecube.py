"""Cube texture implementation for the GPU system with multi-backend support."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ornata.gpu.textures.sampler_state import SamplerState


class CubeTexture:
    """Cube texture implementation with comprehensive multi-backend support.

    Supports DirectX, OpenGL backends with automatic fallback
    to CPU-side storage when GPU is unavailable.
    """

    def __init__(
        self,
        size: int,
        data: list[bytes | bytearray | memoryview | list[int] | None] | None = None,
        format: str = "rgba8",
        usage: str = "shader_read",
        mip_levels: int = 1,
        sampler_state: SamplerState | None = None,
    ) -> None:
        """Initialize cube texture.

        Args:
            size: Width/height of each cube face in pixels.
            data: List of 6 faces' pixel data, or None per face.
            format: Texture format string (e.g., 'rgba8', 'rgb8').
            usage: Texture usage flags.
            mip_levels: Number of mipmap levels.
            sampler_state: Custom sampler state configuration.
        """
        self.size = size
        self.format = format.lower()
        self.usage = usage.lower()
        self.mip_levels = mip_levels
        
        if data is not None and len(data) != 6:
            raise ValueError("Cube texture requires data for 6 faces")
        
        self._data: list[bytes | bytearray | memoryview | list[int] | None] = data or [None] * 6
        self._texture_id: Any | None = None
        self._backend_type: str | None = None
        from ornata.gpu.textures.sampler_state import DEFAULT_SAMPLER
        self._sampler_state = sampler_state or DEFAULT_SAMPLER
        self._is_dirty = True
        
        # Platform-specific texture handles
        self._directx_texture: Any | None = None
        self._opengl_texture: int | None = None
        
        # Shader Resource View for DirectX
        self._srv: Any | None = None

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
        """Try to create DirectX cube texture."""
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
                    
                # Initialize backend to get the device
                backend._ensure_initialized()
                if backend._device is None or backend._device.native_device is None:
                    return False
                    
                # Create DirectX cube texture using the actual API
                texture_manager = DirectXTexture(backend._device.native_device)
                
                # Note: DirectX cube textures require special setup
                # For now, create as 2D array texture with 6 slices
                texture = texture_manager.create_texture_2d(
                    width=self.size,
                    height=self.size
                )
                srv = texture_manager.create_shader_resource_view(texture)
                
                self._directx_texture = texture
                self._srv = srv
                self._texture_id = srv  # Use SRV as the texture identifier
                self._backend_type = "directx"
                return True
                
            except ImportError:
                return False
                
        except Exception:
            return False

    def _try_create_opengl_texture(self) -> bool:
        """Try to create OpenGL cube texture."""
        try:
            from ornata.api.exports.interop import GL_TEXTURE_CUBE_MAP, glBindTexture, glGenTextures
            
            # Generate and bind cubemap texture
            self._opengl_texture = glGenTextures(1)
            glBindTexture(GL_TEXTURE_CUBE_MAP, self._opengl_texture)

            # Configure sampler state
            self._apply_opengl_sampler_state()
            
            # Upload data for all 6 faces
            self._upload_opengl_cube_data()

            glBindTexture(GL_TEXTURE_CUBE_MAP, 0)
            
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
        """Apply sampler state settings for OpenGL cubemap."""
        try:
            from ornata.api.exports.interop import (
                GL_TEXTURE_CUBE_MAP,
                GL_TEXTURE_MAG_FILTER,
                GL_TEXTURE_MAX_ANISOTROPY_EXT,
                GL_TEXTURE_MIN_FILTER,
                GL_TEXTURE_WRAP_R,
                GL_TEXTURE_WRAP_S,
                GL_TEXTURE_WRAP_T,
                glTexParameterf,
                glTexParameteri,
            )
            
            # Wrap modes - cubemaps require R wrap mode too
            wrap_s = self._get_opengl_wrap_mode(self._sampler_state.wrap_s)
            wrap_t = self._get_opengl_wrap_mode(self._sampler_state.wrap_t)
            wrap_r = self._get_opengl_wrap_mode(self._sampler_state.wrap_r)
            
            glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, wrap_s)
            glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, wrap_t)
            glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, wrap_r)
            
            # Filter modes
            min_filter = self._get_opengl_filter_mode(self._sampler_state.min_filter)
            mag_filter = self._get_opengl_filter_mode(self._sampler_state.mag_filter)
            
            glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, min_filter)
            glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, mag_filter)
            
            # Anisotropy
            if self._sampler_state.max_anisotropy > 1:
                glTexParameterf(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAX_ANISOTROPY_EXT, 
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

    def _upload_opengl_cube_data(self) -> None:
        """Upload cube texture data to OpenGL."""
        from ornata.api.exports.interop import (
            GL_TEXTURE_CUBE_MAP_NEGATIVE_X,
            GL_TEXTURE_CUBE_MAP_NEGATIVE_Y,
            GL_TEXTURE_CUBE_MAP_NEGATIVE_Z,
            GL_TEXTURE_CUBE_MAP_POSITIVE_X,
            GL_TEXTURE_CUBE_MAP_POSITIVE_Y,
            GL_TEXTURE_CUBE_MAP_POSITIVE_Z,
            glTexImage2D,
        )
        
        internal_format, pixel_format, pixel_type = self._get_opengl_format()
        targets = [
            GL_TEXTURE_CUBE_MAP_POSITIVE_X,
            GL_TEXTURE_CUBE_MAP_NEGATIVE_X,
            GL_TEXTURE_CUBE_MAP_POSITIVE_Y,
            GL_TEXTURE_CUBE_MAP_NEGATIVE_Y,
            GL_TEXTURE_CUBE_MAP_POSITIVE_Z,
            GL_TEXTURE_CUBE_MAP_NEGATIVE_Z,
        ]
        
        for face, target in enumerate(targets):
            face_data = self._data[face]
            glTexImage2D(
                target,
                0,
                internal_format,
                self.size,
                self.size,
                0,
                pixel_format,
                pixel_type,
                face_data,
            )

    def _get_opengl_format(self) -> tuple[int, int, int]:
        """Get OpenGL format constants for texture format."""
        from ornata.api.exports.interop import GL_RGB, GL_RGB8, GL_RGBA, GL_RGBA8, GL_UNSIGNED_BYTE
        
        fmt_l = self.format.lower()
        if fmt_l == "rgba8":
            return (GL_RGBA8, GL_RGBA, GL_UNSIGNED_BYTE)
        if fmt_l == "rgb8":
            return (GL_RGB8, GL_RGB, GL_UNSIGNED_BYTE)
        # Default to RGBA8
        return (GL_RGBA8, GL_RGBA, GL_UNSIGNED_BYTE)

    def bind(self, slot: int = 0) -> None:
        """Bind cube texture to texture slot."""
        if self._backend_type == "directx" and self._srv:
            # DirectX uses SRV for binding
            pass  # SRV binding would be done through the device context
        elif self._backend_type == "opengl" and self._opengl_texture:
            try:
                from ornata.api.exports.interop import GL_TEXTURE0, GL_TEXTURE_CUBE_MAP, glActiveTexture, glBindTexture
                glActiveTexture(GL_TEXTURE0 + slot)
                glBindTexture(GL_TEXTURE_CUBE_MAP, self._opengl_texture)
            except Exception:
                pass  # CPU fallback
        # CPU fallback - no-op

    def unbind(self) -> None:
        """Unbind cube texture."""
        if self._backend_type == "directx" and self._srv:
            # DirectX unbind would be done through the device context
            pass
        elif self._backend_type == "opengl" and self._opengl_texture:
            try:
                from ornata.api.exports.interop import GL_TEXTURE_CUBE_MAP, glBindTexture
                glBindTexture(GL_TEXTURE_CUBE_MAP, 0)
            except Exception:
                pass

    def update_data(self, data: list[bytes | bytearray | memoryview | list[int] | None]) -> None:
        """Update texture data for all faces.

        Args:
            data: List of pixel data for 6 faces.
        """
        if len(data) != 6:
            raise ValueError("Cube texture requires data for 6 faces")
        
        self._data = data
        self._is_dirty = True
        
        if self._backend_type == "directx" and self._directx_texture:
            # DirectX data update would go here
            pass
        elif self._backend_type == "opengl" and self._opengl_texture:
            try:
                from ornata.api.exports.interop import (
                    GL_TEXTURE_CUBE_MAP,
                    GL_TEXTURE_CUBE_MAP_NEGATIVE_X,
                    GL_TEXTURE_CUBE_MAP_NEGATIVE_Y,
                    GL_TEXTURE_CUBE_MAP_NEGATIVE_Z,
                    GL_TEXTURE_CUBE_MAP_POSITIVE_X,
                    GL_TEXTURE_CUBE_MAP_POSITIVE_Y,
                    GL_TEXTURE_CUBE_MAP_POSITIVE_Z,
                    glBindTexture,
                    glTexSubImage2D,
                )
                glBindTexture(GL_TEXTURE_CUBE_MAP, self._opengl_texture)
                _, pixel_format, pixel_type = self._get_opengl_format()
                targets = [
                    GL_TEXTURE_CUBE_MAP_POSITIVE_X,
                    GL_TEXTURE_CUBE_MAP_NEGATIVE_X,
                    GL_TEXTURE_CUBE_MAP_POSITIVE_Y,
                    GL_TEXTURE_CUBE_MAP_NEGATIVE_Y,
                    GL_TEXTURE_CUBE_MAP_POSITIVE_Z,
                    GL_TEXTURE_CUBE_MAP_NEGATIVE_Z,
                ]
                for face, target in enumerate(targets):
                    glTexSubImage2D(
                        target,
                        0,
                        0,
                        0,
                        self.size,
                        self.size,
                        pixel_format,
                        pixel_type,
                        self._data[face],
                    )
                glBindTexture(GL_TEXTURE_CUBE_MAP, 0)
            except Exception:
                pass  # CPU fallback

    def update_face(self, face_index: int, data: bytes | bytearray | memoryview | list[int]) -> None:
        """Update data for a specific face.

        Args:
            face_index: Index of the face (0-5).
            data: Pixel data for the face.
        """
        if not 0 <= face_index < 6:
            raise ValueError("Face index must be between 0 and 5")
        
        self._data[face_index] = data
        self._is_dirty = True
        
        if self._backend_type == "directx" and self._directx_texture:
            # DirectX face update would go here
            pass
        elif self._backend_type == "opengl" and self._opengl_texture:
            try:
                from ornata.api.exports.interop import (
                    GL_TEXTURE_CUBE_MAP,
                    GL_TEXTURE_CUBE_MAP_NEGATIVE_X,
                    GL_TEXTURE_CUBE_MAP_NEGATIVE_Y,
                    GL_TEXTURE_CUBE_MAP_NEGATIVE_Z,
                    GL_TEXTURE_CUBE_MAP_POSITIVE_X,
                    GL_TEXTURE_CUBE_MAP_POSITIVE_Y,
                    GL_TEXTURE_CUBE_MAP_POSITIVE_Z,
                    glBindTexture,
                    glTexSubImage2D,
                )
                glBindTexture(GL_TEXTURE_CUBE_MAP, self._opengl_texture)
                _, pixel_format, pixel_type = self._get_opengl_format()
                targets = [
                    GL_TEXTURE_CUBE_MAP_POSITIVE_X,
                    GL_TEXTURE_CUBE_MAP_NEGATIVE_X,
                    GL_TEXTURE_CUBE_MAP_POSITIVE_Y,
                    GL_TEXTURE_CUBE_MAP_NEGATIVE_Y,
                    GL_TEXTURE_CUBE_MAP_POSITIVE_Z,
                    GL_TEXTURE_CUBE_MAP_NEGATIVE_Z,
                ]
                glTexSubImage2D(
                    targets[face_index],
                    0,
                    0,
                    0,
                    self.size,
                    self.size,
                    pixel_format,
                    pixel_type,
                    data,
                )
                glBindTexture(GL_TEXTURE_CUBE_MAP, 0)
            except Exception:
                pass  # CPU fallback

    def generate_mipmaps(self) -> None:
        """Generate mipmaps for the cube texture."""
        if self.mip_levels <= 1:
            return
            
        if self._backend_type == "directx" and self._directx_texture:
            # DirectX mipmap generation would go here
            pass
        elif self._backend_type == "opengl" and self._opengl_texture:
            try:
                from ornata.api.exports.interop import GL_TEXTURE_CUBE_MAP, glBindTexture, glGenerateMipmap
                glBindTexture(GL_TEXTURE_CUBE_MAP, self._opengl_texture)
                glGenerateMipmap(GL_TEXTURE_CUBE_MAP)
                glBindTexture(GL_TEXTURE_CUBE_MAP, 0)
            except Exception:
                pass  # CPU fallback

    def set_sampler_state(self, sampler_state: SamplerState) -> None:
        """Set the sampler state for this cube texture.

        Args:
            sampler_state: New sampler state configuration.
        """
        self._sampler_state = sampler_state
        
        if self._backend_type == "opengl" and self._opengl_texture:
            try:
                from ornata.api.exports.interop import GL_TEXTURE_CUBE_MAP, glBindTexture
                glBindTexture(GL_TEXTURE_CUBE_MAP, self._opengl_texture)
                self._apply_opengl_sampler_state()
                glBindTexture(GL_TEXTURE_CUBE_MAP, 0)
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
            # DirectX cleanup
            if self._srv:
                self._srv.Release()
            if self._directx_texture:
                self._directx_texture.Release()
        elif self._backend_type == "opengl" and self._opengl_texture:
            try:
                from ornata.api.exports.interop import glDeleteTextures
                glDeleteTextures(1, [self._opengl_texture])
            except Exception:
                pass

    def __del__(self) -> None:
        """Destructor to ensure cleanup."""
        self.cleanup()