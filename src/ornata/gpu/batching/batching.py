"""GPU batching system for optimized rendering."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

from ornata.api.exports.definitions import BatchedGeometry, BatchKey, Geometry, PersistentBuffer
from ornata.api.exports.utils import get_logger
from ornata.gpu.instancing.instancing import InstanceDetector, InstanceGroup

if TYPE_CHECKING:
    from ornata.gpu.misc import GPUBackend, Shader

logger = get_logger(__name__)

# Geometry count thresholds for batching decisions
GEOMETRY_BATCH_THRESHOLD_MIN = 5  # Minimum geometries to consider batching
GEOMETRY_BATCH_THRESHOLD_MAX = 100  # Maximum geometries per batch before flush
GEOMETRY_COUNT_THRESHOLD_SMALL = 10  # Threshold for small batch optimization


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

            # Store original geometry info
            batched_geom = BatchedGeometry(
                vertices=geometry.vertices.copy(),
                indices=geometry.indices.copy(),
                vertex_offset=self.vertex_count,
                index_offset=self.index_count,
                vertex_count=geometry.vertex_count,
                index_count=geometry.index_count
            )

            # Adjust indices for vertex offset
            adjusted_indices = [idx + self.vertex_count for idx in geometry.indices]

            # Add to batch
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


class RenderBatcher:
    """Manages batched rendering for optimal GPU performance with adaptive batching."""

    def __init__(self, backend: GPUBackend) -> None:
        """Initialize render batcher.

        Args:
            backend: GPU backend for rendering.
        """
        self.backend = backend
        self.batches: dict[BatchKey, GeometryBatch] = {}
        self._lock = threading.RLock()
        self.max_batch_size = 65536  # vertices
        self.instance_detector = InstanceDetector()  # For detecting repeated UI elements
        self._batch_cache: dict[str, GeometryBatch] = {}  # Cache for frequently used batches

        # Persistent buffer management for GPU optimization
        self._persistent_buffers: dict[str, PersistentBuffer] = {}
        self._buffer_pool: list[PersistentBuffer] = []
        self._max_persistent_buffers = 50  # Limit persistent buffer count

    def submit_geometry(self, geometry: Geometry, shader: Shader,
                        texture_id: int | None = None, blend_mode: str = "normal") -> None:
        """Submit geometry for batched rendering with optimized small batch handling.

        Args:
            geometry: Geometry to render.
            shader: Shader to use.
            texture_id: Texture ID if applicable.
            blend_mode: Blend mode for rendering.
        """
        key = BatchKey(shader.name, texture_id, blend_mode)
        cache_key = f"{shader.name}_{texture_id}_{blend_mode}"

        with self._lock:
            # Check batch cache first for frequently used configurations
            if cache_key in self._batch_cache:
                batch = self._batch_cache[cache_key]
                if batch.add_geometry(geometry):
                    return
                # Cache batch is full, render and clear it
                self._render_batch(batch, shader)
                batch.clear()
                batch.add_geometry(geometry)
                return

            # Get or create batch
            if key not in self.batches:
                self.batches[key] = GeometryBatch(key, max_vertices=self.max_batch_size)

            batch = self.batches[key]

            # Try to add to existing batch
            if not batch.add_geometry(geometry):
                # Batch is full, render it and start new batch
                self._render_batch(batch, shader)
                batch.clear()

                # Create new batch and add geometry
                new_batch = GeometryBatch(key, max_vertices=self.max_batch_size)
                new_batch.add_geometry(geometry)
                self.batches[key] = new_batch

                # Cache frequently used batch configurations
                if len(self.batches) <= 10:  # Limit cache size
                    self._batch_cache[cache_key] = new_batch

    def flush(self) -> None:
        """Flush all pending batches to GPU."""
        with self._lock:
            # Process instanced rendering groups first
            instance_groups = self.instance_detector.get_instance_groups()
            for group in instance_groups:
                if group.base_geometry:
                    # Render instanced group
                    self._render_instanced_group(group)

            for batch in self.batches.values():
                if not batch.is_empty():
                    # Get shader for this batch with proper error handling
                    shader = self.backend.shaders_.get(batch.key.shader_name)
                    if shader is None:
                        logger.error(f"Shader '{batch.key.shader_name}' not found for batch rendering")
                        batch.clear()
                        continue
                    
                    try:
                        self._render_batch(batch, shader)
                    except Exception as e:
                        logger.error(f"Failed to render batch with shader '{batch.key.shader_name}': {e}")
                        # Continue with next batch instead of crashing
                        batch.clear()
                        continue
                    batch.clear()

            self.batches.clear()
            self.instance_detector.clear()

    def _render_batch(self, batch: GeometryBatch, shader: Shader) -> None:
        """Render a single batch using persistent GPU buffers.

        Args:
            batch: Batch to render.
            shader: Shader to use.
        """
        if batch.is_empty():
            return

        try:
            # Get or create persistent buffer for this batch key
            buffer_key = f"{batch.key.shader_name}_{batch.key.texture_id}_{batch.key.blend_mode}"
            persistent_buffer = self._get_persistent_buffer(buffer_key, batch)

            # Update GPU buffers if data has changed
            if persistent_buffer.is_dirty:
                self._upload_batch_to_gpu(persistent_buffer, batch)

            # Bind shader
            shader.bind()

            # Render using persistent GPU buffers
            self._render_persistent_batch(persistent_buffer, shader)

            logger.debug(
                f"Rendered batch with {batch.vertex_count} vertices, "
                f"{len(batch.geometries)} geometries using persistent GPU buffers"
            )
        except Exception as e:
            logger.warning(f"Failed to render batch: {e}")

    def _get_persistent_buffer(self, buffer_key: str, batch: GeometryBatch) -> PersistentBuffer:
        """Get or create a persistent buffer for the batch.

        Args:
            buffer_key: Unique key for buffer identification.
            batch: Batch requiring the buffer.

        Returns:
            PersistentBuffer instance ready for use.
        """
        # Check if buffer already exists
        if buffer_key in self._persistent_buffers:
            buffer = self._persistent_buffers[buffer_key]
            # Check if buffer can accommodate the batch
            if buffer.can_fit_geometry(Geometry(
                vertices=batch.vertices,
                indices=batch.indices,
                vertex_count=batch.vertex_count,
                index_count=batch.index_count
            )):
                return buffer
            else:
                # Buffer too small, remove and create new one
                self._return_persistent_buffer(buffer)
                del self._persistent_buffers[buffer_key]

        # Try to reuse from pool
        for buffer in self._buffer_pool:
            if buffer.can_fit_geometry(Geometry(
                vertices=batch.vertices,
                indices=batch.indices,
                vertex_count=batch.vertex_count,
                index_count=batch.index_count
            )):
                self._buffer_pool.remove(buffer)
                self._persistent_buffers[buffer_key] = buffer
                return buffer

        # Create new persistent buffer
        buffer = PersistentBuffer()
        self._persistent_buffers[buffer_key] = buffer
        return buffer

    def _upload_batch_to_gpu(self, buffer: PersistentBuffer, batch: GeometryBatch) -> None:
        """Upload batch geometry to persistent GPU buffers with backend-specific implementation.

        Args:
            buffer: Persistent buffer to upload to.
            batch: Batch geometry to upload.
        """
        backend: Any = self.backend
        try:
            # Create GPU buffers if they don't exist - backend-specific implementation
            if buffer.vertex_buffer is None:
                try:
                    # Backend-specific vertex buffer creation
                    if hasattr(backend, 'create_vertex_buffer'):
                        logger.info("Creating vertex buffer.")
                        buffer.vertex_buffer = backend.create_vertex_buffer(batch.vertices, "static")
                    elif hasattr(backend, 'vertex_buffer_manager'):
                        logger.info("Using the vertex buffer manager to create a vertex buffer.")
                        buffer.vertex_buffer = backend.vertex_buffer_manager.create_buffer(batch.vertices, "static")
                    else:
                        # Fallback: Create buffer using generic buffer management
                        buffer.vertex_buffer = self._create_backend_vertex_buffer(batch.vertices)
                    
                    buffer.vertex_data = batch.vertices.copy()
                except Exception as e:
                    logger.warning(f"Failed to create vertex buffer, using CPU fallback: {e}")
                    buffer.vertex_buffer = None

            if buffer.index_buffer is None:
                try:
                    # Backend-specific index buffer creation
                    if hasattr(backend, 'create_index_buffer'):
                        logger.info("Creating an index buffer.")
                        buffer.index_buffer = backend.create_index_buffer(batch.indices, "static")
                    elif hasattr(backend, 'index_buffer_manager'):
                        logger.info("Using the index buffer manager to create an index buffer.")
                        buffer.index_buffer = backend.index_buffer_manager.create_buffer(batch.indices, "static")
                    else:
                        # Fallback: Create buffer using generic buffer management
                        buffer.index_buffer = self._create_backend_index_buffer(batch.indices)
                    
                    buffer.index_data = batch.indices.copy()
                except Exception as e:
                    logger.warning(f"Failed to create index buffer, using CPU fallback: {e}")
                    buffer.index_buffer = None

            # Update existing buffers if data changed with proper error handling
            if buffer.vertex_buffer and buffer.vertex_data != batch.vertices:
                try:
                    # Backend-specific buffer update
                    if hasattr(buffer.vertex_buffer, 'update_data'):
                        buffer.vertex_buffer.update_data(batch.vertices)
                    elif hasattr(self.backend, 'update_vertex_buffer'):
                        self.backend.update_vertex_buffer(buffer.vertex_buffer, batch.vertices)
                    else:
                        # Fallback: recreate buffer
                        buffer.vertex_buffer = self._create_backend_vertex_buffer(batch.vertices)
                    
                    buffer.vertex_data = batch.vertices.copy()
                except Exception as e:
                    logger.warning(f"Failed to update vertex buffer, continuing with CPU data: {e}")

            if buffer.index_buffer and buffer.index_data != batch.indices:
                try:
                    # Backend-specific buffer update
                    if hasattr(buffer.index_buffer, 'update_data'):
                        buffer.index_buffer.update_data(batch.indices)
                    elif hasattr(self.backend, 'update_index_buffer'):
                        self.backend.update_index_buffer(buffer.index_buffer, batch.indices)
                    else:
                        # Fallback: recreate buffer
                        buffer.index_buffer = self._create_backend_index_buffer(batch.indices)
                    
                    buffer.index_data = batch.indices.copy()
                except Exception as e:
                    logger.warning(f"Failed to update index buffer, continuing with CPU data: {e}")

            buffer.current_vertices = batch.vertex_count
            buffer.current_indices = batch.index_count
            buffer.is_dirty = False

            logger.debug(f"Uploaded batch to persistent GPU buffers: {buffer.current_vertices} vertices, {buffer.current_indices} indices")

        except Exception as e:
            logger.warning(f"Failed to upload batch to GPU buffers: {e}")
            # Fall back to CPU rendering for this batch
            buffer.is_dirty = True  # Mark as dirty to retry next time
            buffer.vertex_buffer = None
            buffer.index_buffer = None

    def _render_persistent_batch(self, buffer: PersistentBuffer, shader: Shader) -> None:
        """Render using persistent GPU buffers.

        Args:
            buffer: Persistent buffer containing geometry.
            shader: Shader to use for rendering.
        """
        try:
            # Bind persistent buffers
            if buffer.vertex_buffer and hasattr(buffer.vertex_buffer, 'bind'):
                buffer.vertex_buffer.bind()
            if buffer.index_buffer and hasattr(buffer.index_buffer, 'bind'):
                buffer.index_buffer.bind()

            # Create geometry from buffer data
            geometry = Geometry(
                vertices=buffer.vertex_data or [],
                indices=buffer.index_data or [],
                vertex_count=buffer.current_vertices,
                index_count=buffer.current_indices
            )

            # Render using backend
            self.backend.render_geometry(geometry, shader)

        except Exception as e:
            logger.warning(f"Failed to render persistent batch: {e}")
            # Fall back to creating temporary geometry
            if buffer.vertex_data and buffer.index_data:
                temp_geometry = Geometry(
                    vertices=buffer.vertex_data,
                    indices=buffer.index_data,
                    vertex_count=buffer.current_vertices,
                    index_count=buffer.current_indices
                )
                self.backend.render_geometry(temp_geometry, shader)

    def _return_persistent_buffer(self, buffer: PersistentBuffer) -> None:
        """Return a persistent buffer to the pool for reuse.

        Args:
            buffer: Buffer to return to pool.
        """
        if len(self._buffer_pool) < self._max_persistent_buffers:
            # Clear buffer data but keep GPU resources for reuse
            buffer.clear()
            buffer.is_dirty = True
            self._buffer_pool.append(buffer)
        else:
            # Pool full, clean up GPU resources
            self._cleanup_persistent_buffer(buffer)

    def _cleanup_persistent_buffer(self, buffer: PersistentBuffer) -> None:
        """Clean up GPU resources associated with a persistent buffer.

        Args:
            buffer: Buffer to clean up.
        """
        try:
            # Clean up GPU buffer resources if they exist
            if buffer.vertex_buffer and hasattr(buffer.vertex_buffer, 'cleanup'):
                buffer.vertex_buffer.cleanup()
            if buffer.index_buffer and hasattr(buffer.index_buffer, 'cleanup'):
                buffer.index_buffer.cleanup()

            # Clear references
            buffer.vertex_buffer = None
            buffer.index_buffer = None
            buffer.vertex_data = None
            buffer.index_data = None
            buffer.current_vertices = 0
            buffer.current_indices = 0
            buffer.is_dirty = False

            logger.debug("Cleaned up persistent buffer GPU resources")

        except Exception as e:
            logger.warning(f"Error cleaning up persistent buffer: {e}")

    def clear(self) -> None:
        """Clear all batches without rendering."""
        with self._lock:
            for batch in self.batches.values():
                batch.clear()
            self.batches.clear()
            self._batch_cache.clear()
            self.instance_detector.clear()

    def _render_instanced_group(self, group: InstanceGroup) -> None:
        """Render an instanced group using GPU instancing.

        Args:
            group: Instance group to render.
        """
        if not group.base_geometry or not group.transforms:
            return

        try:
            # Get appropriate shader for instanced rendering
            shader_name = f"{group.identity.component_name}_instanced"
            shader = self.backend.shaders_.get(shader_name)
            if not shader:
                # Fallback to default shader
                shader = self.backend.shaders_.get("default")
                if not shader:
                    logger.warning(
                        f"No suitable shader found for instanced rendering of "
                        f"{group.identity.component_name}"
                    )
                    return

            # Bind shader
            shader.bind()

            # Prepare instance data (transforms)
            instance_data: list[float] = []
            for transform in group.transforms:
                instance_data.extend([
                    transform.x, transform.y,
                    transform.scale_x, transform.scale_y,
                    transform.rotation
                ])

            # Render instances with single draw call
            self.backend.render_instanced_geometry(
                group.base_geometry,
                instance_data,
                group.component_count,
                shader
            )

            logger.debug(
                f"Rendered instanced group with {group.component_count} "
                f"instances of {group.identity.component_name}"
            )

        except Exception as e:
            # If instanced rendering fails, log and continue without crashing.
            logger.warning(f"Failed to render instanced group: {e}")
    def _create_backend_vertex_buffer(self, data: list[float]) -> Any:
        """Create vertex buffer using backend-specific methods.

        Args:
            data: Vertex data to create buffer with.

        Returns:
            Backend-specific vertex buffer handle or None if creation fails.
        """
        backend: Any = self.backend
        try:
            # Try to use buffer management from the backend
            if hasattr(backend, 'buffers'):
                # Look for vertex buffer manager
                if hasattr(backend.buffers, 'vertex_buffers'):
                    logger.info("Creating vertex buffer using vertex_buffers manager.")
                    return backend.buffers.vertex_buffers.create(data, "static")
            
            # Try generic buffer creation through the backend interface
            if hasattr(backend, 'create_buffer'):
                logger.info("Creating vertex buffer using create_buffer.")
                return backend.create_buffer(data, "vertex", "static")
            
            # Try hardware buffer manager if available
            if hasattr(backend, 'hardware_buffer_manager'):
                logger.info("Creating vertex buffer using hardware buffer manager.")
                return backend.hardware_buffer_manager.create_vertex_buffer(data)
            
            # Final fallback - create a simple wrapper object
            class SimpleVertexBuffer:
                def __init__(self, vertex_data: list[float]) -> None:
                    self.data = vertex_data
                    self.size = len(vertex_data) * 4  # Assuming float32
                
                def update_data(self, new_data: list[float]) -> None:
                    self.data = new_data
                    self.size = len(new_data) * 4
                
                def bind(self) -> None:
                    pass  # No-op for fallback
            
            return SimpleVertexBuffer(data)
            
        except Exception as e:
            logger.warning(f"Failed to create backend vertex buffer: {e}")
            return None

    def _create_backend_index_buffer(self, data: list[int]) -> Any:
        """Create index buffer using backend-specific methods.

        Args:
            data: Index data to create buffer with.

        Returns:
            Backend-specific index buffer handle or None if creation fails.
        """
        backend: Any = self.backend
        try:
            # Try to use buffer management from the backend
            if hasattr(backend, 'buffers'):
                # Look for index buffer manager
                if hasattr(backend.buffers, 'index_buffers'):
                    logger.info("Creating index buffer using the buffer manager.")
                    return backend.buffers.index_buffers.create(data, "static")
            
            # Try generic buffer creation through the backend interface
            if hasattr(backend, 'create_buffer'):
                logger.info("Creating a index buffer using create_buffer.")
                return backend.create_buffer(data, "index", "static")
            
            # Try hardware buffer manager if available
            if hasattr(backend, 'hardware_buffer_manager'):
                logger.info("Creating an index buffer using hardware buffer manager.")
                return backend.hardware_buffer_manager.create_index_buffer(data)
            
            # Final fallback - create a simple wrapper object
            class SimpleIndexBuffer:
                def __init__(self, index_data: list[int]) -> None:
                    self.data = index_data
                    self.size = len(index_data) * 4  # Assuming uint32
                
                def update_data(self, new_data: list[int]) -> None:
                    self.data = new_data
                    self.size = len(new_data) * 4
                
                def bind(self) -> None:
                    pass  # No-op for fallback
            
            return SimpleIndexBuffer(data)
            
        except Exception as e:
            logger.warning(f"Failed to create backend index buffer: {e}")
            return None

    def cleanup(self) -> None:
        """Clean up batching resources and persistent buffers."""
        with self._lock:
            # Clear all batches
            for batch in self.batches.values():
                batch.clear()
            self.batches.clear()
            self._batch_cache.clear()
            self.instance_detector.clear()

            # Clean up persistent buffers
            for buffer in self._persistent_buffers.values():
                self._cleanup_persistent_buffer(buffer)
            self._persistent_buffers.clear()

            for buffer in self._buffer_pool:
                self._cleanup_persistent_buffer(buffer)
            self._buffer_pool.clear()

            logger.debug("Batching system cleaned up")