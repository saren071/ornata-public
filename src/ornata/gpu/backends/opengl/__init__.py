"""Auto-generated exports for ornata.gpu.backends.opengl."""

from __future__ import annotations

from . import backend, context, ibo, instancing, pipeline, program, shader, state, textures, ubo, utils, vao, vbo
from .backend import OpenGLBackend
from .context import OpenGLContextManager
from .ibo import OpenGLIBOManager
from .instancing import OpenGLInstancingManager
from .pipeline import OpenGLPipelineManager
from .program import OpenGLProgramManager
from .shader import OpenGLShaderCompiler
from .state import OpenGLStateManager
from .textures import OpenGLTextureManager
from .ubo import OpenGLUBOManager
from .utils import (
    check_opengl_error,
    get_max_texture_size,
    get_max_viewport_dims,
    get_opengl_extensions,
    get_opengl_version,
    has_opengl_extension,
    log_opengl_info,
)
from .vao import OpenGLVAOManager
from .vbo import OpenGLVBOManager

__all__ = [
    "OpenGLBackend",
    "OpenGLContextManager",
    "OpenGLIBOManager",
    "OpenGLInstancingManager",
    "OpenGLPipelineManager",
    "OpenGLProgramManager",
    "OpenGLShaderCompiler",
    "OpenGLStateManager",
    "OpenGLTextureManager",
    "OpenGLUBOManager",
    "OpenGLVAOManager",
    "OpenGLVBOManager",
    "backend",
    "check_opengl_error",
    "context",
    "get_max_texture_size",
    "get_max_viewport_dims",
    "get_opengl_extensions",
    "get_opengl_version",
    "has_opengl_extension",
    "ibo",
    "instancing",
    "log_opengl_info",
    "pipeline",
    "program",
    "shader",
    "state",
    "textures",
    "ubo",
    "utils",
    "vao",
    "vbo",
]
