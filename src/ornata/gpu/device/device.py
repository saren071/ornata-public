"""GPU device management and rendering functionality."""

from __future__ import annotations

import threading
import weakref
from typing import TYPE_CHECKING, Any

from ornata.api.exports.definitions import Geometry
from ornata.api.exports.utils import ThreadSafeLRUCache, get_logger

if TYPE_CHECKING:
    from ornata.api.exports.definitions import Component
    from ornata.gpu.buffers.index import IndexBuffer
    from ornata.gpu.buffers.vertex import VertexBuffer
    from ornata.gpu.device.capabilities import Capabilities
    from ornata.gpu.device.limits import Limits
    from ornata.gpu.misc import GPUBackend, Shader

logger = get_logger(__name__)


class DeviceManager:
    """Manages GPU device lifecycle, backend selection, and rendering operations."""

    def __init__(self) -> None:
        """Initialize the device manager."""
        # Backend and capabilities
        from ornata.gpu.device import Capabilities, DeviceSelector, Limits
        self._backend: GPUBackend | None = None
        self._capabilities = Capabilities()
        self._limits = Limits()
        self._selection = DeviceSelector()

        # Fallback
        from ornata.gpu.fallback.cpu_fallback import CPUFallback
        self._fallback = CPUFallback()

        # Threading
        self._lock = threading.RLock()

        # Shader management
        self._shaders: dict[str, Shader] = {}

        # Memory pools for buffer reuse
        from ornata.api.exports.utils import ThreadSafeMemoryPool
        self._geometry_pool = ThreadSafeMemoryPool[Geometry](Geometry, max_size=1000)
        self._vertex_pool = ThreadSafeMemoryPool[list[float]](list, max_size=1000)
        self._index_pool = ThreadSafeMemoryPool[list[int]](list, max_size=1000)

        # Buffer pools for GPU buffer reuse between frames (backend-aware)
        from ornata.gpu.buffers import IndexBuffer, VertexBuffer
        self._vertex_buffer_pool = ThreadSafeMemoryPool[VertexBuffer](VertexBuffer, max_size=500)
        self._index_buffer_pool = ThreadSafeMemoryPool[IndexBuffer](IndexBuffer, max_size=500)

        # Backend-specific buffer tracking for proper cleanup
        self._backend_vertex_buffers: dict[str, set[VertexBuffer]] = {}
        self._backend_index_buffers: dict[str, set[IndexBuffer]] = {}

        # Component hash-based geometry cache for performance optimization
        self._geometry_cache: ThreadSafeLRUCache[int, Any] = ThreadSafeLRUCache(max_size=1000)

        # Initialization state
        self._initialized = False
        self._default_shader_sources: tuple[str, str] | None = None
        self._context_cache: dict[str, Any] = {}  # Cache for GPU contexts

        # Lazy initialization
        self._lazy_init_threshold = 1  # Initialize GPU immediately for benchmarks
        self._call_count = 0

        # Memory leak detection and monitoring
        self._active_buffers: set[Any] = set()
        self._buffer_weak_refs: list[weakref.ref[Any]] = []
        self._pool_stats = {
            "vertex_buffers_created": 0,
            "vertex_buffers_reused": 0,
            "index_buffers_created": 0,
            "index_buffers_reused": 0,
            "leaks_detected": 0
        }

    def initialize(self) -> None:
        """Initialize the GPU device and backend."""
        with self._lock:
            if self._initialized:
                logger.debug("Device manager already initialized, skipping")
                return

            logger.info("Starting GPU device manager initialization...")

            try:
                # Select and initialize backend
                logger.debug("Selecting GPU backend...")
                self._backend = self._selection.select_backend()
                logger.info(f"Backend selection result: {self._backend}")

                # Update capabilities and limits with backend
                if self._backend is not None:
                    from ornata.gpu.device import Capabilities, Limits
                    logger.debug("Initializing capabilities and limits...")
                    self._capabilities = Capabilities(self._backend)
                    self._limits = Limits(self._backend)
                    logger.debug("Capabilities and limits initialized successfully")
                else:
                    logger.warning("No GPU backend available, will use CPU fallback")

                self._initialized = True
                logger.info("Device manager initialized successfully")

                # Batch compile common shaders upfront for performance
                logger.debug("Starting batch shader compilation...")
                self._batch_compile_common_shaders()
                logger.debug("Batch shader compilation completed")

            except Exception as e:
                logger.error(f"GPU initialization failed: {e}", exc_info=True)
                # Don't set _initialized = True on failure
                raise

    def _ensure_initialized(self) -> None:
        """Ensure the device manager is initialized."""
        if not self._initialized:
            # Lazy initialization: only initialize after threshold calls
            self._call_count += 1
            if self._call_count >= self._lazy_init_threshold:
                self.initialize()

    def _batch_compile_common_shaders(self) -> None:
        """Batch compile commonly used shaders upfront for performance optimization."""
        # Get default shader sources
        vertex_src, fragment_src = self.get_default_shader_sources()

        # Define common shader variants that are frequently used
        common_shaders = [
            ("default_component", vertex_src, fragment_src),
            ("text_shader", vertex_src, fragment_src),  # For text rendering
            ("ui_shader", vertex_src, fragment_src),    # For UI components
        ]

        # Batch compile all common shaders
        compiled = self.batch_compile_shaders(common_shaders)
        logger.debug(f"Pre-compiled {len(compiled)} common shaders for performance optimization")

    def is_available(self) -> bool:
        """Check if GPU acceleration is available."""
        with self._lock:
            self._ensure_initialized()
            return self._backend is not None

    def active_backend_kind(self) -> str | None:
        """Return a lowercase backend kind identifier or None.

        Returns:
            One of: "directx", "opengl" or None when no backend.
        """
        with self._lock:
            if self._backend is None:
                return None
            name = self._backend.__class__.__name__.lower()
            if "directx" in name:
                return "directx"
            if "opengl" in name:
                return "opengl"
            return name

    def active_renderer_kind(self) -> Any | None:
        """Alias for active_backend_kind to support legacy calls."""
        from ornata.api.exports.definitions import RendererType
        kind = self.active_backend_kind()
        if kind == "directx":
            return RendererType.DIRECTX11
        if kind == "opengl":
            return RendererType.OPENGL
        return RendererType.CPU
    
    @property
    def backend(self) -> GPUBackend | None:
        """Expose the underlying GPU backend."""
        return self._backend

    @property
    def device(self) -> Any:
        """Expose the underlying GPU device (e.g. ID3D11Device)."""
        if self._backend is None or not hasattr(self._backend, "device"):
            raise RuntimeError("GPU device not initialized or unavailable")
        return self._backend.device

    @property
    def context(self) -> Any:
        """Expose the underlying immediate context (e.g. ID3D11DeviceContext)."""
        if self._backend is None or not hasattr(self._backend, "context"):
            raise RuntimeError("GPU context not initialized or unavailable")
        return self._backend.context

    def get_capabilities(self) -> Capabilities:
        """Get the device capabilities interface."""
        return self._capabilities

    def get_limits(self) -> Limits:
        """Get the device limits interface."""
        return self._limits

    def create_shader(self, name: str, vertex_src: str, fragment_src: str) -> Shader:
        """Create and compile a shader program.

        Args:
            name: Unique name for the shader.
            vertex_src: Vertex shader source code.
            fragment_src: Fragment shader source code.

        Returns:
            Compiled Shader instance.

        Raises:
            GPUBackendNotAvailableError: If no GPU backend is available.
        """
        with self._lock:
            self._ensure_initialized()

            existing = self._shaders.get(name)
            if existing is not None:
                return existing

            if self._backend is None:
                return self._fallback.create_shader(name, vertex_src, fragment_src)

            try:
                shader = self._backend.create_shader(name, vertex_src, fragment_src)
                if shader is not None:
                    self._shaders[name] = shader
                    logger.debug(f"Successfully created GPU shader: {name}")
                    return shader
                
                # If backend returned None without raising, use fallback
                fallback_shader = self._fallback.create_shader(name, vertex_src, fragment_src)
                self._shaders[name] = fallback_shader
                return fallback_shader

            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                logger.warning(f"GPU shader creation failed for {name}: {e}, falling back to CPU\n{tb}")
                
                fallback_shader = self._fallback.create_shader(name, vertex_src, fragment_src)
                self._shaders[name] = fallback_shader
                return fallback_shader

    def dispose_shader(self, name: str) -> bool:
        """Dispose of a shader and invalidate related context cache entries.

        Args:
            name: Name of the shader to dispose.

        Returns:
            True if shader was disposed, False if not found.
        """
        with self._lock:
            shader = self._shaders.pop(name, None)
            if shader is None:
                return False

            # Invalidate context cache entries that reference this shader
            keys_to_remove: list[str] = []
            for cache_key in self._context_cache:
                if name in cache_key:
                    keys_to_remove.append(cache_key)

            for key in keys_to_remove:
                del self._context_cache[key]

            # Call backend-specific disposal if available
            if self._backend is not None and hasattr(self._backend, 'dispose_shader'):
                try:
                    self._backend.dispose_shader(shader)
                except Exception as e:
                    logger.warning(f"Error disposing shader {name} in backend: {e}")

            logger.debug(f"Disposed shader {name} and invalidated {len(keys_to_remove)} context cache entries")
            return True

    def batch_compile_shaders(self, shader_definitions: list[tuple[str, str, str]]) -> dict[str, Shader]:
        """Compile multiple shaders upfront for performance optimization.

        Args:
            shader_definitions: List of (name, vertex_src, fragment_src) tuples.

        Returns:
            Dictionary mapping shader names to compiled Shader instances.
            Failed compilations fall back to CPU shaders.
        """
        with self._lock:
            self._ensure_initialized()

            compiled_shaders: dict[str, Shader] = {}

            for name, vertex_src, fragment_src in shader_definitions:
                # Skip if already compiled
                if name in self._shaders:
                    compiled_shaders[name] = self._shaders[name]
                    continue

                if self._backend is not None:
                    try:
                        shader = self._backend.create_shader(name, vertex_src, fragment_src)
                        if shader is not None:
                            self._shaders[name] = shader
                            compiled_shaders[name] = shader
                        logger.debug(f"Successfully batch-compiled GPU shader: {name}")
                    except Exception as e:
                        logger.warning(f"GPU shader compilation failed for {name}: {e}, using CPU fallback")
                        cpu_shader = self._fallback.create_shader(name, vertex_src, fragment_src)
                        self._shaders[name] = cpu_shader
                        compiled_shaders[name] = cpu_shader
                else:
                    # No GPU backend available, use CPU fallback for all
                    cpu_shader = self._fallback.create_shader(name, vertex_src, fragment_src)
                    self._shaders[name] = cpu_shader
                    compiled_shaders[name] = cpu_shader

            logger.debug(f"Batch compiled {len(compiled_shaders)} shaders")
            return compiled_shaders

    def get_default_shader_sources(self) -> tuple[str, str]:
        """Return backend-appropriate default shader sources.

        Returns:
            Tuple of (vertex_source, fragment_source) strings.
        """
        with self._lock:
            if self._default_shader_sources is not None:
                return self._default_shader_sources

            sources: tuple[str, str] | None = None

            # Always prefer the default GLSL sources; backend compilers are responsible for translation
            # (e.g., GLSL→HLSL for DirectX) when necessary.

            if sources is None:
                from ornata.api.exports.gpu import load_fragment_program_source as _f
                from ornata.api.exports.gpu import load_vertex_program_source as _v

                sources = (_v(), _f())

            self._default_shader_sources = sources
            return sources

    def get_shader(self, name: str) -> Shader | None:
        """Return a previously created shader by name if available.

        Parameters
        ----------
        name : str
            Shader name used during creation.

        Returns
        -------
        Shader | None
            Cached shader instance or None if not found.
        """
        with self._lock:
            self._ensure_initialized()
            return self._shaders.get(name)

    def render_geometry(self, geometry: Geometry, shader: Shader) -> None:
        """Render geometry using GPU acceleration or CPU fallback with buffer reuse.

        Args:
            geometry: The geometry data to render.
            shader: The shader to use for rendering.
        """
        with self._lock:
            self._ensure_initialized()

            if self._backend is None:
                self._fallback.render_geometry(geometry, shader)
                return

            try:
                # Acquire or reuse GPU buffers for this geometry
                stride = self._geometry_stride(geometry)
                vertex_buffer = self.acquire_vertex_buffer(
                    geometry.vertices,
                    "dynamic",
                    stride_floats=stride,
                )
                index_buffer = self.acquire_index_buffer(geometry.indices, "dynamic")

                # Bind buffers and shader
                vertex_buffer.bind()
                index_buffer.bind()

                # Cache GPU context to avoid repeated initialization
                context_key = f"{shader.name}_{id(geometry)}"
                if context_key not in self._context_cache:
                    shader.bind()
                    self._context_cache[context_key] = True

                # Render using backend
                self._backend.render_geometry(geometry, shader)

                # Release buffers back to pool for reuse in next frame
                self.release_vertex_buffer(vertex_buffer)
                self.release_index_buffer(index_buffer)

                logger.debug(f"Successfully rendered geometry with {geometry.vertex_count} vertices using GPU with buffer reuse")
            except Exception as e:
                logger.warning(f"GPU rendering failed: {e}, falling back to CPU")
                self._fallback.render_geometry(geometry, shader)

    def render_instanced_geometry(self, geometry: Geometry, instance_data: list[float], instance_count: int, shader: Shader) -> None:
        """Render instanced geometry using GPU acceleration or fallback to CPU.

        Args:
            geometry: The base geometry to instance.
            instance_data: Flattened list of instance transform data (x, y, scale_x, scale_y, rotation per instance).
            instance_count: Number of instances to render.
            shader: The shader to use for rendering.
        """
        with self._lock:
            self._ensure_initialized()

            if self._backend is None:
                # Fall back to CPU rendering
                logger.debug("No GPU backend available, falling back to CPU for instanced rendering")
                self._fallback.render_instanced_geometry(geometry, instance_data, instance_count, shader)
                return

            # Check if backend supports instancing
            supports = getattr(self._backend, 'supports_instancing', None)
            if not callable(supports) or not bool(supports()):
                logger.debug("GPU backend does not support instancing, falling back to CPU")
                self._fallback.render_instanced_geometry(geometry, instance_data, instance_count, shader)
                return

            try:
                self._backend.render_instanced_geometry(geometry, instance_data, instance_count, shader)
                logger.debug(f"Successfully rendered {instance_count} instances using GPU instancing")
            except Exception as e:
                logger.warning(f"GPU instanced rendering failed: {e}, falling back to CPU")
                self._fallback.render_instanced_geometry(geometry, instance_data, instance_count, shader)

    def render_geometry_batched(self, geometries: list[tuple[Geometry, Shader, int | None, str]]) -> None:
        """Render multiple geometries using optimized batching with buffer reuse.

        Args:
            geometries: List of (geometry, shader, texture_id, blend_mode) tuples.
        """
        with self._lock:
            self._ensure_initialized()

            if self._backend is None:
                # Fall back to individual rendering
                for geometry, shader, _, _ in geometries:
                    self._fallback.render_geometry(geometry, shader)
                return

            try:
                from ornata.api.exports.gpu import RenderBatcher
                batcher = RenderBatcher(self._backend)

                # Submit all geometries for batching with small render optimization
                small_render_threshold = 10  # Geometries under this count use immediate rendering
                if len(geometries) <= small_render_threshold:
                    # For small renders, use immediate rendering with buffer reuse
                    for geometry, shader, texture_id, blend_mode in geometries:
                        # Acquire buffers from pool
                        vertex_buffer = self.acquire_vertex_buffer(
                            geometry.vertices,
                            "dynamic",
                            stride_floats=self._geometry_stride(geometry),
                        )
                        index_buffer = self.acquire_index_buffer(geometry.indices, "dynamic")

                        # Bind buffers and shader
                        vertex_buffer.bind()
                        index_buffer.bind()

                        context_key = f"{shader.name}_{texture_id}_{blend_mode}_{id(geometry)}"
                        if context_key not in self._context_cache:
                            shader.bind()
                            self._context_cache[context_key] = True
                        self._backend.render_geometry(geometry, shader)

                        # Release buffers back to pool
                        self.release_vertex_buffer(vertex_buffer)
                        self.release_index_buffer(index_buffer)
                    logger.debug(f"Rendered {len(geometries)} geometries using optimized small-batch GPU rendering with buffer reuse")
                else:
                    temp_buffers: list[tuple[VertexBuffer, IndexBuffer]] = []
                    # Submit all geometries for batching with buffer reuse
                    for geometry, shader, texture_id, blend_mode in geometries:
                        # Acquire buffers for this geometry
                        vertex_buffer = self.acquire_vertex_buffer(
                            geometry.vertices,
                            "dynamic",
                            stride_floats=self._geometry_stride(geometry),
                        )
                        index_buffer = self.acquire_index_buffer(geometry.indices, "dynamic")

                        # Create geometry with pooled buffers for batching
                        from ornata.gpu.device.geometry import Geometry
                        pooled_geometry = Geometry(
                            vertices=vertex_buffer.data,
                            indices=index_buffer.data,
                            vertex_count=geometry.vertex_count,
                            index_count=geometry.index_count
                        )

                        batcher.submit_geometry(pooled_geometry, shader, texture_id, blend_mode)

                        # Store buffer references for cleanup after batching
                        temp_buffers.append((vertex_buffer, index_buffer))

                    # Flush all batches
                    batcher.flush()

                    # Release all temporary buffers back to pool
                    for vertex_buffer, index_buffer in temp_buffers:
                        self.release_vertex_buffer(vertex_buffer)
                        self.release_index_buffer(index_buffer)

                    logger.debug(f"Successfully rendered {len(geometries)} geometries using batched GPU rendering with buffer reuse")

            except Exception as e:
                logger.warning(f"Batched GPU rendering failed: {e}, falling back to individual rendering")
                # Fall back to individual rendering
                for geometry, shader, _, _ in geometries:
                    try:
                        context_key = f"{shader.name}_{id(geometry)}"
                        if context_key not in self._context_cache:
                            shader.bind()
                            self._context_cache[context_key] = True
                        self._backend.render_geometry(geometry, shader)
                    except Exception as inner_e:
                        logger.warning(f"Individual GPU rendering failed: {inner_e}, using CPU fallback")
                        self._fallback.render_geometry(geometry, shader)

    def invalidate_geometry_cache(self) -> None:
        """Invalidate all cached geometries to force regeneration.

        This method clears the geometry cache, ensuring that subsequent geometry
        conversions will recalculate geometries from components.
        """
        with self._lock:
            self._geometry_cache.clear()
            logger.debug("Geometry cache invalidated")

    def get_geometry_cache_stats(self) -> dict[str, int | float]:
        """Get statistics about the geometry cache performance.

        Returns:
            Dictionary containing cache statistics including size, hits, misses, and hit rate.
        """
        with self._lock:
            return self._geometry_cache.stats()

    def _geometry_stride(self, geometry: Geometry) -> int:
        """Compute the floats-per-vertex stride for a geometry.

        Args:
            geometry: Geometry whose vertex data is being uploaded.

        Returns:
            Number of floats per vertex, defaulting to 5 when it cannot be derived.
        """
        vertex_count = geometry.vertex_count
        if vertex_count > 0:
            total_values = len(geometry.vertices)
            if total_values >= vertex_count:
                stride = total_values // vertex_count
                if stride > 0:
                    return stride
        return 5

    def get_pool_stats(self) -> dict[str, int]:
        """Get statistics about memory pool usage and buffer management.

        Returns:
            Dictionary containing pool statistics including creation/reuse counts and leak detection.
        """
        with self._lock:
            # Clean up dead weak references for leak detection
            self._buffer_weak_refs = [ref for ref in self._buffer_weak_refs if ref() is not None]
            active_refs = len([ref for ref in self._buffer_weak_refs if ref() is not None])
            self._pool_stats["leaks_detected"] = len(self._active_buffers) - active_refs

            # Log warning if leaks detected
            if self._pool_stats["leaks_detected"] > 0:
                logger.warning(f"Memory leak detected: {self._pool_stats['leaks_detected']} buffers not properly released")

            return self._pool_stats.copy()

    def check_for_leaks(self) -> dict[str, int | dict[str, dict[str, int]]]:
        """Perform comprehensive memory leak detection and return detailed report.

        Returns:
            Dictionary with leak analysis including buffer counts and recommendations.
        """
        with self._lock:
            # Clean up dead weak references
            self._buffer_weak_refs = [ref for ref in self._buffer_weak_refs if ref() is not None]

            # Count active references
            active_refs = len([ref for ref in self._buffer_weak_refs if ref() is not None])

            # Calculate leaks
            leaks = len(self._active_buffers) - active_refs

            # Get pool sizes
            vertex_pool_size = len(self._vertex_buffer_pool.pool)
            index_pool_size = len(self._index_buffer_pool.pool)

            # Backend-specific leak analysis
            backend_leaks: dict[str, dict[str, int]] = {}
            for backend_name, vertex_buffers in self._backend_vertex_buffers.items():
                backend_active = len(vertex_buffers)
                backend_index_buffers = self._backend_index_buffers.get(backend_name, set())
                backend_total = backend_active + len(backend_index_buffers)
                backend_leaks[backend_name] = {
                    "vertex_buffers": backend_active,
                    "index_buffers": len(backend_index_buffers),
                    "total_buffers": backend_total
                }

            leak_report: dict[str, int | dict[str, dict[str, int]]] = {
                "active_buffers": len(self._active_buffers),
                "tracked_references": active_refs,
                "leaks_detected": leaks,
                "vertex_pool_size": vertex_pool_size,
                "index_pool_size": index_pool_size,
                "total_pools_size": vertex_pool_size + index_pool_size,
                "backend_buffer_distribution": backend_leaks
            }

            # Log detailed leak information
            if leaks > 0:
                logger.error(f"CRITICAL: Memory leaks detected! {leaks} buffers not released. "
                            f"Active: {len(self._active_buffers)}, Tracked: {active_refs}")
                logger.error(f"Pool status - Vertex: {vertex_pool_size}, Index: {index_pool_size}")
                for backend_name, counts in backend_leaks.items():
                    logger.error(f"Backend {backend_name}: {counts['total_buffers']} buffers "
                                f"({counts['vertex_buffers']} vertex, {counts['index_buffers']} index)")

            return leak_report

    def get_pool_sizes(self) -> dict[str, int | float]:
        """Get current sizes of all memory pools for monitoring.

        Returns:
            Dictionary with current pool sizes and utilization metrics.
        """
        with self._lock:
            vertex_pool_size = len(self._vertex_buffer_pool.pool)
            index_pool_size = len(self._index_buffer_pool.pool)
            geometry_pool_size = len(self._geometry_pool.pool)
            vertex_data_pool_size = len(self._vertex_pool.pool)
            index_data_pool_size = len(self._index_pool.pool)

            vertex_pool_max = self._vertex_buffer_pool.max_size or 0
            index_pool_max = self._index_buffer_pool.max_size or 0
            vertex_pool_utilization = (vertex_pool_size / vertex_pool_max) * 100 if vertex_pool_max > 0 else 0
            index_pool_utilization = (index_pool_size / index_pool_max) * 100 if index_pool_max > 0 else 0

            return {
                "vertex_buffer_pool_size": vertex_pool_size,
                "index_buffer_pool_size": index_pool_size,
                "geometry_pool_size": geometry_pool_size,
                "vertex_data_pool_size": vertex_data_pool_size,
                "index_data_pool_size": index_data_pool_size,
                "vertex_buffer_pool_utilization_percent": vertex_pool_utilization,
                "index_buffer_pool_utilization_percent": index_pool_utilization,
                "total_buffer_pools_size": vertex_pool_size + index_pool_size,
                "total_data_pools_size": vertex_data_pool_size + index_data_pool_size,
            }

    def acquire_vertex_buffer(self, data: list[float], usage: str = "dynamic", *, stride_floats: int | None = None) -> VertexBuffer:
        """Acquire a vertex buffer from the pool or create a new one.

        Args:
            data: Vertex data for the buffer.
            usage: Buffer usage pattern.
            stride_floats: Optional floats-per-vertex stride hint.

        Returns:
            VertexBuffer instance from pool or newly created.
        """
        with self._lock:
            backend_key = self.active_backend_kind() or "cpu"
            stride_value = stride_floats if stride_floats and stride_floats > 0 else None
            from ornata.gpu.buffers import VertexBuffer

            # Try to reuse an existing buffer
            if self._vertex_buffer_pool.pool:
                buffer = self._vertex_buffer_pool.acquire()
                if stride_value and buffer.stride_floats != stride_value:
                    buffer.cleanup()
                    buffer = VertexBuffer(data, usage, stride_floats=stride_value, gpu_manager=self)
                    self._pool_stats["vertex_buffers_created"] += 1
                else:
                    if hasattr(buffer, "update_data"):
                        buffer.update_data(data)
                    if stride_value is not None:
                        buffer.set_stride(stride_value, data_length=len(data))
                self._pool_stats["vertex_buffers_reused"] += 1
                # Track for leak detection
                self._active_buffers.add(buffer)
                self._buffer_weak_refs.append(weakref.ref(buffer, lambda ref: self._active_buffers.discard(ref())))
                # Track backend-specific buffer
                if backend_key not in self._backend_vertex_buffers:
                    self._backend_vertex_buffers[backend_key] = set()
                self._backend_vertex_buffers[backend_key].add(buffer)
                return buffer

            # Create new buffer
            buffer = VertexBuffer(data, usage, stride_floats=stride_value or 5, gpu_manager=self)
            self._pool_stats["vertex_buffers_created"] += 1
            # Track for leak detection
            self._active_buffers.add(buffer)
            self._buffer_weak_refs.append(weakref.ref(buffer, lambda ref: self._active_buffers.discard(ref())))
            # Track backend-specific buffer
            if backend_key not in self._backend_vertex_buffers:
                self._backend_vertex_buffers[backend_key] = set()
            self._backend_vertex_buffers[backend_key].add(buffer)
            return buffer

    def acquire_index_buffer(self, indices: list[int], usage: str = "dynamic") -> IndexBuffer:
        """Acquire an index buffer from the pool or create a new one.

        Args:
            indices: Index data for the buffer.
            usage: Buffer usage pattern.

        Returns:
            IndexBuffer instance from pool or newly created.
        """
        with self._lock:
            backend_key = self.active_backend_kind() or "cpu"

            # Try to reuse an existing buffer
            if self._index_buffer_pool.pool:
                buffer = self._index_buffer_pool.acquire()
                if hasattr(buffer, 'update_data'):
                    buffer.update_data(indices)
                self._pool_stats["index_buffers_reused"] += 1
                # Track for leak detection
                self._active_buffers.add(buffer)
                self._buffer_weak_refs.append(weakref.ref(buffer, lambda ref: self._active_buffers.discard(ref())))
                # Track backend-specific buffer
                if backend_key not in self._backend_index_buffers:
                    self._backend_index_buffers[backend_key] = set()
                self._backend_index_buffers[backend_key].add(buffer)
                return buffer

            # Create new buffer
            from ornata.gpu.buffers import IndexBuffer
            buffer = IndexBuffer(indices, usage, gpu_manager=self)
            self._pool_stats["index_buffers_created"] += 1
            # Track for leak detection
            self._active_buffers.add(buffer)
            self._buffer_weak_refs.append(weakref.ref(buffer, lambda ref: self._active_buffers.discard(ref())))
            # Track backend-specific buffer
            if backend_key not in self._backend_index_buffers:
                self._backend_index_buffers[backend_key] = set()
            self._backend_index_buffers[backend_key].add(buffer)
            return buffer

    def release_vertex_buffer(self, buffer: VertexBuffer) -> None:
        """Release a vertex buffer back to the pool for reuse.

        Args:
            buffer: The vertex buffer to release.
        """
        with self._lock:
            if buffer in self._active_buffers:
                self._active_buffers.discard(buffer)

            # Remove from backend-specific tracking
            for backend_buffers in self._backend_vertex_buffers.values():
                backend_buffers.discard(buffer)

            self._vertex_buffer_pool.release(buffer)

    def release_index_buffer(self, buffer: IndexBuffer) -> None:
        """Release an index buffer back to the pool for reuse.

        Args:
            buffer: The index buffer to release.
        """
        with self._lock:
            if buffer in self._active_buffers:
                self._active_buffers.discard(buffer)

            # Remove from backend-specific tracking
            for backend_buffers in self._backend_index_buffers.values():
                backend_buffers.discard(buffer)

            self._index_buffer_pool.release(buffer)

    def cleanup(self) -> None:
        """Clean up device resources and shutdown."""
        with self._lock:
            # Clear caches
            self._geometry_cache.clear()
            self._context_cache.clear()
            self._shaders.clear()

            # Clear pools
            self._vertex_buffer_pool.pool.clear()
            self._index_buffer_pool.pool.clear()
            self._geometry_pool.pool.clear()
            self._vertex_pool.pool.clear()
            self._index_pool.pool.clear()

            # Clear backend-specific buffer tracking
            self._backend_vertex_buffers.clear()
            self._backend_index_buffers.clear()

            # Clear leak detection
            self._active_buffers.clear()
            self._buffer_weak_refs.clear()

            # Shutdown backend if available
            if self._backend is not None and hasattr(self._backend, 'shutdown'):
                try:
                    self._backend.shutdown()
                except Exception as e:
                    logger.warning(f"Error shutting down backend: {e}")

            self._backend = None
            self._initialized = False
            logger.debug("Device manager cleaned up")


def render_with_gpu_acceleration(component: Component, target_surface: Any) -> None:
    """Render a component using GPU acceleration when available.

    Args:
        component: Component to render.
        target_surface: Backend-specific surface or context receiving rendering output.
    """
    manager = get_device_manager()

    if manager.is_available():
        # Convert component to GPU geometry
        from ornata.gpu.device.geometry import component_to_gpu_geometry
        geometry = component_to_gpu_geometry(component)

        # Use appropriate shader per backend
        vs_src, fs_src = manager.get_default_shader_sources()
        shader = manager.create_shader("default_component", vs_src, fs_src)

        # Render with GPU acceleration
        manager.render_geometry(geometry, shader)
        logger.debug("Rendered component with GPU acceleration")
    else:
        # Fall back to CPU rendering
        from ornata.gpu.device.geometry import cpu_render
        cpu_render(component, target_surface)
        logger.debug("Rendered component with CPU fallback")


# Global device manager singleton
_device_manager_singleton: DeviceManager | None = None
_device_manager_lock = threading.Lock()


def get_device_manager() -> DeviceManager:
    """Return the process-wide device manager singleton.

    Returns:
        DeviceManager: Shared manager instance reused across render calls.
    """
    global _device_manager_singleton
    with _device_manager_lock:
        if _device_manager_singleton is None:
            _device_manager_singleton = DeviceManager()
        return _device_manager_singleton