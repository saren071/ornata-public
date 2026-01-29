# file: programs/vertex_program.py
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ornata.gpu.programs.base import ShaderProgramBase

if TYPE_CHECKING:
    from ornata.api.exports.definitions import CompilationResult
    from ornata.gpu.misc import GPUBackend


class VertexProgram(ShaderProgramBase):
    """Vertex shader program with comprehensive backend support."""
    
    def __init__(self, source: str | None = None) -> None:
        """Initialize vertex shader program.
        
        Args:
            source: Optional vertex shader source code
        """
        super().__init__(["vertex", "default.glsl"], source)
        
        # Set up standard vertex attributes
        self.set_attribute("position", 0, "vec2", 8)
        self.set_attribute("color", 1, "vec4", 16)
        self.set_attribute("texcoord", 2, "vec2", 8)
        
        # Add standard vertex shader macros
        self.add_macro("VERTEX_SHADER", "1")
        self.add_macro("MAX_VERTICES", "65536")

    def compile(self, backend: GPUBackend) -> CompilationResult:
        """Compile vertex shader for backend.
        
        Args:
            backend: GPU backend to compile for
            
        Returns:
            CompilationResult with success status and errors
        """
        # Validate source before compilation
        from ornata.api.exports.definitions import CompilationResult, RendererType
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
            # Set vertex-specific uniform defaults
            self.set_uniform("u_model_view_proj", [1.0, 0.0, 0.0, 0.0,
                                                  0.0, 1.0, 0.0, 0.0,
                                                  0.0, 0.0, 1.0, 0.0,
                                                  0.0, 0.0, 0.0, 1.0])
            self.set_uniform("u_opacity", 1.0)
        
        return result

    def _compile_backend_specific(self, backend: Any) -> CompilationResult:
        """Backend-specific vertex shader compilation."""
        from ornata.api.exports.definitions import RendererType
        backend_type = self._detect_backend_type(backend)
        
        if backend_type == RendererType.DIRECTX11:
            return self._compile_directx11_vertex(backend)
        elif backend_type == RendererType.OPENGL:
            return self._compile_opengl_vertex(backend)
        else:
            # Delegate to base class for other backends
            return super()._compile_backend_specific(backend)

    def _compile_directx11_vertex(self, backend: Any) -> CompilationResult:
        """Compile vertex shader using DirectX backend."""
        from ornata.api.exports.definitions import CompilationResult, RendererType
        if not hasattr(backend, "compile_vertex_shader"):
            return CompilationResult(
                bytecode=b"",
                errors=["Renderer does not support DirectX11 vertex shader compilation"],
                warnings=[],
                success=False,
                renderer_type=RendererType.DIRECTX11
            )
        
        try:
            # Process source with DirectX-specific macros
            directx_source = self._apply_directx11_macros(self._source)
            
            # Compile vertex shader
            vertex_shader = backend.compile_vertex_shader(directx_source)
            
            if vertex_shader is None:
                return CompilationResult(
                    bytecode=b"",
                    errors=["DirectX11 vertex shader compilation failed"],
                    warnings=[],
                    success=False,
                    renderer_type=RendererType.DIRECTX11
                )
            
            return CompilationResult(
                bytecode=vertex_shader,
                errors=[],
                warnings=[],
                success=True,
                renderer_type=RendererType.DIRECTX11
            )
        except Exception as e:
            return CompilationResult(
                bytecode=b"",
                errors=[f"DirectX11 vertex shader compilation error: {str(e)}"],
                warnings=[],
                success=False,
                renderer_type=RendererType.DIRECTX11
            )

    def _compile_opengl_vertex(self, backend: Any) -> CompilationResult:
        """Compile vertex shader using OpenGL backend."""
        from ornata.api.exports.definitions import CompilationResult, RendererType
        if not hasattr(backend, "compile_vertex_shader"):
            return CompilationResult(
                bytecode=b"",
                errors=["Renderer does not support OpenGL vertex shader compilation"],
                warnings=[],
                success=False,
                renderer_type=RendererType.OPENGL
            )
        
        try:
            # Process source with OpenGL-specific macros
            opengl_source = self._apply_opengl_macros(self._source)
            
            # Compile vertex shader
            vertex_shader_id = backend.compile_vertex_shader(opengl_source)
            
            if vertex_shader_id is None:
                return CompilationResult(
                    bytecode=b"",
                    errors=["OpenGL vertex shader compilation failed"],
                    warnings=[],
                    success=False,
                    renderer_type=RendererType.OPENGL
                )
            
            return CompilationResult(
                bytecode=vertex_shader_id,
                errors=[],
                warnings=[],
                success=True,
                renderer_type=RendererType.OPENGL
            )
        except Exception as e:
            return CompilationResult(
                bytecode=b"",
                errors=[f"OpenGL vertex shader compilation error: {str(e)}"],
                warnings=[],
                success=False,
                renderer_type=RendererType.OPENGL
            )

    def _apply_directx11_macros(self, source: str) -> str:
        """Apply DirectX11-specific macros to vertex shader source."""
        directx_macros = [
            "#define HLSL 1",
            "#define VERTEX_SHADER 1",
            "#define MAX_TEXTURE_COORDS 8",
            "#define MAX_VERTEX_ATTRIBS 16"
        ]
        
        return "\n".join(directx_macros) + "\n" + source

    def _apply_opengl_macros(self, source: str) -> str:
        """Apply OpenGL-specific macros to vertex shader source."""
        opengl_macros = [
            "#version 460 core",
            "#define GLSL 1",
            "#define VERTEX_SHADER 1"
        ]
        
        return "\n".join(opengl_macros) + "\n" + source

    def create_input_layout(self, backend: Any) -> Any:
        """Create input layout for DirectX backends.
        
        Args:
            backend: GPU backend
            
        Returns:
            Input layout object for DirectX or None for other backends
        """
        if not hasattr(backend, "create_input_layout"):
            return None
        
        # Define standard input layout for vertex shaders
        input_elements = [
            {"semantic": "POSITION", "index": 0, "format": "DXGI_FORMAT_R32G32_FLOAT"},
            {"semantic": "COLOR", "index": 0, "format": "DXGI_FORMAT_R8G8B8A8_UNORM"},
            {"semantic": "TEXCOORD", "index": 0, "format": "DXGI_FORMAT_R32G32_FLOAT"},
        ]
        
        return backend.create_input_layout(input_elements)


def load_vertex_program_source() -> str:
    """Load default GLSL vertex shader source.

    Returns:
        The default vertex shader GLSL source as a string.
    """
    return VertexProgram().get_source()


def create_default_vertex_program() -> VertexProgram:
    """Create a default vertex shader program.
    
    Returns:
        VertexProgram instance with default configuration
    """
    program = VertexProgram()
    
    # Add standard uniforms for UI rendering
    program.set_uniform("u_color", [1.0, 1.0, 1.0, 1.0])
    program.set_uniform("u_resolution", [1920.0, 1080.0])
    program.set_uniform("u_time", 0.0)
    
    return program
