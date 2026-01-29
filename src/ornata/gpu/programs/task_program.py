# file: programs/task_program.py
from __future__ import annotations

from typing import TYPE_CHECKING

from ornata.gpu.programs.base import ShaderProgramBase

if TYPE_CHECKING:
    from ornata.gpu.misc import GPUBackend


class TaskProgram(ShaderProgramBase):
    def __init__(self, source: str | None = None) -> None:
        super().__init__(["task", "default.glsl"], source)

    def compile(self, backend: GPUBackend) -> None:
        if not hasattr(backend, "compile_task_shader"):
            raise RuntimeError("Backend does not support task shader compilation")
        self._compiled_program = backend.compile_task_shader(self._source)
        if self._compiled_program is None:
            raise RuntimeError("Task shader compilation failed: backend returned None")
        self._compiled = True
