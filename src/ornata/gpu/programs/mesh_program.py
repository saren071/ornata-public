# file: programs/mesh_program.py
from __future__ import annotations

from typing import TYPE_CHECKING

from ornata.gpu.programs.base import ShaderProgramBase

if TYPE_CHECKING:
    from ornata.api.exports.definitions import CompilationResult
    from ornata.gpu.misc import GPUBackend


class MeshProgram(ShaderProgramBase):
    def __init__(self, source: str | None = None) -> None:
        super().__init__(["mesh", "default.glsl"], source)

    def compile(self, backend: "GPUBackend") -> "CompilationResult":
        return self._compile_stage_shader(backend, "compile_mesh_shader", "Mesh")
