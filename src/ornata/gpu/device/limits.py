"""Hardware limits detection and safe fallbacks."""

from __future__ import annotations

import platform
from typing import TYPE_CHECKING

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.gpu.misc import GPUBackend

logger = get_logger(__name__)


class Limits:
    """Queries hardware constraints with safe fallbacks."""

    def __init__(self, backend: GPUBackend | None = None) -> None:
        """Initialize limits detector.

        Args:
            backend: GPU backend to query. If None, uses default detection.
        """
        self._backend = backend
        self._cached_limits: dict[str, int] | None = None

    def get_max_texture_size(self) -> int:
        """Get the maximum supported texture size.

        Returns:
            Maximum texture dimension in pixels.
        """
        return self._get_limit("max_texture_size", 2048)

    def get_max_renderbuffer_size(self) -> int:
        """Get the maximum supported renderbuffer size.

        Returns:
            Maximum renderbuffer dimension in pixels.
        """
        return self._get_limit("max_renderbuffer_size", 2048)

    def get_max_vertex_buffer_size(self) -> int:
        """Get the maximum supported vertex buffer size.

        Returns:
            Maximum vertex buffer size in bytes.
        """
        return self._get_limit("max_vertex_buffer_size", 16 * 1024 * 1024)  # 16MB

    def get_max_index_buffer_size(self) -> int:
        """Get the maximum supported index buffer size.

        Returns:
            Maximum index buffer size in bytes.
        """
        return self._get_limit("max_index_buffer_size", 8 * 1024 * 1024)  # 8MB

    def get_max_uniform_buffer_size(self) -> int:
        """Get the maximum supported uniform buffer size.

        Returns:
            Maximum uniform buffer size in bytes.
        """
        return self._get_limit("max_uniform_buffer_size", 64 * 1024)  # 64KB

    def get_max_shader_storage_buffer_size(self) -> int:
        """Get the maximum supported shader storage buffer size.

        Returns:
            Maximum shader storage buffer size in bytes.
        """
        return self._get_limit("max_shader_storage_buffer_size", 128 * 1024 * 1024)  # 128MB

    def get_max_vertex_attributes(self) -> int:
        """Get the maximum number of vertex attributes.

        Returns:
            Maximum number of vertex attributes supported.
        """
        return self._get_limit("max_vertex_attributes", 16)

    def get_max_texture_units(self) -> int:
        """Get the maximum number of texture units.

        Returns:
            Maximum number of texture units supported.
        """
        return self._get_limit("max_texture_units", 16)

    def get_max_uniform_buffer_bindings(self) -> int:
        """Get the maximum number of uniform buffer bindings.

        Returns:
            Maximum number of uniform buffer bindings supported.
        """
        return self._get_limit("max_uniform_buffer_bindings", 8)

    def get_max_shader_storage_buffer_bindings(self) -> int:
        """Get the maximum number of shader storage buffer bindings.

        Returns:
            Maximum number of shader storage buffer bindings supported.
        """
        return self._get_limit("max_shader_storage_buffer_bindings", 8)

    def get_max_framebuffer_color_attachments(self) -> int:
        """Get the maximum number of framebuffer color attachments.

        Returns:
            Maximum number of color attachments supported.
        """
        return self._get_limit("max_framebuffer_color_attachments", 8)

    def get_max_samples(self) -> int:
        """Get the maximum number of samples for multisampling.

        Returns:
            Maximum number of samples supported.
        """
        return self._get_limit("max_samples", 4)

    def get_max_compute_work_group_size(self) -> int:
        """Get the maximum compute work group size.

        Returns:
            Maximum work group size for compute shaders.
        """
        return self._get_limit("max_compute_work_group_size", 1024)

    def get_max_compute_work_group_invocations(self) -> int:
        """Get the maximum compute work group invocations.

        Returns:
            Maximum work group invocations for compute shaders.
        """
        return self._get_limit("max_compute_work_group_invocations", 1024)

    def _get_limit(self, name: str, default: int) -> int:
        """Get a limit value with caching and fallbacks.

        Args:
            name: Limit name to query.
            default: Default value if limit cannot be determined.

        Returns:
            Limit value or default.
        """
        if self._cached_limits is None:
            self._cached_limits = self._query_limits()

        return self._cached_limits.get(name, default)

    def _query_limits(self) -> dict[str, int]:
        """Query limits from the GPU backend.

        Returns:
            Dictionary of limit names to values.
        """
        limits: dict[str, int] = {}

        if self._backend is None:
            # Return conservative defaults when no backend available
            limits.update({
                "max_texture_size": 2048,
                "max_renderbuffer_size": 2048,
                "max_vertex_buffer_size": 16 * 1024 * 1024,  # 16MB
                "max_index_buffer_size": 8 * 1024 * 1024,    # 8MB
                "max_uniform_buffer_size": 64 * 1024,        # 64KB
                "max_shader_storage_buffer_size": 128 * 1024 * 1024,  # 128MB
                "max_vertex_attributes": 16,
                "max_texture_units": 16,
                "max_uniform_buffer_bindings": 8,
                "max_shader_storage_buffer_bindings": 8,
                "max_framebuffer_color_attachments": 8,
                "max_samples": 4,
                "max_compute_work_group_size": 1024,
                "max_compute_work_group_invocations": 1024,
            })
            return limits

        try:
            # Query backend-specific limits
            if hasattr(self._backend, 'get_limits'):
                result = self._backend.get_limits()  # dynamic backend-provided dict
                if isinstance(result, dict):
                    tmp: dict[str, int] = {}
                    for k, v in result.items():
                        if isinstance(k, str) and isinstance(v, int):
                            tmp[k] = v
                    limits.update(tmp)
            else:
                # Fallback to basic limit detection
                limits.update(self._detect_basic_limits())
        except Exception as e:
            logger.warning(f"Failed to query GPU limits: {e}")
            # Fall back to conservative defaults
            limits.update({
                "max_texture_size": 2048,
                "max_renderbuffer_size": 2048,
                "max_vertex_buffer_size": 16 * 1024 * 1024,  # 16MB
                "max_index_buffer_size": 8 * 1024 * 1024,    # 8MB
                "max_uniform_buffer_size": 64 * 1024,        # 64KB
                "max_shader_storage_buffer_size": 128 * 1024 * 1024,  # 128MB
                "max_vertex_attributes": 16,
                "max_texture_units": 16,
                "max_uniform_buffer_bindings": 8,
                "max_shader_storage_buffer_bindings": 8,
                "max_framebuffer_color_attachments": 8,
                "max_samples": 4,
                "max_compute_work_group_size": 1024,
                "max_compute_work_group_invocations": 1024,
            })

        return limits

    def _detect_basic_limits(self) -> dict[str, int]:
        """Detect basic limits based on platform and backend type.

        Returns:
            Dictionary of basic limit detections.
        """
        limits: dict[str, int] = {}
        system = platform.system()

        # Basic limit assumptions based on platform
        if system == "Windows":
            limits.update({
                "max_texture_size": 16384,
                "max_renderbuffer_size": 16384,
                "max_vertex_buffer_size": 256 * 1024 * 1024,  # 256MB
                "max_index_buffer_size": 128 * 1024 * 1024,   # 128MB
                "max_uniform_buffer_size": 64 * 1024,         # 64KB
                "max_shader_storage_buffer_size": 1024 * 1024 * 1024,  # 1GB
                "max_vertex_attributes": 32,
                "max_texture_units": 32,
                "max_uniform_buffer_bindings": 16,
                "max_shader_storage_buffer_bindings": 16,
                "max_framebuffer_color_attachments": 8,
                "max_samples": 16,
                "max_compute_work_group_size": 1024,
                "max_compute_work_group_invocations": 1024,
            })

        return limits

    def validate_texture_size(self, size: int) -> None:
        """Validate texture size against hardware limits.

        Args:
            size: Texture size to validate.

        Raises:
            ValueError: If size exceeds maximum texture size.
        """
        max_size = self.get_max_texture_size()
        if size > max_size:
            raise ValueError(f"Texture size {size} exceeds maximum {max_size}")

    def validate_renderbuffer_size(self, size: int) -> None:
        """Validate renderbuffer size against hardware limits.

        Args:
            size: Renderbuffer size to validate.

        Raises:
            ValueError: If size exceeds maximum renderbuffer size.
        """
        max_size = self.get_max_renderbuffer_size()
        if size > max_size:
            raise ValueError(f"Renderbuffer size {size} exceeds maximum {max_size}")

    def validate_vertex_buffer_size(self, size: int) -> None:
        """Validate vertex buffer size against hardware limits.

        Args:
            size: Buffer size in bytes to validate.

        Raises:
            ValueError: If size exceeds maximum vertex buffer size.
        """
        max_size = self.get_max_vertex_buffer_size()
        if size > max_size:
            raise ValueError(f"Vertex buffer size {size} exceeds maximum {max_size}")

    def validate_index_buffer_size(self, size: int) -> None:
        """Validate index buffer size against hardware limits.

        Args:
            size: Buffer size in bytes to validate.

        Raises:
            ValueError: If size exceeds maximum index buffer size.
        """
        max_size = self.get_max_index_buffer_size()
        if size > max_size:
            raise ValueError(f"Index buffer size {size} exceeds maximum {max_size}")

    def validate_uniform_buffer_size(self, size: int) -> None:
        """Validate uniform buffer size against hardware limits.

        Args:
            size: Buffer size in bytes to validate.

        Raises:
            ValueError: If size exceeds maximum uniform buffer size.
        """
        max_size = self.get_max_uniform_buffer_size()
        if size > max_size:
            raise ValueError(f"Uniform buffer size {size} exceeds maximum {max_size}")

    def validate_shader_storage_buffer_size(self, size: int) -> None:
        """Validate shader storage buffer size against hardware limits.

        Args:
            size: Buffer size in bytes to validate.

        Raises:
            ValueError: If size exceeds maximum shader storage buffer size.
        """
        max_size = self.get_max_shader_storage_buffer_size()
        if size > max_size:
            raise ValueError(f"Shader storage buffer size {size} exceeds maximum {max_size}")

    def validate_vertex_attributes(self, count: int) -> None:
        """Validate vertex attributes count against hardware limits.

        Args:
            count: Number of vertex attributes to validate.

        Raises:
            ValueError: If count exceeds maximum vertex attributes.
        """
        max_count = self.get_max_vertex_attributes()
        if count > max_count:
            raise ValueError(f"Vertex attributes count {count} exceeds maximum {max_count}")

    def validate_texture_units(self, count: int) -> None:
        """Validate texture units count against hardware limits.

        Args:
            count: Number of texture units to validate.

        Raises:
            ValueError: If count exceeds maximum texture units.
        """
        max_count = self.get_max_texture_units()
        if count > max_count:
            raise ValueError(f"Texture units count {count} exceeds maximum {max_count}")

    def validate_uniform_buffer_bindings(self, count: int) -> None:
        """Validate uniform buffer bindings count against hardware limits.

        Args:
            count: Number of uniform buffer bindings to validate.

        Raises:
            ValueError: If count exceeds maximum uniform buffer bindings.
        """
        max_count = self.get_max_uniform_buffer_bindings()
        if count > max_count:
            raise ValueError(f"Uniform buffer bindings count {count} exceeds maximum {max_count}")

    def validate_shader_storage_buffer_bindings(self, count: int) -> None:
        """Validate shader storage buffer bindings count against hardware limits.

        Args:
            count: Number of shader storage buffer bindings to validate.

        Raises:
            ValueError: If count exceeds maximum shader storage buffer bindings.
        """
        max_count = self.get_max_shader_storage_buffer_bindings()
        if count > max_count:
            raise ValueError(f"Shader storage buffer bindings count {count} exceeds maximum {max_count}")

    def validate_framebuffer_color_attachments(self, count: int) -> None:
        """Validate framebuffer color attachments count against hardware limits.

        Args:
            count: Number of color attachments to validate.

        Raises:
            ValueError: If count exceeds maximum framebuffer color attachments.
        """
        max_count = self.get_max_framebuffer_color_attachments()
        if count > max_count:
            raise ValueError(f"Framebuffer color attachments count {count} exceeds maximum {max_count}")

    def validate_samples(self, count: int) -> None:
        """Validate multisampling samples count against hardware limits.

        Args:
            count: Number of samples to validate.

        Raises:
            ValueError: If count exceeds maximum samples.
        """
        max_count = self.get_max_samples()
        if count > max_count:
            raise ValueError(f"Samples count {count} exceeds maximum {max_count}")

    def validate_compute_work_group_size(self, size: int) -> None:
        """Validate compute work group size against hardware limits.

        Args:
            size: Work group size to validate.

        Raises:
            ValueError: If size exceeds maximum compute work group size.
        """
        max_size = self.get_max_compute_work_group_size()
        if size > max_size:
            raise ValueError(f"Compute work group size {size} exceeds maximum {max_size}")

    def validate_compute_work_group_invocations(self, count: int) -> None:
        """Validate compute work group invocations against hardware limits.

        Args:
            count: Work group invocations to validate.

        Raises:
            ValueError: If count exceeds maximum compute work group invocations.
        """
        max_count = self.get_max_compute_work_group_invocations()
        if count > max_count:
            raise ValueError(f"Compute work group invocations {count} exceeds maximum {max_count}")

    def invalidate_cache(self) -> None:
        """Invalidate the cached limits to force re-querying."""
        self._cached_limits = None
        logger.debug("Limits cache invalidated")
