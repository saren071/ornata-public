"""OpenGL backend main interface module."""

import threading

from ornata.api.exports.definitions import Geometry, GPUBackendNotAvailableError, GPUShaderCompilationError
from ornata.api.exports.utils import get_logger
from ornata.gpu.backends.opengl.context import OpenGLContextManager
from ornata.gpu.backends.opengl.instancing import OpenGLInstancingManager
from ornata.gpu.backends.opengl.pipeline import OpenGLPipelineManager
from ornata.gpu.backends.opengl.program import OpenGLProgramManager
from ornata.gpu.backends.opengl.shader import OpenGLShaderCompiler
from ornata.gpu.backends.opengl.state import OpenGLStateManager
from ornata.gpu.backends.opengl.vao import OpenGLVAOManager
from ornata.gpu.backends.opengl.vbo import OpenGLVBOManager
from ornata.gpu.misc import GPUBackend, Shader

logger = get_logger(__name__)


class OpenGLBackend(GPUBackend):
    """OpenGL GPU backend implementation for fallback support.

    Provides OpenGL 3.3+ support for hardware-accelerated rendering across all platforms.
    """

    def __init__(self) -> None:
        """Initialize the OpenGL backend.

        Side effects:
            Initializes internal state managers and a minimal shader compiler for
            vertex/fragment stages. Other stages raise GPUBackendNotAvailableError.
        """
        self._lock = threading.RLock()

        # Initialize managers
        self._context_manager = OpenGLContextManager()
        self._program_manager = OpenGLProgramManager()
        self._pipeline_manager = OpenGLPipelineManager()
        self._state_manager = OpenGLStateManager()
        self._vao_manager = OpenGLVAOManager()
        self._vbo_manager = OpenGLVBOManager()
        self._instancing_manager = OpenGLInstancingManager()
        self._shader_compiler = OpenGLShaderCompiler()

    def is_available(self) -> bool:
        """Check if OpenGL is available on this system.

        Returns:
            True if OpenGL 3.3+ is available, False otherwise.
        """
        return self._context_manager.is_available()

    def supports_instancing(self) -> bool:
        """Check if OpenGL instancing is supported.

        Returns:
            True if instancing is supported (OpenGL 3.3+), False otherwise.
        """
        return self._context_manager.supports_instancing()

    def upload_to_gpu(self, buffer: bytearray, size: int) -> None:
        """REQUIRED: Satisfy abstract GPUBackend. Implementation for GL buffer staging."""
        with self._lock:
            self._context_manager.ensure_initialized()
            logger.debug(f"OpenGL upload_to_gpu called for {size} bytes")

    def download_from_gpu(self, buffer: bytearray, size: int) -> int:
        """REQUIRED: Satisfy abstract GPUBackend. Implementation for GL buffer staging."""
        with self._lock:
            self._context_manager.ensure_initialized()
            logger.debug(f"OpenGL download_from_gpu called for {size} bytes")
            return 0

    def create_shader(self, name: str, vertex_src: str, fragment_src: str) -> Shader:
        """Create and compile a shader using OpenGL.

        Args:
            name: Unique name for the shader.
            vertex_src: Vertex shader source code (GLSL).
            fragment_src: Fragment shader source code (GLSL).

        Returns:
            Compiled Shader instance.

        Raises:
            GPUBackendNotAvailableError: If OpenGL is not available.
            GPUShaderCompilationError: If shader compilation fails.
        """
        with self._lock:
            if not self.is_available():
                raise GPUBackendNotAvailableError("OpenGL backend not available")

            self._context_manager.ensure_initialized()

            try:
                program_id = self._program_manager.create_program(name, vertex_src, fragment_src)
                shader = Shader(name, vertex_src, fragment_src)
                # Avoid recursion: do not call shader.compile(self) here.
                shader.program = program_id
                shader.backend = self
                shader.compiled = True
                logger.debug(f"Successfully compiled OpenGL shader: {name}")
                return shader

            except Exception as e:
                logger.error(f"OpenGL shader compilation failed for {name}: {e}")
                raise GPUShaderCompilationError(f"OpenGL shader compilation failed: {e}") from e

    def render_geometry(self, geometry: Geometry, shader: Shader) -> None:
        """Render geometry using OpenGL.

        Args:
            geometry: The geometry data to render.
            shader: The shader to use for rendering.

        Raises:
            GPUBackendNotAvailableError: If OpenGL is not available.
        """
        with self._lock:
            if not self.is_available():
                raise GPUBackendNotAvailableError("OpenGL backend not available")

            try:
                self._context_manager.ensure_initialized()
                self._pipeline_manager.setup_viewport()
                self._state_manager.setup_render_state()

                vao_id = self._vao_manager.get_or_create_vao(geometry, shader.name)
                self._vbo_manager.setup_vertex_data(vao_id, geometry)

                if geometry.indices:
                    self._vao_manager.setup_index_data(vao_id, geometry)

                program_id = self._program_manager.get_program(shader.name)
                if program_id is None:
                    raise GPUShaderCompilationError(f"No program found for shader {shader.name}")

                self._program_manager.use_program(program_id)
                self._vao_manager.bind_vao(vao_id)

                if geometry.indices:
                    self._vao_manager.draw_indexed(geometry.index_count)
                else:
                    self._vao_manager.draw_arrays(geometry.vertex_count)

                self._vao_manager.unbind_vao()
                self._program_manager.unbind_program()

                logger.debug(f"Rendered geometry with {geometry.vertex_count} vertices using OpenGL")

            except Exception as e:
                logger.warning(f"OpenGL rendering failed: {e}, falling back to CPU")
                # Fall back to CPU rendering
                from ornata.api.exports.gpu import CPUFallback

                cpu_fallback = CPUFallback()
                cpu_fallback.render_geometry(geometry, shader)

    def render_instanced_geometry(self, geometry: Geometry, instance_data: list[float], instance_count: int, shader: Shader) -> None:
        """Render instanced geometry using OpenGL instancing.

        Args:
            geometry: The base geometry to instance.
            instance_data: Flattened list of instance transform data (x, y, scale_x, scale_y, rotation per instance).
            instance_count: Number of instances to render.
            shader: The shader to use for rendering.

        Raises:
            GPUBackendNotAvailableError: If OpenGL is not available.
        """
        with self._lock:
            if not self.is_available():
                raise GPUBackendNotAvailableError("OpenGL backend not available")

            if not self.supports_instancing():
                raise GPUBackendNotAvailableError("OpenGL instancing not supported")

            try:
                self._context_manager.ensure_initialized()
                self._pipeline_manager.setup_viewport()
                self._state_manager.setup_render_state()

                program_id = self._program_manager.get_program(shader.name)
                if program_id is None:
                    raise GPUShaderCompilationError(f"No program found for shader {shader.name}")

                self._program_manager.use_program(program_id)

                vao_id = self._instancing_manager.setup_instanced_vao(geometry, shader.name, instance_data)
                self._instancing_manager.render_instances(vao_id, geometry, instance_count)

                self._vao_manager.unbind_vao()
                self._program_manager.unbind_program()

                logger.debug(f"Rendered {instance_count} instances of geometry with {geometry.vertex_count} vertices using OpenGL instancing")

            except Exception as e:
                logger.warning(f"OpenGL instanced rendering failed: {e}, falling back to CPU")
                # Fall back to CPU rendering
                from ornata.api.exports.gpu import CPUFallback

                cpu_fallback = CPUFallback()
                for _ in range(instance_count):
                    cpu_fallback.render_geometry(geometry, shader)

    def render_geometry_batched(self, geometries: list[Geometry], shader: Shader) -> None:
        """Render multiple geometries using instanced rendering when possible.

        Args:
            geometries: List of geometries to render.
            shader: The shader to use for rendering.

        Raises:
            GPUBackendNotAvailableError: If OpenGL is not available.
        """
        with self._lock:
            if not self.is_available():
                raise GPUBackendNotAvailableError("OpenGL backend not available")

            if not geometries:
                return

            try:
                self._context_manager.ensure_initialized()
                self._pipeline_manager.setup_viewport()
                self._state_manager.setup_render_state()

                program_id = self._program_manager.get_program(shader.name)
                if program_id is None:
                    raise GPUShaderCompilationError(f"No program found for shader {shader.name}")

                self._program_manager.use_program(program_id)

                # For now, render each geometry individually but with optimized state management
                for geometry in geometries:
                    vao_key = f"{shader.name}_batched_{id(geometry)}"
                    vao_id = self._vao_manager.get_or_create_vao(geometry, vao_key)
                    self._vbo_manager.setup_vertex_data(vao_id, geometry)

                    if geometry.indices:
                        self._vao_manager.setup_index_data(vao_id, geometry)

                    self._vao_manager.bind_vao(vao_id)

                    if geometry.indices:
                        self._vao_manager.draw_indexed(geometry.index_count)
                    else:
                        self._vao_manager.draw_arrays(geometry.vertex_count)

                    self._vao_manager.unbind_vao()

                self._program_manager.unbind_program()

                logger.debug(f"Rendered {len(geometries)} geometries using batched OpenGL rendering")

            except Exception as e:
                logger.warning(f"Batched OpenGL rendering failed: {e}, falling back to CPU")
                # Fall back to CPU rendering
                from ornata.api.exports.gpu import CPUFallback

                cpu_fallback = CPUFallback()
                for geometry in geometries:
                    cpu_fallback.render_geometry(geometry, shader)

    def cleanup(self) -> None:
        """Clean up OpenGL resources."""
        with self._lock:
            try:
                self._program_manager.cleanup()
                self._vao_manager.cleanup()
                self._vbo_manager.cleanup()
                self._instancing_manager.cleanup()
                self._context_manager.cleanup()

                logger.debug("OpenGL backend cleaned up")

            except Exception as e:
                logger.error(f"Error during OpenGL cleanup: {e}")
                # Don't re-raise during cleanup

    # -------------------------- Stage Compilation ---------------------------
    def compile_vertex_shader(self, source: str) -> object:
        """Compile a vertex shader.

        Parameters:
            source: GLSL source for the vertex stage.

        Returns:
            OpenGL shader object identifier (int).
        """
        with self._lock:
            self._context_manager.ensure_initialized()
            return int(self._shader_compiler.compile_vertex_shader("__vtx__", source))

    def compile_fragment_shader(self, source: str) -> object:
        """Compile a fragment shader.

        Parameters:
            source: GLSL source for the fragment stage.

        Returns:
            OpenGL shader object identifier (int).
        """
        with self._lock:
            self._context_manager.ensure_initialized()
            return int(self._shader_compiler.compile_fragment_shader("__frag__", source))

    def compile_geometry_shader(self, source: str) -> object:
        """OpenGL geometry shaders are not provided here.

        Parameters:
            source: GLSL source for the geometry stage.

        Returns:
            Never returns; raises error.
        """
        raise GPUBackendNotAvailableError("OpenGL geometry shaders not supported in this build")

    def compile_mesh_shader(self, source: str) -> object:
        """OpenGL mesh/task shaders are not supported.

        Parameters:
            source: GLSL source.

        Returns:
            Never returns; raises error.
        """
        raise GPUBackendNotAvailableError("OpenGL mesh shaders not supported")

    def compile_task_shader(self, source: str) -> object:
        """OpenGL task shaders are not supported.

        Parameters:
            source: GLSL source.

        Returns:
            Never returns; raises error.
        """
        raise GPUBackendNotAvailableError("OpenGL task shaders not supported")

    def compile_tess_control_shader(self, source: str) -> object:
        """OpenGL tessellation not provided here.

        Parameters:
            source: GLSL source.

        Returns:
            Never returns; raises error.
        """
        raise GPUBackendNotAvailableError("OpenGL tessellation shaders not supported in this build")

    def compile_tess_eval_shader(self, source: str) -> object:
        """OpenGL tessellation not provided here.

        Parameters:
            source: GLSL source.

        Returns:
            Never returns; raises error.
        """
        raise GPUBackendNotAvailableError("OpenGL tessellation shaders not supported in this build")

    def compile_compute_shader(self, source: str) -> object:
        """OpenGL compute shaders are not implemented here.

        Parameters:
            source: GLSL source.

        Returns:
            Never returns; raises error.
        """
        raise GPUBackendNotAvailableError("OpenGL compute shaders not supported in this build")

    def compile_raygen_shader(self, source: str) -> object:
        """Ray tracing not supported by OpenGL backend."""
        raise GPUBackendNotAvailableError("OpenGL ray tracing not supported")

    def compile_miss_shader(self, source: str) -> object:
        """Ray tracing not supported by OpenGL backend."""
        raise GPUBackendNotAvailableError("OpenGL ray tracing not supported")

    def compile_closesthit_shader(self, source: str) -> object:
        """Ray tracing not supported by OpenGL backend."""
        raise GPUBackendNotAvailableError("OpenGL ray tracing not supported")

    # -------------------------- Pipeline Builders ---------------------------
    def create_tessellation_pipeline(self, name: str, vs_src: str, tcs_src: str, tes_src: str, fs_src: str) -> Shader:
        """Tessellation pipeline unsupported for OpenGL in this build.

        Parameters:
            name: Pipeline name.
            vs_src: Vertex shader source.
            tcs_src: Tessellation control shader source.
            tes_src: Tessellation evaluation shader source.
            fs_src: Fragment shader source.

        Returns:
            Never returns; raises error.
        """
        raise GPUBackendNotAvailableError("OpenGL tessellation pipeline not supported")

    def create_mesh_pipeline(self, name: str, task_src: str | None, mesh_src: str, fs_src: str) -> Shader:
        """Mesh pipeline unsupported for OpenGL in this build.

        Parameters:
            name: Pipeline name.
            task_src: Task shader source or None.
            mesh_src: Mesh shader source.
            fs_src: Fragment shader source.

        Returns:
            Never returns; raises error.
        """
        raise GPUBackendNotAvailableError("OpenGL mesh pipeline not supported")

    def create_compute(self, name: str, cs_src: str) -> Shader:
        """Compute program unsupported for OpenGL in this build.

        Parameters:
            name: Program name.
            cs_src: Compute shader source.

        Returns:
            Never returns; raises error.
        """
        raise GPUBackendNotAvailableError("OpenGL compute not supported")

    def create_raytracing_pipeline(self, name: str, rgen_src: str, rmiss_src: str, rchit_src: str, anyhit_src: str | None) -> Shader:
        """Ray tracing pipeline unsupported for OpenGL in this build."""
        raise GPUBackendNotAvailableError("OpenGL ray tracing pipeline not supported")
