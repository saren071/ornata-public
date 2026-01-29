# file: programs/fragment_program.py
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ornata.api.exports.definitions import CompilationResult
from ornata.definitions.enums import RendererType
from ornata.gpu.programs.base import ShaderProgramBase

if TYPE_CHECKING:
    from ornata.gpu.misc import GPUBackend


class FragmentProgram(ShaderProgramBase):
    """Fragment shader program with comprehensive backend support."""
    
    def __init__(self, source: str | None = None) -> None:
        """Initialize fragment shader program.
        
        Args:
            source: Optional fragment shader source code
        """
        super().__init__(["fragment", "default.glsl"], source)
        
        # Set up standard fragment uniforms
        self.set_uniform("u_color", [1.0, 1.0, 1.0, 1.0])
        self.set_uniform("u_opacity", 1.0)
        self.set_uniform("u_texture", 0)  # Texture slot 0
        
        # Add standard fragment shader macros
        self.add_macro("FRAGMENT_SHADER", "1")
        self.add_macro("MAX_TEXTURE_UNITS", "16")

    def compile(self, backend: GPUBackend) -> CompilationResult:
        """Compile fragment shader for backend.
        
        Args:
            backend: GPU backend to compile for
            
        Returns:
            CompilationResult with success status and errors
        """
        # Validate source before compilation
        is_valid, validation_errors = self.validate_source()
        if not is_valid:
            self._errors.extend(validation_errors)
            return CompilationResult(
                bytecode=b"",
                errors=validation_errors,
                warnings=[],
                success=False,
                renderer_type=RendererType.CPU
            )
        
        # Backend-specific compilation
        result = super().compile(backend)
        
        if result.success:
            # Set fragment-specific uniform defaults
            self.set_uniform("u_resolution", [1920.0, 1080.0])
            self.set_uniform("u_time", 0.0)
        
        return result

    def _compile_backend_specific(self, backend: Any) -> CompilationResult:
        """Backend-specific fragment shader compilation."""
        backend_type = self._detect_backend_type(backend)
        
        if backend_type == RendererType.DIRECTX11:
            return self._compile_directx_fragment(backend)
        elif backend_type == RendererType.OPENGL:
            return self._compile_opengl_fragment(backend)
        else:
            # Delegate to base class for other backends
            return super()._compile_backend_specific(backend)

    def _compile_directx_fragment(self, backend: Any) -> CompilationResult:
        """Compile fragment shader using DirectX backend."""
        if not hasattr(backend, "compile_fragment_shader"):
            return CompilationResult(
                bytecode=b"",
                errors=["Backend does not support DirectX fragment shader compilation"],
                warnings=[],
                success=False,
                renderer_type=RendererType.DIRECTX11
            )
        
        try:
            # Process source with DirectX-specific macros
            directx_source = self._apply_directx_macros(self._source)
            
            # Compile fragment shader
            fragment_shader = backend.compile_fragment_shader(directx_source)
            
            if fragment_shader is None:
                return CompilationResult(
                    bytecode=b"",
                    errors=["DirectX fragment shader compilation failed"],
                    warnings=[],
                    success=False,
                    renderer_type=RendererType.DIRECTX11
                )
            
            return CompilationResult(
                bytecode=fragment_shader,
                errors=[],
                warnings=[],
                success=True,
                renderer_type=RendererType.DIRECTX11
            )
        except Exception as e:
            return CompilationResult(
                bytecode=b"",
                errors=[f"DirectX fragment shader compilation error: {str(e)}"],
                warnings=[],
                success=False,
                renderer_type=RendererType.DIRECTX11
            )

    def _compile_opengl_fragment(self, backend: Any) -> CompilationResult:
        """Compile fragment shader using OpenGL backend."""
        if not hasattr(backend, "compile_fragment_shader"):
            return CompilationResult(
                bytecode=b"",
                errors=["Backend does not support OpenGL fragment shader compilation"],
                warnings=[],
                success=False,
                renderer_type=RendererType.OPENGL
            )
        
        try:
            # Process source with OpenGL-specific macros
            opengl_source = self._apply_opengl_macros(self._source)
            
            # Compile fragment shader
            fragment_shader_id = backend.compile_fragment_shader(opengl_source)
            
            if fragment_shader_id is None:
                return CompilationResult(
                    bytecode=b"",
                    errors=["OpenGL fragment shader compilation failed"],
                    warnings=[],
                    success=False,
                    renderer_type=RendererType.OPENGL
                )
            
            return CompilationResult(
                bytecode=fragment_shader_id,
                errors=[],
                warnings=[],
                success=True,
                renderer_type=RendererType.OPENGL
            )
        except Exception as e:
            return CompilationResult(
                bytecode=b"",
                errors=[f"OpenGL fragment shader compilation error: {str(e)}"],
                warnings=[],
                success=False,
                renderer_type=RendererType.OPENGL
            )

    def _apply_directx_macros(self, source: str) -> str:
        """Apply DirectX-specific macros to fragment shader source."""
        directx_macros = [
            "#define HLSL 1",
            "#define FRAGMENT_SHADER 1",
            "#define MAX_SAMPLERS 16",
            "#define MAX_RENDER_TARGETS 8"
        ]
        
        return "\n".join(directx_macros) + "\n" + source

    def _apply_opengl_macros(self, source: str) -> str:
        """Apply OpenGL-specific macros to fragment shader source."""
        opengl_macros = [
            "#version 460 core",
            "#define GLSL 1",
            "#define FRAGMENT_SHADER 1"
        ]
        
        return "\n".join(opengl_macros) + "\n" + source

    def enable_blending(self, backend: Any) -> None:
        """Enable blending for fragment shader.
        
        Args:
            backend: GPU backend
        """
        if hasattr(backend, "enable_blending"):
            backend.enable_blending()

    def set_blend_mode(self, backend: Any, mode: str) -> None:
        """Set blending mode for fragment shader.
        
        Args:
            backend: GPU backend
            mode: Blend mode (e.g., "alpha", "add", "multiply")
        """
        if hasattr(backend, "set_blend_mode"):
            backend.set_blend_mode(mode)


def load_fragment_program_source() -> str:
    """Load default GLSL fragment shader source.

    Returns:
        The default fragment shader GLSL source as a string.
    """
    return FragmentProgram().get_source()


def create_default_fragment_program() -> FragmentProgram:
    """Create a default fragment shader program.
    
    Returns:
        FragmentProgram instance with default configuration
    """
    program = FragmentProgram()
    
    # Add standard uniforms for UI rendering
    program.set_uniform("u_background_color", [0.0, 0.0, 0.0, 0.0])
    program.set_uniform("u_border_color", [1.0, 1.0, 1.0, 1.0])
    program.set_uniform("u_border_width", 1.0)
    program.set_uniform("u_corner_radius", 0.0)
    
    return program
