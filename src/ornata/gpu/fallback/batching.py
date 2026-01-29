"""CPU-based batching system for software rendering."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from ornata.api.exports.definitions import BatchedGeometry, BatchKey
from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.definitions import Geometry
    from ornata.gpu.misc import GPUBackend, Shader

logger = get_logger(__name__)


class GeometryBatch:
    """Batch of geometries sharing the same shader and state."""

    def __init__(self, key: BatchKey, max_vertices: int = 65536, max_indices: int = 98304) -> None:
        """Initialize geometry batch.

        Args:
            key: Batch key identifying shader and state.
            max_vertices: Maximum vertices per batch.
            max_indices: Maximum indices per batch.
        """
        self.key = key
        self.max_vertices = max_vertices
        self.max_indices = max_indices
        self.vertices: list[float] = []
        self.indices: list[int] = []
        self.geometries: list[BatchedGeometry] = []
        self.vertex_count = 0
        self.index_count = 0
        self._lock = threading.RLock()

    def can_add(self, geometry: Geometry) -> bool:
        """Check if geometry can be added to this batch.

        Args:
            geometry: Geometry to check.

        Returns:
            True if geometry can be added.
        """
        return (self.vertex_count + geometry.vertex_count <= self.max_vertices and
                self.index_count + geometry.index_count <= self.max_indices)

    def add_geometry(self, geometry: Geometry) -> bool:
        """Add geometry to batch.

        Args:
            geometry: Geometry to add.

        Returns:
            True if added successfully, False if batch is full.
        """
        with self._lock:
            if not self.can_add(geometry):
                return False

            batched_geom = BatchedGeometry(
                vertices=geometry.vertices.copy(),
                indices=geometry.indices.copy(),
                vertex_offset=self.vertex_count,
                index_offset=self.index_count,
                vertex_count=geometry.vertex_count,
                index_count=geometry.index_count
            )

            adjusted_indices = [idx + self.vertex_count for idx in geometry.indices]

            self.vertices.extend(geometry.vertices)
            self.indices.extend(adjusted_indices)
            self.geometries.append(batched_geom)

            self.vertex_count += geometry.vertex_count
            self.index_count += geometry.index_count

            return True

    def clear(self) -> None:
        """Clear batch data."""
        with self._lock:
            self.vertices.clear()
            self.indices.clear()
            self.geometries.clear()
            self.vertex_count = 0
            self.index_count = 0

    def is_empty(self) -> bool:
        """Check if batch is empty.

        Returns:
            True if batch contains no geometries.
        """
        return self.vertex_count == 0


class CPUFallbackBatcher:
    """CPU-based batching system for software rendering."""

    def __init__(self, backend: GPUBackend) -> None:
        """Initialize CPU fallback batcher.

        Args:
            backend: GPU backend for rendering.
        """
        self.backend = backend
        self.batches: dict[BatchKey, GeometryBatch] = {}
        self._lock = threading.RLock()
        self.max_batch_size = 65536  # vertices

    def submit_geometry(self, geometry: Geometry, shader: Shader,
                        texture_id: int | None = None, blend_mode: str = "normal") -> None:
        """Submit geometry for batched CPU rendering.

        Args:
            geometry: Geometry to render.
            shader: Shader to use.
            texture_id: Texture ID if applicable.
            blend_mode: Blend mode for rendering.
        """
        key = BatchKey(shader.name, texture_id, blend_mode)

        with self._lock:
            if key not in self.batches:
                self.batches[key] = GeometryBatch(key, max_vertices=self.max_batch_size)

            batch = self.batches[key]

            if not batch.add_geometry(geometry):
                # Batch is full, render it and start new batch
                self._render_batch(batch, shader)
                batch.clear()
                batch.add_geometry(geometry)

    def flush(self) -> None:
        """Flush all pending batches to CPU rendering."""
        with self._lock:
            for batch in self.batches.values():
                if not batch.is_empty():
                    shader = self.backend.shaders.get(batch.key.shader_name)
                    if shader:
                        self._render_batch(batch, shader)
                    batch.clear()

            self.batches.clear()

    def _render_batch(self, batch: GeometryBatch, shader: Shader) -> None:
        """Render a single batch using CPU backend.

        Args:
            batch: Batch to render.
            shader: Shader to use.
        """
        if batch.is_empty():
            return

        try:
            from ornata.api.exports.definitions import Geometry
            batch_geometry = Geometry(
                vertices=batch.vertices,
                indices=batch.indices,
                vertex_count=batch.vertex_count,
                index_count=batch.index_count
            )

            self.backend.render_geometry(batch_geometry, shader)

            logger.debug(
                f"Rendered CPU batch with {batch.vertex_count} vertices, "
                f"{len(batch.geometries)} geometries"
            )
        except Exception as e:
            logger.warning(f"Failed to render CPU batch: {e}")