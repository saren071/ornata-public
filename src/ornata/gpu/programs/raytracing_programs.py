# file: programs/raytracing_programs.py
from __future__ import annotations

from typing import TYPE_CHECKING

from ornata.gpu.programs.base import ShaderProgramBase

if TYPE_CHECKING:
    from ornata.api.exports.definitions import CompilationResult
    from ornata.gpu.misc import GPUBackend


class RayGenProgram(ShaderProgramBase):
    def __init__(self, source: str | None = None) -> None:
        super().__init__(["raytracing", "rgen.glsl"], source)

    def compile(self, backend: GPUBackend) -> CompilationResult:
        if not hasattr(backend, "compile_raygen_shader"):
            raise RuntimeError("Backend does not support raygen shader compilation")
        self._compiled_program = backend.compile_raygen_shader(self._source)
        if self._compiled_program is None:
            raise RuntimeError("Raygen shader compilation failed: backend returned None")
        self._compiled = True


class RayMissProgram(ShaderProgramBase):
    def __init__(self, source: str | None = None) -> None:
        super().__init__(["raytracing", "rmiss.glsl"], source)

    def compile(self, backend: GPUBackend) -> CompilationResult:
        if not hasattr(backend, "compile_miss_shader"):
            raise RuntimeError("Backend does not support ray miss shader compilation")
        self._compiled_program = backend.compile_miss_shader(self._source)
        if self._compiled_program is None:
            raise RuntimeError("Ray miss shader compilation failed: backend returned None")
        self._compiled = True


class RayClosestHitProgram(ShaderProgramBase):
    def __init__(self, source: str | None = None) -> None:
        super().__init__(["raytracing", "rchit.glsl"], source)

    def compile(self, backend: GPUBackend) -> CompilationResult:
        if not hasattr(backend, "compile_closesthit_shader"):
            raise RuntimeError("Backend does not support ray closest-hit shader compilation")
        self._compiled_program = backend.compile_closesthit_shader(self._source)
        if self._compiled_program is None:
            raise RuntimeError("Ray closest-hit shader compilation failed: backend returned None")
        self._compiled = True
