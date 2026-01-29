# file: programs/base.py
from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING, Any

from ornata.api.exports.definitions import RendererType

if TYPE_CHECKING:
    from ornata.api.exports.definitions import CompilationResult, ShaderMacro


class ShaderProgramBase:
    """Base utilities for shader program source loading with comprehensive backend support."""

    def __init__(self, default_rel_path: list[str], source: str | None = None) -> None:
        self._compiled: bool = False
        self._compiled_program: Any | None = None
        self._source: str = source or self._load_source_from(default_rel_path)
        self._compilation_time_ms: float = 0.0
        self._renderer_type: RendererType | None = None
        self._errors: list[str] = []
        self._warnings: list[str] = []
        self._macros: list[ShaderMacro] = []
        self._uniforms: dict[str, Any] = {}
        self._attributes: dict[str, Any] = {}

    def _load_source_from(self, rel_parts: list[str]) -> str:
        shader_path = os.path.join(os.path.dirname(__file__), "shaders", *rel_parts)
        try:
            with open(shader_path, encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Shader file not found: {shader_path}") from e
        except OSError as e:
            raise OSError(f"Failed to read shader file: {shader_path}") from e

    def compile(self, backend: Any) -> CompilationResult:
        """Compile shader for backend.
        
        Args:
            backend: GPU backend to compile for
            
        Returns:
            CompilationResult with success status and errors
        """
        start_time = time.time()
        self._errors.clear()
        self._warnings.clear()
        
        try:
            # Validate backend compatibility
            if not hasattr(backend, "is_available") or not backend.is_available():
                self._errors.append("Backend is not available")
                self._compiled = False
                return self._create_compilation_result(False, start_time)
            
            # Backend-specific compilation
            compilation_result = self._compile_backend_specific(backend)
            self._compiled = compilation_result.success
            
            if compilation_result.success:
                self._compiled_program = compilation_result.bytecode
                self._renderer_type = compilation_result.renderer_type
                self._compilation_time_ms = compilation_result.compilation_time_ms
            else:
                self._errors.extend(compilation_result.errors)
                
            return compilation_result
            
        except Exception as e:
            self._errors.append(f"Unexpected compilation error: {str(e)}")
            self._compiled = False
            return self._create_compilation_result(False, start_time)

    def _compile_backend_specific(self, backend: Any) -> CompilationResult:
        """Backend-specific compilation logic."""
        backend_type = self._detect_backend_type(backend)
        
        if backend_type == RendererType.DIRECTX11:
            return self._compile_directx(backend)
        elif backend_type == RendererType.OPENGL:
            return self._compile_opengl(backend)
        else:
            return self._compile_fallback(backend)

    def _compile_directx(self, backend: Any) -> CompilationResult:
        """Compile using DirectX backend."""
        from ornata.api.exports.definitions import CompilationResult, RendererType
        if not hasattr(backend, "compile_shader"):
            return CompilationResult(
                bytecode=b"",
                errors=["Backend does not support DirectX compilation"],
                warnings=[],
                success=False,
                renderer_type=RendererType.DIRECTX11
            )
        
        try:
            # Apply macros to source
            processed_source = self._apply_macros(self._source)
            
            # Compile with DirectX backend
            result = backend.compile_shader(
                processed_source,
                "vs_5_0",  # Target for vertex shaders, should be configurable
                "main"
            )
            
            if result is None:
                return CompilationResult(
                    bytecode=b"",
                    errors=["DirectX compilation failed - null result"],
                    warnings=[],
                    success=False,
                    renderer_type=RendererType.DIRECTX11
                )
            
            return CompilationResult(
                bytecode=result,
                errors=[],
                warnings=[],
                success=True,
                renderer_type=RendererType.DIRECTX11
            )
        except Exception as e:
            return CompilationResult(
                bytecode=b"",
                errors=[f"DirectX compilation error: {str(e)}"],
                warnings=[],
                success=False,
                renderer_type=RendererType.DIRECTX11
            )

    def _compile_opengl(self, backend: Any) -> CompilationResult:
        """Compile using OpenGL backend."""
        from ornata.api.exports.definitions import CompilationResult, RendererType
        if not hasattr(backend, "compile_shader"):
            return CompilationResult(
                bytecode=b"",
                errors=["Backend does not support OpenGL compilation"],
                warnings=[],
                success=False,
                renderer_type=RendererType.OPENGL
            )
        
        try:
            # Apply macros to source
            processed_source = self._apply_macros(self._source)
            
            # Compile with OpenGL backend
            shader_id = backend.compile_shader(processed_source)
            
            if shader_id is None:
                return CompilationResult(
                    bytecode=b"",
                    errors=["OpenGL compilation failed - null result"],
                    warnings=[],
                    success=False,
                    renderer_type=RendererType.OPENGL
                )
            
            return CompilationResult(
                bytecode=shader_id,
                errors=[],
                warnings=[],
                success=True,
                renderer_type=RendererType.OPENGL
            )
        except Exception as e:
            return CompilationResult(
                bytecode=b"",
                errors=[f"OpenGL compilation error: {str(e)}"],
                warnings=[],
                success=False,
                renderer_type=RendererType.OPENGL
            )

    def _compile_stage_shader(
        self,
        backend: Any,
        method_name: str,
        stage_label: str,
    ) -> CompilationResult:
        """Compile a specific shader stage using the backend-provided method."""
        from ornata.api.exports.definitions import CompilationResult

        start_time = time.time()
        self._errors.clear()
        self._warnings.clear()

        renderer_type = self._detect_backend_type(backend)
        compiler = getattr(backend, method_name, None)

        if not callable(compiler):
            message = f"Backend does not support {stage_label} shader compilation"
            self._compiled = False
            self._renderer_type = renderer_type
            return CompilationResult(
                bytecode=b"",
                errors=[message],
                warnings=[],
                success=False,
                renderer_type=renderer_type,
                compilation_time_ms=(time.time() - start_time) * 1000.0,
            )

        try:
            compiled = compiler(self._source)
            if compiled is None:
                message = f"{stage_label} shader compilation failed: backend returned None"
                self._errors.append(message)
                self._compiled = False
                self._renderer_type = renderer_type
                self._compilation_time_ms = (time.time() - start_time) * 1000.0
                return CompilationResult(
                    bytecode=b"",
                    errors=[message],
                    warnings=[],
                    success=False,
                    renderer_type=renderer_type,
                    compilation_time_ms=self._compilation_time_ms,
                )

            self._compiled_program = compiled
            self._compiled = True
            self._renderer_type = renderer_type
            self._compilation_time_ms = (time.time() - start_time) * 1000.0

            return CompilationResult(
                bytecode=compiled,
                errors=[],
                warnings=[],
                success=True,
                renderer_type=renderer_type,
                compilation_time_ms=self._compilation_time_ms,
            )

        except Exception as exc:  # pragma: keep
            message = f"{stage_label} shader compilation error: {str(exc)}"
            self._errors.append(message)
            self._compiled = False
            self._renderer_type = renderer_type
            return CompilationResult(
                bytecode=b"",
                errors=[message],
                warnings=[],
                success=False,
                renderer_type=renderer_type,
                compilation_time_ms=(time.time() - start_time) * 1000.0,
            )

    def _compile_fallback(self, backend: Any) -> CompilationResult:
        """Compile using CPU fallback."""
        from ornata.api.exports.definitions import CompilationResult, RendererType
        # Placeholder for CPU fallback compilation
        return CompilationResult(
            bytecode=b"",
            errors=["CPU fallback compilation not yet implemented"],
            warnings=[],
            success=False,
            renderer_type=RendererType.CPU
        )

    def _detect_backend_type(self, backend: Any) -> RendererType:
        """Detect backend type from backend object."""
        from ornata.api.exports.definitions import RendererType
        backend_name = getattr(backend, "__class__", "").name.lower()
        
        if "directx" in backend_name or "d3d" in backend_name:
            return RendererType.DIRECTX11
        elif "opengl" in backend_name or "gl" in backend_name:
            return RendererType.OPENGL
        else:
            return RendererType.CPU

    def _apply_macros(self, source: str) -> str:
        """Apply shader macros to source code."""
        if not self._macros:
            return source
        
        result = source
        for macro in self._macros:
            result = f"#define {macro.name} {macro.definition}\n{result}"
        
        return result

    def _create_compilation_result(self, success: bool, start_time: float) -> CompilationResult:
        """Create a compilation result."""
        from ornata.api.exports.definitions import CompilationResult, RendererType
        return CompilationResult(
            bytecode=b"" if not success else self._compiled_program,
            errors=self._errors.copy(),
            warnings=self._warnings.copy(),
            success=success,
            renderer_type=self._renderer_type or RendererType.CPU,
            compilation_time_ms=(time.time() - start_time) * 1000.0
        )

    def is_compiled(self) -> bool:
        """Check if shader is compiled successfully."""
        return self._compiled

    def get_source(self) -> str:
        """Get shader source code."""
        return self._source

    def get_compiled_program(self) -> Any:
        """Get compiled shader program handle."""
        return self._compiled_program

    @property
    def handle(self) -> Any | None:
        """Get compiled shader program handle (alias for compatibility)."""
        return self._compiled_program

    @property
    def compilation_time_ms(self) -> float:
        """Get compilation time in milliseconds."""
        return self._compilation_time_ms

    @property
    def renderer_type(self) -> RendererType | None:
        """Get renderer type used for compilation."""
        return self._renderer_type

    @property
    def errors(self) -> list[str]:
        """Get compilation errors."""
        return self._errors.copy()

    @property
    def warnings(self) -> list[str]:
        """Get compilation warnings."""
        return self._warnings.copy()

    def add_macro(self, name: str, definition: str) -> None:
        """Add shader macro definition.
        
        Args:
            name: Macro name
            definition: Macro definition
        """
        from ornata.api.exports.definitions import ShaderMacro
        self._macros.append(ShaderMacro(name=name, definition=definition))

    def set_uniform(self, name: str, value: Any) -> None:
        """Set shader uniform value.
        
        Args:
            name: Uniform name
            value: Uniform value
        """
        self._uniforms[name] = value

    def set_attribute(self, name: str, location: int, type_name: str, size_bytes: int) -> None:
        """Set shader attribute information.
        
        Args:
            name: Attribute name
            location: Attribute location
            type_name: Attribute type name
            size_bytes: Attribute size in bytes
        """
        self._attributes[name] = {
            "location": location,
            "type_name": type_name,
            "size_bytes": size_bytes
        }

    def validate_source(self) -> tuple[bool, list[str]]:
        """Validate shader source for security and correctness.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors: list[str] = []
        
        # Basic validation checks
        if not self._source.strip():
            errors.append("Shader source is empty")
        
        # Security checks - prevent infinite loops and malicious code
        if "while(true)" in self._source.lower() or "for(;;)" in self._source:
            errors.append("Potential infinite loop detected")
        
        # Check for dangerous operations
        dangerous_keywords = ["system(", "exec(", "subprocess", "os.system"]
        for keyword in dangerous_keywords:
            if keyword in self._source.lower():
                errors.append(f"Dangerous keyword detected: {keyword}")
        
        return len(errors) == 0, errors

    def cleanup(self) -> None:
        """Cleanup compiled resources."""
        self._compiled = False
        self._compiled_program = None
        self._backend_type = None
        self._errors.clear()
        self._warnings.clear()
        self._macros.clear()
        self._uniforms.clear()
        self._attributes.clear()
