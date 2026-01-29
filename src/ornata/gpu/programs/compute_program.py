# file: programs/compute_program.py
from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from ornata.api.exports.definitions import CompilationResult, RendererType
from ornata.gpu.programs.base import ShaderProgramBase

if TYPE_CHECKING:
    from ornata.gpu.misc import GPUBackend

ComputeVariant = Literal["image", "ssbo"]


class ComputeProgram(ShaderProgramBase):
    """Manages compute shaders. Supports 'image' and 'ssbo' default variants."""

    _variant: ComputeVariant

    def __init__(self, source: str | None = None, variant: ComputeVariant = "image") -> None:
        self._variant = variant
        default = ["compute", "image_compute.glsl"] if variant == "image" else ["compute", "ssbo_compute.glsl"]
        super().__init__(default, source)

    def compile(self, backend: GPUBackend) -> CompilationResult:
        if not hasattr(backend, "compile_compute_shader"):
            return CompilationResult(
                bytecode=b"",
                errors=["Backend does not support compute shader compilation"],
                warnings=[],
                success=False,
                renderer_type=RendererType.CPU
            )
        
        is_valid, validation_errors = self.validate_source()
        if not is_valid:
            return CompilationResult(
                bytecode=b"",
                errors=validation_errors,
                warnings=[],
                success=False,
                renderer_type=RendererType.CPU
            )
        
        try:
            self._compiled_program = backend.compile_compute_shader(self._source)
            if self._compiled_program is None:
                return CompilationResult(
                    bytecode=b"",
                    errors=["Compute shader compilation failed: backend returned None"],
                    warnings=[],
                    success=False,
                    renderer_type=RendererType.CPU
                )
            self._compiled = True
            return CompilationResult(
                bytecode=self._compiled_program,
                errors=[],
                warnings=[],
                success=True,
                renderer_type=RendererType.CPU
            )
        except Exception as e:
            return CompilationResult(
                bytecode=b"",
                errors=[f"Compute shader compilation error: {str(e)}"],
                warnings=[],
                success=False,
                renderer_type=RendererType.CPU
            )

    @property
    def variant(self) -> ComputeVariant:
        return self._variant
