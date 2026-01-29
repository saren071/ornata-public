"""Geometry conversion utilities with caching and optimization."""

from __future__ import annotations

import hashlib
import threading
import time
from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import ThreadSafeLRUCache, get_logger

if TYPE_CHECKING:
    from ornata.api.exports.definitions import Component
    from ornata.gpu.misc import Geometry

logger = get_logger(__name__)


class GeometryConverter:
    """Handles conversion of components to GPU geometry with caching and optimization."""

    def __init__(self, cache_size: int = 1000) -> None:
        """Initialize the geometry converter.

        Args:
            cache_size: Maximum number of geometries to cache.
        """
        from ornata.api.exports.definitions import Geometry
        from ornata.api.exports.utils import ThreadSafeMemoryPool
        self._geometry_cache: ThreadSafeLRUCache[str, Any] = ThreadSafeLRUCache(max_size=cache_size)
        self._geometry_pool: ThreadSafeMemoryPool[Geometry] = ThreadSafeMemoryPool[Geometry](Geometry, max_size=1000)
        self._vertex_pool: ThreadSafeMemoryPool[list[float]] = ThreadSafeMemoryPool[list[float]](list, max_size=1000)
        self._index_pool: ThreadSafeMemoryPool[list[int]] = ThreadSafeMemoryPool[list[int]](list, max_size=1000)

    def component_to_geometry(self, component: Component) -> Geometry:
        """Convert a component to GPU geometry with hash-based caching and collision handling.

        Args:
            component: The renderable component to convert.

        Returns:
            Geometry data suitable for GPU rendering.
        """
        # Generate cache key from component hash
        cache_key = self._calculate_component_hash(component)

        # Check cache first
        cached_geometry: Geometry | None = self._geometry_cache.get(cache_key)
        if cached_geometry is not None:
            logger.debug(f"Geometry cache hit for component {type(component).__name__}")
            return cached_geometry

        logger.debug(f"Geometry cache miss for component {type(component).__name__}, generating geometry")

        # Generate geometry
        geometry = self._generate_component_geometry(component)

        # Handle potential hash collisions by verifying geometry matches component
        if cached_geometry := self._geometry_cache.get(cache_key):
            # Collision detected - verify if geometry matches
            if not self._geometry_matches_component(cached_geometry, component):
                logger.warning(f"Hash collision detected for component {type(component).__name__}, regenerating geometry")
                # Force regeneration with different key (append timestamp for uniqueness)
                cache_key = f"{cache_key}_{int(time.time() * 1000000)}"
            else:
                return cached_geometry

        # Cache the generated geometry
        self._geometry_cache.set(cache_key, geometry)

        return geometry

    def _calculate_component_hash(self, component: Component) -> str:
        """Calculate a hash for component geometry caching.

        Args:
            component: The component to hash.

        Returns:
            String hash representing the component's geometry characteristics.
        """
        # Use component type and key properties for hash
        component_type = type(component).__name__
        component_id = getattr(component, 'id', None) or id(component)

        # Include child count for nested components
        try:
            child_count = len(list(component.iter_children()))
        except (AttributeError, TypeError):
            child_count = 0

        # Create hash from key characteristics
        hash_input = f"{component_type}_{component_id}_{child_count}"
        return hashlib.md5(hash_input.encode()).hexdigest()

    def _generate_component_geometry(self, component: Component) -> Geometry:
        """Generate geometry for a component using pooled vertex/index data.

        Args:
            component: The renderable component to convert.

        Returns:
            Geometry data suitable for GPU rendering.
        """

        # Try to measure component, fallback to default size if not supported
        try:
            measure = component.measure()
            width = float(measure.width)
            height = float(measure.height)
        except AttributeError:
            # Component doesn't support measurement, use default dimensions
            logger.debug(f"Component {type(component).__name__} doesn't support measurement, using defaults")
            width = 100.0  # Default width
            height = 20.0  # Default height

        # For nested components, optimize by flattening geometry where possible
        children = component.iter_children()
        if children:
            # Calculate total geometry for nested components to reduce draw calls
            total_vertices: list[float] = []
            total_indices: list[int] = []
            vertex_offset = 0

            # Add parent geometry first
            parent_vertices = [
                0.0, 0.0, 0.0, 0.0, 0.0,  # Bottom-left
                width, 0.0, 0.0, 1.0, 0.0,  # Bottom-right
                width, height, 0.0, 1.0, 1.0,  # Top-right
                0.0, height, 0.0, 0.0, 1.0,  # Top-left
            ]
            parent_indices = [0, 1, 2, 2, 3, 0]
            total_vertices.extend(parent_vertices)
            total_indices.extend(parent_indices)
            vertex_offset += 4

            # Add child geometries with offset positioning
            for child in children:
                try:
                    child_measure = child.measure()
                    child_width = float(child_measure.width)
                    child_height = float(child_measure.height)
                    # Position child relative to parent (simplified layout)
                    child_x_offset = 0.0  # Could be enhanced with actual layout logic
                    child_y_offset = 0.0

                    child_vertices = [
                        child_x_offset, child_y_offset, 0.0, 0.0, 0.0,
                        child_x_offset + child_width, child_y_offset, 0.0, 1.0, 0.0,
                        child_x_offset + child_width, child_y_offset + child_height, 0.0, 1.0, 1.0,
                        child_x_offset, child_y_offset + child_height, 0.0, 0.0, 1.0,
                    ]
                    child_indices = [vertex_offset, vertex_offset + 1, vertex_offset + 2,
                                    vertex_offset + 2, vertex_offset + 3, vertex_offset]

                    total_vertices.extend(child_vertices)
                    total_indices.extend(child_indices)
                    vertex_offset += 4
                except AttributeError:
                    logger.debug(f"Child component {type(child).__name__} doesn't support measurement, skipping")

            # Use pooled vertex and index data
            pooled_vertices: list[float] = self._vertex_pool.acquire()
            pooled_indices: list[int] = self._index_pool.acquire()
            if hasattr(pooled_vertices, 'clear'):
                pooled_vertices.clear()
            if hasattr(pooled_indices, 'clear'):
                pooled_indices.clear()
            pooled_vertices.extend(total_vertices)
            pooled_indices.extend(total_indices)
            from ornata.api.exports.definitions import Geometry

            return Geometry(vertices=pooled_vertices, indices=pooled_indices,
                            vertex_count=len(total_vertices) // 5, index_count=len(total_indices))
        else:
            # Simple quad for leaf components - use pooled data
            vertices = [
                0.0, 0.0, 0.0, 0.0, 0.0,  # Bottom-left
                width, 0.0, 0.0, 1.0, 0.0,  # Bottom-right
                width, height, 0.0, 1.0, 1.0,  # Top-right
                0.0, height, 0.0, 0.0, 1.0,  # Top-left
            ]
            indices = [0, 1, 2, 2, 3, 0]

            # Use pooled vertex and index data
            pooled_vertices = self._vertex_pool.acquire()
            pooled_indices = self._index_pool.acquire()
            if hasattr(pooled_vertices, 'clear'):
                pooled_vertices.clear()
            if hasattr(pooled_indices, 'clear'):
                pooled_indices.clear()
            pooled_vertices.extend(vertices)
            pooled_indices.extend(indices)
            from ornata.api.exports.definitions import Geometry
            return Geometry(vertices=pooled_vertices, indices=pooled_indices, vertex_count=4, index_count=6)

    def _geometry_matches_component(self, geometry: Geometry, component: Component) -> bool:
        """Verify if cached geometry matches the component characteristics.

        Args:
            geometry: The cached geometry to verify.
            component: The component to check against.

        Returns:
            True if geometry matches component, False otherwise.
        """
        try:
            expected_vertex_count = 4  # Base quad

            # For nested components, add child geometries
            children = list(component.iter_children())
            expected_vertex_count += len(children) * 4

            return geometry.vertex_count == expected_vertex_count
        except (AttributeError, TypeError):
            # If measurement fails, assume mismatch to be safe
            return False

    def invalidate_cache(self) -> None:
        """Invalidate all cached geometries to force regeneration."""
        self._geometry_cache.clear()
        logger.debug("Geometry cache invalidated")

    def get_cache_stats(self) -> dict[str, int | float]:
        """Get statistics about the geometry cache performance.

        Returns:
            Dictionary containing cache statistics including size, hits, misses, and hit rate.
        """
        return self._geometry_cache.stats()

    def cleanup(self) -> None:
        """Clean up geometry converter resources."""
        self._geometry_cache.clear()
        self._geometry_pool.pool.clear()
        self._vertex_pool.pool.clear()
        self._index_pool.pool.clear()
        logger.debug("Geometry converter cleaned up")


# Global geometry converter singleton
_geometry_converter_singleton: GeometryConverter | None = None
_geometry_converter_lock = threading.Lock()


def get_geometry_converter() -> GeometryConverter:
    """Return the process-wide geometry converter singleton.

    Returns:
        GeometryConverter: Shared converter instance reused across render calls.
    """
    global _geometry_converter_singleton
    with _geometry_converter_lock:
        if _geometry_converter_singleton is None:
            _geometry_converter_singleton = GeometryConverter()
        return _geometry_converter_singleton


def component_to_gpu_geometry(component: Component) -> Geometry:
    """Convert a component to GPU geometry with caching and optimization.

    Args:
        component: The renderable component to convert.

    Returns:
        Geometry data suitable for GPU rendering.
    """
    converter = get_geometry_converter()
    return converter.component_to_geometry(component)


def cpu_render(component: Component, target_surface: Any) -> None:
    """CPU-based rendering fallback.

    Args:
        component: Component to render using software path.
        target_surface: Render target for CPU fallback.
    """
    # Placeholder implementation - would perform software rendering
    logger.debug("Performing CPU-based rendering")
