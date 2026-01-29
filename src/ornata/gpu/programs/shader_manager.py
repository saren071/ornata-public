# file: programs/shader_manager.py
from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.gpu.misc import GPUBackend, Shader

logger = get_logger(__name__)


class ShaderManager:
    """Manages shader compilation, caching, and pipeline creation for all stages."""

    def __init__(self) -> None:
        self._shaders: dict[str, Shader] = {}
        self._lock = threading.RLock()
        self._backend: GPUBackend | None = None

    def set_backend(self, backend: GPUBackend) -> None:
        with self._lock:
            self._backend = backend

    # ------- Raster (VS/FS) -------
    def create_shader(self, name: str, vertex_src: str, fragment_src: str) -> Shader | None:
        with self._lock:
            if name in self._shaders:
                return self._shaders[name]
            if self._backend is None:
                from ornata.api.exports.definitions import GPUBackendNotAvailableError
                raise GPUBackendNotAvailableError("No GPU backend available for shader compilation")
            try:
                shader = self._backend.create_shader(name, vertex_src, fragment_src)
                if shader is not None:
                    self._shaders[name] = shader
                logger.debug(f"Created raster shader program: {name}")
                return shader
            except Exception as e:
                msg = f"GPU shader creation failed for {name}: {e}"
                logger.error(msg)
                from ornata.api.exports.definitions import GPUShaderCompilationError
                raise GPUShaderCompilationError(msg) from e

    def batch_compile_shaders(self, defs: list[tuple[str, str, str]]) -> dict[str, Shader]:
        with self._lock:
            if self._backend is None:
                from ornata.api.exports.definitions import GPUBackendNotAvailableError
                raise GPUBackendNotAvailableError("No GPU backend available for batch shader compilation")
            out: dict[str, Shader] = {}
            for name, vs, fs in defs:
                if name in self._shaders:
                    out[name] = self._shaders[name]
                    continue
                try:
                    prog = self._backend.create_shader(name, vs, fs)
                    if prog is not None:
                        self._shaders[name] = out[name] = prog
                    logger.debug(f"Batch-compiled: {name}")
                except Exception as e:
                    msg = f"Batch compile failed for {name}: {e}"
                    logger.error(msg)
                    from ornata.api.exports.definitions import GPUShaderCompilationError
                    raise GPUShaderCompilationError(msg) from e
            return out

    # ------- Tessellation Pipeline (VS+TCS+TES+FS) -------
    def create_tessellation_pipeline(self, name: str, vs_src: str, tcs_src: str, tes_src: str, fs_src: str) -> Shader:
        with self._lock:
            if name in self._shaders:
                return self._shaders[name]
            if self._backend is None or not hasattr(self._backend, "create_tessellation_pipeline"):
                from ornata.api.exports.definitions import GPUBackendNotAvailableError
                raise GPUBackendNotAvailableError("Backend lacks tessellation pipeline creation")
            try:
                pipeline: Shader = self._backend.create_tessellation_pipeline(name, vs_src, tcs_src, tes_src, fs_src)
                self._shaders[name] = pipeline
                logger.debug(f"Created tessellation pipeline: {name}")
                return pipeline
            except Exception as e:
                msg = f"Tessellation pipeline creation failed for {name}: {e}"
                logger.error(msg)
                from ornata.api.exports.definitions import GPUShaderCompilationError
                raise GPUShaderCompilationError(msg) from e

    # ------- Mesh Pipeline (Task+Mesh+FS) -------
    def create_mesh_pipeline(self, name: str, task_src: str | None, mesh_src: str, fs_src: str) -> Shader:
        with self._lock:
            if name in self._shaders:
                return self._shaders[name]
            if self._backend is None or not hasattr(self._backend, "create_mesh_pipeline"):
                from ornata.api.exports.definitions import GPUBackendNotAvailableError
                raise GPUBackendNotAvailableError("Backend lacks mesh pipeline creation")
            try:
                pipeline: Shader = self._backend.create_mesh_pipeline(name, task_src, mesh_src, fs_src)
                self._shaders[name] = pipeline
                logger.debug(f"Created mesh pipeline: {name}")
                return pipeline
            except Exception as e:
                msg = f"Mesh pipeline creation failed for {name}: {e}"
                logger.error(msg)
                from ornata.api.exports.definitions import GPUShaderCompilationError
                raise GPUShaderCompilationError(msg) from e

    # ------- Compute -------
    def create_compute(self, name: str, cs_src: str) -> Shader:
        with self._lock:
            if name in self._shaders:
                return self._shaders[name]
            if self._backend is None or not hasattr(self._backend, "create_compute"):
                from ornata.api.exports.definitions import GPUBackendNotAvailableError
                raise GPUBackendNotAvailableError("Backend lacks compute creation")
            try:
                prog: Shader = self._backend.create_compute(name, cs_src)
                self._shaders[name] = prog
                logger.debug(f"Created compute program: {name}")
                return prog
            except Exception as e:
                msg = f"Compute creation failed for {name}: {e}"
                logger.error(msg)
                from ornata.api.exports.definitions import GPUShaderCompilationError
                raise GPUShaderCompilationError(msg) from e

    # ------- Ray Tracing Pipeline (RGEN + RMISS + RCHIT [optional anyhit]) -------
    def create_raytracing_pipeline(
        self,
        name: str,
        rgen_src: str,
        rmiss_src: str,
        rchit_src: str,
        anyhit_src: str | None = None,
    ) -> Shader:
        with self._lock:
            if name in self._shaders:
                return self._shaders[name]
            if self._backend is None or not hasattr(self._backend, "create_raytracing_pipeline"):
                from ornata.api.exports.definitions import GPUBackendNotAvailableError
                raise GPUBackendNotAvailableError("Backend lacks ray tracing pipeline creation")
            try:
                pipeline: Shader = self._backend.create_raytracing_pipeline(name, rgen_src, rmiss_src, rchit_src, anyhit_src)
                self._shaders[name] = pipeline
                logger.debug(f"Created ray tracing pipeline: {name}")
                return pipeline
            except Exception as e:
                msg = f"Ray tracing pipeline creation failed for {name}: {e}"
                logger.error(msg)
                from ornata.api.exports.definitions import GPUShaderCompilationError
                raise GPUShaderCompilationError(msg) from e

    # ------- Utilities -------
    def get_shader(self, name: str) -> Shader | None:
        with self._lock:
            return self._shaders.get(name)

    def has_shader(self, name: str) -> bool:
        with self._lock:
            return name in self._shaders

    def clear_cache(self) -> None:
        with self._lock:
            self._shaders.clear()
            logger.debug("Shader cache cleared")

    # Basic but useful source validation for VS/FS (other stages are backend-validated)
    def validate_shader_sources(self, vertex_src: str, fragment_src: str) -> bool:
        if not vertex_src or not fragment_src:
            return False
        if "#version" not in vertex_src or "#version" not in fragment_src:
            return False
        if "void main(" not in vertex_src or "void main(" not in fragment_src:
            return False
        return True

    # Link convenience (if backend exposes it)
    def link_program(self, vertex_shader: Shader, fragment_shader: Shader) -> Any | tuple[Shader, Shader] | None:
        if self._backend is None:
            logger.warning("No GPU backend available for linking")
            return None

# HLSL loader functions removed: DirectX compiler performs GLSL→HLSL translation internally
