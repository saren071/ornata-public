"""GPU capabilities detection and querying."""

from __future__ import annotations

import platform
from typing import TYPE_CHECKING

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.gpu.misc import GPUBackend

logger = get_logger(__name__)


class Capabilities:
    """Queries GPU features and capabilities with cross-platform compatibility."""

    def __init__(self, backend: GPUBackend | None = None) -> None:
        """Initialize capabilities detector.

        Args:
            backend: GPU backend to query. If None, uses default detection.
        """
        self._backend = backend
        self._cached_capabilities: dict[str, bool | int] | None = None

    def supports_instancing(self) -> bool:
        """Check if the GPU backend supports geometry instancing.

        Returns:
            True if instancing is supported, False otherwise.
        """
        capability = self._get_capability("instancing", False)
        if isinstance(capability, bool):
            return capability
        return False

    def supports_compute_shaders(self) -> bool:
        """Check if the GPU backend supports compute shaders.

        Returns:
            True if compute shaders are supported, False otherwise.
        """
        capability = self._get_capability("compute_shaders", False)
        if isinstance(capability, bool):
            return capability
        return False

    def supports_geometry_shaders(self) -> bool:
        """Check if the GPU backend supports geometry shaders.

        Returns:
            True if geometry shaders are supported, False otherwise.
        """
        capability = self._get_capability("geometry_shaders", False)
        if isinstance(capability, bool):
            return capability
        return False

    def supports_tessellation(self) -> bool:
        """Check if the GPU backend supports tessellation shaders.

        Returns:
            True if tessellation is supported, False otherwise.
        """
        capability = self._get_capability("tessellation", False)
        if isinstance(capability, bool):
            return capability
        return False

    def supports_multiple_render_targets(self) -> bool:
        """Check if the GPU backend supports multiple render targets.

        Returns:
            True if MRT is supported, False otherwise.
        """
        capability = self._get_capability("multiple_render_targets", False)
        if isinstance(capability, bool):
            return capability
        return False

    def supports_texture_compression(self) -> bool:
        """Check if the GPU backend supports texture compression.

        Returns:
            True if texture compression is supported, False otherwise.
        """
        capability = self._get_capability("texture_compression", False)
        if isinstance(capability, bool):
            return capability
        return False

    def supports_anisotropic_filtering(self) -> bool:
        """Check if the GPU backend supports anisotropic texture filtering.

        Returns:
            True if anisotropic filtering is supported, False otherwise.
        """
        capability = self._get_capability("anisotropic_filtering", False)
        if isinstance(capability, bool):
            return capability
        return False

    def get_max_texture_size(self) -> int:
        """Get the maximum supported texture size.

        Returns:
            Maximum texture dimension in pixels.
        """
        return self._get_capability("max_texture_size", 2048)

    def get_max_renderbuffer_size(self) -> int:
        """Get the maximum supported renderbuffer size.

        Returns:
            Maximum renderbuffer dimension in pixels.
        """
        return self._get_capability("max_renderbuffer_size", 2048)

    def get_max_vertex_attributes(self) -> int:
        """Get the maximum number of vertex attributes.

        Returns:
            Maximum number of vertex attributes supported.
        """
        return self._get_capability("max_vertex_attributes", 16)

    def get_max_texture_units(self) -> int:
        """Get the maximum number of texture units.

        Returns:
            Maximum number of texture units supported.
        """
        return self._get_capability("max_texture_units", 16)

    def get_max_uniform_buffer_bindings(self) -> int:
        """Get the maximum number of uniform buffer bindings.

        Returns:
            Maximum number of uniform buffer bindings supported.
        """
        return self._get_capability("max_uniform_buffer_bindings", 8)

    def get_max_shader_storage_buffer_bindings(self) -> int:
        """Get the maximum number of shader storage buffer bindings.

        Returns:
            Maximum number of shader storage buffer bindings supported.
        """
        return self._get_capability("max_shader_storage_buffer_bindings", 8)

    def _get_capability(self, name: str, default: bool | int) -> bool | int:
        """Get a capability value with caching and fallbacks.

        Args:
            name: Capability name to query.
            default: Default value if capability cannot be determined.

        Returns:
            Capability value or default.
        """
        if self._cached_capabilities is None:
            self._cached_capabilities = self._query_capabilities()

        return self._cached_capabilities.get(name, default)

    def _query_capabilities(self) -> dict[str, bool | int]:
        """Query capabilities from the GPU backend.

        Returns:
            Dictionary of capability names to values.
        """
        capabilities: dict[str, bool | int] = {}

        if self._backend is None:
            # Return conservative defaults when no backend available
            capabilities.update({
                "instancing": False,
                "compute_shaders": False,
                "geometry_shaders": False,
                "tessellation": False,
                "multiple_render_targets": False,
                "texture_compression": False,
                "anisotropic_filtering": False,
                "max_texture_size": 2048,
                "max_renderbuffer_size": 2048,
                "max_vertex_attributes": 16,
                "max_texture_units": 16,
                "max_uniform_buffer_bindings": 8,
                "max_shader_storage_buffer_bindings": 8,
            })
            return capabilities

        try:
            # Query backend-specific capabilities
            if hasattr(self._backend, 'get_capabilities'):
                result = self._backend.get_capabilities()  # dynamic backend-provided dict
                if isinstance(result, dict):
                    # Narrow to expected types to satisfy type checker
                    tmp: dict[str, bool | int] = {}
                    for k, v in result.items():
                        if isinstance(k, str) and (isinstance(v, bool) or isinstance(v, int)):
                            tmp[k] = v
                    capabilities.update(tmp)
            else:
                # Fallback to basic capability detection
                capabilities.update(self._detect_basic_capabilities())
        except Exception as e:
            logger.warning(f"Failed to query GPU capabilities: {e}")
            # Fall back to conservative defaults
            capabilities.update({
                "instancing": False,
                "compute_shaders": False,
                "geometry_shaders": False,
                "tessellation": False,
                "multiple_render_targets": False,
                "texture_compression": False,
                "anisotropic_filtering": False,
                "max_texture_size": 2048,
                "max_renderbuffer_size": 2048,
                "max_vertex_attributes": 16,
                "max_texture_units": 16,
                "max_uniform_buffer_bindings": 8,
                "max_shader_storage_buffer_bindings": 8,
            })

        return capabilities

    def _detect_basic_capabilities(self) -> dict[str, bool | int]:
        """Detect basic capabilities based on platform and backend type.

        Returns:
            Dictionary of basic capability detections.
        """
        capabilities: dict[str, bool | int] = {}
        system = platform.system()

        # Basic capability assumptions based on platform
        if system == "Windows":
            capabilities.update({
                "instancing": True,  # Most modern Windows GPUs support this
                "compute_shaders": True,
                "geometry_shaders": True,
                "tessellation": True,
                "multiple_render_targets": True,
                "texture_compression": True,
                "anisotropic_filtering": True,
                "max_texture_size": 16384,
                "max_renderbuffer_size": 16384,
                "max_vertex_attributes": 32,
                "max_texture_units": 32,
                "max_uniform_buffer_bindings": 16,
                "max_shader_storage_buffer_bindings": 16,
            })

        return capabilities

    def invalidate_cache(self) -> None:
        """Invalidate the cached capabilities to force re-querying."""
        self._cached_capabilities = None
        logger.debug("Capabilities cache invalidated")
