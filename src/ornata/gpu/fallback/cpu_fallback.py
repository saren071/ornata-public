"""CPU fallback implementation providing deterministic software rendering."""
from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger
from ornata.gpu.misc import GPUBackend

if TYPE_CHECKING:
    from collections.abc import Callable

    from ornata.api.exports.definitions import Geometry
    from ornata.gpu.fallback.sw_pipeline import SoftwareShaderProgram
    from ornata.gpu.fallback.sw_textures import SwTexture2D
    from ornata.gpu.misc import Shader


logger = get_logger(__name__)


class CPUFallback(GPUBackend):
    """CPU-based fallback implementation when GPU acceleration is unavailable.

    The fallback renders geometry using a software rasterizer and honours
    pipeline configuration including depth testing and blending. Shaders are
    emulated via :class:`SoftwareShaderProgram` instances that support a small
    and well-defined uniform interface for UI rendering.

    Provides comprehensive support for:
    - Indexed and non-indexed geometry rendering
    - CPU-based instancing for repeated UI elements
    - Software texture management with thread safety
    - Frame callbacks for real-time rendering feedback
    - Performance-optimized rendering pipeline
    """

    def __init__(self, width: int = 800, height: int = 600) -> None:
        from ornata.gpu.fallback.blitter import CPUBlitter
        from ornata.gpu.fallback.instancing import CPUInstancer
        from ornata.gpu.fallback.rasterizer import SoftwareRasterizer
        from ornata.gpu.fallback.sw_pipeline import PipelineConfig, SoftwarePipeline
        self._shaders: dict[str, Shader] = {}
        self._pipeline = SoftwarePipeline(PipelineConfig(viewport_width=width, viewport_height=height))
        self._rasterizer = SoftwareRasterizer(width, height)
        self._instancer = CPUInstancer()
        self._blitter = CPUBlitter()
        self._textures: dict[str, SwTexture2D] = {}
        self._width = width
        self._height = height
        self._lock = threading.RLock()
        self._framebuffer_snapshot: list[list[tuple[int, int, int, int]]] | None = None
        self._on_frame_rendered: Callable[[list[list[tuple[int, int, int, int]]]], None] | None = None
        self._performance_stats: dict[str, int | float] = {
            "frames_rendered": 0,
            "vertices_processed": 0,
            "triangles_rasterized": 0,
            "texture_bindings": 0,
            "uniform_updates": 0,
            "shaders_created": 0,
            "last_render_time_ms": 0.0,
            "total_render_time_ms": 0.0,
        }
        self._shutdown_event = threading.Event()

    def is_available(self) -> bool:
        """CPU fallback is always available as a last resort."""
        return True

    def create_shader(self, name: str, vertex_src: str, fragment_src: str) -> Shader:
        """Create a shader with CPU emulation and required uniform initialization.

        Args:
            name: Unique name for the shader.
            vertex_src: Vertex shader source code (GLSL).
            fragment_src: Fragment shader source code (GLSL).

        Returns:
            Shader instance with CPU emulation and required uniforms.

        Raises:
            ShaderCompilationError: If shader creation fails.
        """

        with self._lock:
            try:
                from ornata.gpu.fallback.sw_pipeline import SoftwareShaderProgram
                from ornata.gpu.misc import Shader
                shader = Shader(name, vertex_src, fragment_src)
                program = SoftwareShaderProgram(vertex_src, fragment_src)
                
                # Initialize required uniforms as per GPU_TODO.md Section 2
                default_color = [1.0, 1.0, 1.0, 1.0]
                default_opacity = 1.0
                default_resolution = [float(self._width), float(self._height)]
                default_texture_slot = 0
                
                program.set_uniform("u_color", default_color)
                program.set_uniform("u_opacity", default_opacity)
                program.set_uniform("u_resolution", default_resolution)
                program.set_uniform("u_texture_slot", default_texture_slot)
                
                shader.uniform_values["u_color"] = default_color
                shader.uniform_values["u_opacity"] = default_opacity
                shader.uniform_values["u_resolution"] = default_resolution
                shader.uniform_values["u_texture_slot"] = default_texture_slot
                
                shader.program = program
                shader.backend = self
                shader.compiled = True
                self._shaders[name] = shader
                self._performance_stats["shaders_created"] += 1
                logger.debug(f"Created CPU fallback shader: {name} with required uniforms")
                return shader
            except Exception as e:
                logger.error(f"CPU shader emulation failed for {name}: {e}")
                from ornata.api.exports.definitions import GPUShaderCompilationError
                raise GPUShaderCompilationError(f"CPU shader emulation failed: {e}") from e

    def clear(self, color: Any) -> None:
        """Simulate clearing the CPU fallback surface."""
        try:
            # You can extend this later to actually draw a background buffer.
            from ornata.api.exports.utils import get_logger
            logger = get_logger(__name__)
            logger.debug(f"CPUFallback.clear called with color={color}")
        except Exception as e:
            from ornata.api.exports.utils import get_logger
            logger = get_logger(__name__)
            logger.error(f"CPUFallback.clear failed: {e}")

    def present(self) -> None:
        """Simulate presenting the CPU fallback frame."""
        try:
            from ornata.api.exports.utils import get_logger
            logger = get_logger(__name__)
            logger.debug("CPUFallback.present called (no-op)")
        except Exception as e:
            from ornata.api.exports.utils import get_logger
            logger = get_logger(__name__)
            logger.error(f"CPUFallback.present failed: {e}")

    def render_geometry(self, geometry: Geometry, shader: Shader) -> None:
        """Render geometry using CPU-based software rendering with performance optimization.

        Args:
            geometry: The geometry data to render.
            shader: The shader to use for rendering.
            
        Raises:
            ValueError: If geometry or shader is invalid.
        """
        import time
        
        if self._shutdown_event.is_set():
            raise RuntimeError("CPU fallback backend has been shut down")
            
        with self._lock:
            try:
                # Validate inputs
                if geometry.vertex_count <= 0 or geometry.index_count < 0:
                    raise ValueError(f"Invalid geometry: vertices={geometry.vertex_count}, indices={geometry.index_count}")
                    
                program = self._extract_program(shader)
                if program is not None:
                    self._pipeline.set_vertex_shader(program)
                    self._pipeline.set_fragment_shader(program)
                if program is not None and not self._pipeline.is_bound():
                    self._pipeline.bind()

                # Performance tracking
                start_time = time.time_ns()
                
                self._rasterizer.render(geometry, shader, self._pipeline)
                self._framebuffer_snapshot = self._rasterizer.get_framebuffer()
                
                # Update performance statistics
                end_time = time.time_ns()
                render_time_ms = (end_time - start_time) / 1_000_000.0
                
                self._performance_stats.update({
                    "frames_rendered": self._performance_stats["frames_rendered"] + 1,
                    "vertices_processed": self._performance_stats["vertices_processed"] + geometry.vertex_count,
                    "triangles_rasterized": self._performance_stats["triangles_rasterized"] + max(0, geometry.index_count // 3),
                    "last_render_time_ms": render_time_ms,
                    "total_render_time_ms": self._performance_stats.get("total_render_time_ms", 0.0) + render_time_ms,
                })

                # Performance-optimized frame callback (avoid copy if no callback)
                if self._on_frame_rendered is not None:
                    self._on_frame_rendered(self._framebuffer_snapshot)

                logger.debug(
                    "CPU fallback rendered %s vertices, %s triangles in %.2fms",
                    geometry.vertex_count,
                    max(0, geometry.index_count // 3),
                    render_time_ms
                )
            except Exception as e:
                logger.error(f"CPU rendering failed: {e}")
                raise

    def render_instanced_geometry(self, geometry: Geometry, instance_data: list[float], instance_count: int, shader: Shader) -> None:
        """Render instanced geometry using CPU instancing support."""

        with self._lock:
            expanded_geometry = self._instancer.process_instances(geometry, instance_data, instance_count)
            logger.debug(
                "CPU fallback expanded %s instances into %s vertices",
                instance_count,
                expanded_geometry.vertex_count,
            )
            self.render_geometry(expanded_geometry, shader)

    def begin_frame(self, clear_color: tuple[int, int, int, int] | None = None) -> None:
        """Prepare the framebuffer for a new frame."""
        with self._lock:
            if clear_color is not None:
                self._rasterizer.set_clear_color(clear_color)
            self._rasterizer.clear()
            self._framebuffer_snapshot = None

    def get_framebuffer(self) -> list[list[tuple[int, int, int, int]]]:
        """Return a copy of the latest rendered framebuffer."""
        with self._lock:
            if self._framebuffer_snapshot is None:
                return self._rasterizer.get_framebuffer()
            return [row[:] for row in self._framebuffer_snapshot]

    def resize_viewport(self, width: int, height: int) -> None:
        """Resize the software viewport and framebuffer."""
        with self._lock:
            self._pipeline.config.viewport_width = width
            self._pipeline.config.viewport_height = height
            self._rasterizer.resize(width, height)

    def set_uniform(self, shader: Shader, name: str, value: float | int | list[float] | list[int]) -> None:
        """Update a uniform on the emulated shader program with validation."""
        if self._shutdown_event.is_set():
            logger.warning("Cannot set uniform on shut down backend")
            return
            
        program = self._extract_program(shader)
        if program is None:
            logger.warning(f"No software program found for shader {shader.name}")
            return
            
        try:
            # Validate uniform name and value
            if not name:
                raise ValueError("Uniform name must be non-empty string")
                
            program.set_uniform(name, value)
            self._performance_stats["uniform_updates"] += 1
            
            # Update shader's uniform values cache
            shader.uniform_values[name] = value
            
            logger.debug(f"Set uniform {name} on shader {shader.name}")
        except Exception as e:
            logger.error(f"Failed to set uniform {name} on shader {shader.name}: {e}")
            raise

    def bind_texture(self, shader: Shader, slot: int, texture: SwTexture2D) -> None:
        """Bind a software texture to a shader with performance optimization.
        
        Args:
            shader: The shader to bind texture to.
            slot: Texture slot index (0-15 typically).
            texture: Software texture to bind.
            
        Raises:
            ValueError: If slot is invalid or texture is None.
        """
        if self._shutdown_event.is_set():
            logger.warning("Cannot bind texture on shut down backend")
            return
            
        if slot < 0 or slot > 15:  # Standard texture slot limit
            raise ValueError(f"Texture slot {slot} out of range (0-15)")
            
        try:
            program = self._extract_program(shader)
            if program is None:
                logger.warning(f"No software program found for shader {shader.name}")
                return
                
            program.bind_texture(slot, texture)
            self._performance_stats["texture_bindings"] += 1
            
            logger.debug(f"Bound texture to slot {slot} on shader {shader.name}")
        except Exception as e:
            logger.error(f"Failed to bind texture to slot {slot} on shader {shader.name}: {e}")
            raise

    def create_texture(self, name: str, width: int, height: int, data: list[int] | None = None) -> SwTexture2D:
        """Create and register a software texture."""
        from ornata.gpu.fallback.sw_textures import SwTexture2D
        texture = SwTexture2D(width, height, data)
        self._textures[name] = texture
        return texture

    def get_texture(self, name: str) -> SwTexture2D | None:
        """Retrieve a registered texture by name."""
        return self._textures.get(name)

    def on_frame_rendered(self, callback: Callable[[list[list[tuple[int, int, int, int]]]], None]) -> None:
        """Register a callback executed whenever a frame is rendered."""
        self._on_frame_rendered = callback

    # -------------------------- Stage Compilation ---------------------------
    def compile_vertex_shader(self, source: str) -> Any:
        """Vertex stage is not compiled in CPU fallback."""
        from ornata.api.exports.definitions import GPUBackendNotAvailableError
        raise GPUBackendNotAvailableError("CPU fallback has no real shader compilation")

    def compile_fragment_shader(self, source: str) -> Any:
        """Fragment stage is not compiled in CPU fallback."""
        from ornata.api.exports.definitions import GPUBackendNotAvailableError
        raise GPUBackendNotAvailableError("CPU fallback has no real shader compilation")

    def compile_geometry_shader(self, source: str) -> Any:
        """Geometry stage not supported in CPU fallback."""
        from ornata.api.exports.definitions import GPUBackendNotAvailableError
        raise GPUBackendNotAvailableError("CPU fallback has no geometry stage")

    def compile_mesh_shader(self, source: str) -> Any:
        """Mesh stage not supported in CPU fallback."""
        from ornata.api.exports.definitions import GPUBackendNotAvailableError
        raise GPUBackendNotAvailableError("CPU fallback has no mesh stage")

    def compile_task_shader(self, source: str) -> Any:
        """Task stage not supported in CPU fallback."""
        from ornata.api.exports.definitions import GPUBackendNotAvailableError
        raise GPUBackendNotAvailableError("CPU fallback has no task stage")

    def compile_tess_control_shader(self, source: str) -> Any:
        """Tessellation control not supported in CPU fallback."""
        from ornata.api.exports.definitions import GPUBackendNotAvailableError
        raise GPUBackendNotAvailableError("CPU fallback has no tessellation control stage")

    def compile_tess_eval_shader(self, source: str) -> Any:
        """Tessellation evaluation not supported in CPU fallback."""
        from ornata.api.exports.definitions import GPUBackendNotAvailableError
        raise GPUBackendNotAvailableError("CPU fallback has no tessellation evaluation stage")

    def compile_compute_shader(self, source: str) -> Any:
        """Compute stage not supported in CPU fallback."""
        from ornata.api.exports.definitions import GPUBackendNotAvailableError
        raise GPUBackendNotAvailableError("CPU fallback has no compute stage")

    def compile_raygen_shader(self, source: str) -> Any:
        """Ray tracing not supported in CPU fallback."""
        from ornata.api.exports.definitions import GPUBackendNotAvailableError
        raise GPUBackendNotAvailableError("CPU fallback has no ray tracing stages")

    def compile_miss_shader(self, source: str) -> Any:
        """Ray tracing not supported in CPU fallback."""
        from ornata.api.exports.definitions import GPUBackendNotAvailableError
        raise GPUBackendNotAvailableError("CPU fallback has no ray tracing stages")

    def compile_closesthit_shader(self, source: str) -> Any:
        """Ray tracing not supported in CPU fallback."""
        from ornata.api.exports.definitions import GPUBackendNotAvailableError
        raise GPUBackendNotAvailableError("CPU fallback has no ray tracing stages")

    def upload_to_gpu(self, buffer: bytearray, size: int) -> None:
        """CPU fallback cannot perform GPU uploads."""
        from ornata.api.exports.definitions import GPUBackendNotAvailableError

        raise GPUBackendNotAvailableError("CPU fallback has no GPU upload path")

    def download_from_gpu(self, buffer: bytearray, size: int) -> int:
        """CPU fallback cannot perform GPU downloads."""
        from ornata.api.exports.definitions import GPUBackendNotAvailableError

        raise GPUBackendNotAvailableError("CPU fallback has no GPU download path")

    # -------------------------- Pipeline Builders ---------------------------
    def create_tessellation_pipeline(self, name: str, vs_src: str, tcs_src: str, tes_src: str, fs_src: str) -> Shader:
        """Tessellation pipeline not supported by CPU fallback."""
        from ornata.api.exports.definitions import GPUBackendNotAvailableError
        raise GPUBackendNotAvailableError("CPU fallback tessellation pipeline not supported")

    def create_mesh_pipeline(self, name: str, task_src: str | None, mesh_src: str, fs_src: str) -> Shader:
        """Mesh pipeline not supported by CPU fallback."""
        from ornata.api.exports.definitions import GPUBackendNotAvailableError
        raise GPUBackendNotAvailableError("CPU fallback mesh pipeline not supported")

    def create_compute(self, name: str, cs_src: str) -> Shader:
        """Compute program not supported by CPU fallback."""
        from ornata.api.exports.definitions import GPUBackendNotAvailableError
        raise GPUBackendNotAvailableError("CPU fallback compute not supported")

    def create_raytracing_pipeline(self, name: str, rgen_src: str, rmiss_src: str, rchit_src: str, anyhit_src: str | None) -> Shader:
        """Ray tracing pipeline not supported by CPU fallback."""
        from ornata.api.exports.definitions import GPUBackendNotAvailableError
        raise GPUBackendNotAvailableError("CPU fallback ray tracing pipeline not supported")

    def get_performance_stats(self) -> dict[str, Any]:
        """Get performance statistics for the CPU fallback backend.
        
        Returns:
            Dictionary containing performance metrics including render times,
            vertex processing counts, and resource usage statistics.
        """
        with self._lock:
            base_stats = self._performance_stats
            stats: dict[str, Any] = dict(base_stats)
            
            # Calculate derived metrics
            if stats["frames_rendered"] > 0:
                stats["avg_render_time_ms"] = stats.get("total_render_time_ms", 0.0) / stats["frames_rendered"]
                stats["vertices_per_frame"] = stats["vertices_processed"] / stats["frames_rendered"]
                stats["triangles_per_frame"] = stats["triangles_rasterized"] / stats["frames_rendered"]
            else:
                stats["avg_render_time_ms"] = 0.0
                stats["vertices_per_frame"] = 0.0
                stats["triangles_per_frame"] = 0.0
                
            # Add backend-specific info
            stats.update({
                "backend_type": "CPU_FALLBACK",
                "viewport_width": self._width,
                "viewport_height": self._height,
                "shaders_loaded": len(self._shaders),
                "textures_cached": len(self._textures),
                "is_shutdown": self._shutdown_event.is_set(),
            })
            
            return stats

    def clear_performance_stats(self) -> None:
        """Clear all performance statistics counters."""
        with self._lock:
            self._performance_stats.update({
                "frames_rendered": 0,
                "vertices_processed": 0,
                "triangles_rasterized": 0,
                "texture_bindings": 0,
                "uniform_updates": 0,
                "shaders_created": 0,
                "last_render_time_ms": 0.0,
                "total_render_time_ms": 0.0,
            })
            logger.debug("Cleared CPU fallback performance statistics")

    def shutdown(self) -> None:
        """Perform graceful shutdown of the CPU fallback backend."""
        logger.info("Shutting down CPU fallback backend")
        
        with self._lock:
            self._shutdown_event.set()
            
            # Clean up resources
            self._shaders.clear()
            self._textures.clear()
            self._framebuffer_snapshot = None
            self._on_frame_rendered = None
            
            # Reset pipeline state
            self._pipeline.unbind()
            
        logger.info("CPU fallback backend shutdown complete")

    def is_shutdown(self) -> bool:
        """Check if the backend has been shut down.
        
        Returns:
            True if the backend has been shut down, False otherwise.
        """
        return self._shutdown_event.is_set()

    @staticmethod
    def _extract_program(shader: Shader) -> SoftwareShaderProgram | None:
        """Extract software shader program from shader object.
        
        Args:
            shader: The shader to extract program from.
            
        Returns:
            SoftwareShaderProgram instance if found, None otherwise.
        """
        from ornata.gpu.fallback.sw_pipeline import SoftwareShaderProgram
        program_ref: SoftwareShaderProgram | None = shader.program
        if isinstance(program_ref, SoftwareShaderProgram):
            return program_ref
        return None
