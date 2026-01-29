# file: programs/tess_control_program.py
from __future__ import annotations

from typing import TYPE_CHECKING

from ornata.gpu.programs.base import ShaderProgramBase

if TYPE_CHECKING:
    from ornata.api.exports.definitions import CompilationResult
    from ornata.gpu.misc import GPUBackend


class TessControlProgram(ShaderProgramBase):
    def __init__(self, source: str | None = None) -> None:
        super().__init__(["tess_control", "default.glsl"], source)

    def compile(self, backend: GPUBackend) -> CompilationResult:
        if not hasattr(backend, "compile_tess_control_shader"):
            raise RuntimeError("Backend does not support tessellation control compilation")
        self._compiled_program = backend.compile_tess_control_shader(self._source)
        if self._compiled_program is None:
            raise RuntimeError("Tess control compilation failed: backend returned None")
        self._compiled = True
