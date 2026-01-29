"""OpenGL ctypes bindings for Windows.

Provides ctypes bindings for OpenGL functions needed for GUI rendering.
"""

from __future__ import annotations

import ctypes
from ctypes import (
    POINTER,
    c_char_p,
    c_double,
    c_float,
    c_int,
    c_uint,
    c_void_p,
)
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    # Public callable type used by lazy loaders
    from collections.abc import Callable, Sequence

    from ornata.api.exports.definitions import FilterMode, WrapMode
    GLFunc = Callable[..., Any]

# Windows handle aliases
HDC = c_void_p
HGLRC = c_void_p

# Try to load DLLs (Windows only)
try:
    opengl32 = ctypes.windll.opengl32
except AttributeError:  # non-Windows or not available
    opengl32 = None

try:
    gdi32 = ctypes.windll.gdi32
except AttributeError:
    gdi32 = None


def _load_gl_function(name: str, restype: Any, argtypes: Sequence[Any]) -> GLFunc:
    """Resolve a GL function either from opengl32 exports or via wglGetProcAddress.

    This uses permissive typing (Any) intentionally to interop cleanly with ctypes.
    """
    if opengl32 is None:
        raise RuntimeError("OpenGL library not available")
    # Ensure wglGetProcAddress has proper signature for later use.
    try:
        _wgl_get_proc_address = opengl32.wglGetProcAddress
        _wgl_get_proc_address.argtypes = [c_char_p]
        _wgl_get_proc_address.restype = c_void_p
    except Exception:
        _wgl_get_proc_address = None

    # First try core export from opengl32 (e.g., OpenGL 1.1 entry points)
    try:
        func = getattr(opengl32, name)
        # Bind argument and return types
        func.argtypes = list(argtypes)
        func.restype = restype
        return func
    except AttributeError:
        # Fall back to extension/late-bound entry via wglGetProcAddress
        if _wgl_get_proc_address is None:
            raise AttributeError(f"OpenGL function {name} not found (no wglGetProcAddress)") from None
        address = _wgl_get_proc_address(name.encode("utf-8"))
        if not address:
            raise AttributeError(f"OpenGL function {name} not found") from None
        cfunctype = ctypes.WINFUNCTYPE(restype, *argtypes)
        func = cfunctype(address)
        return func


def _deferred_gl_function(name: str, restype: Any, argtypes: Sequence[Any]) -> GLFunc:
    """Create a lazily-bound GL function loader.

    The first call resolves the address and replaces the closure-local with the bound callable.
    """
    func: GLFunc | None = None

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        nonlocal func
        if func is None:
            func = _load_gl_function(name, restype, argtypes)
        return func(*args, **kwargs)

    return wrapper


def GLuintArray(values: Sequence[int]) -> Any:
    """Create a ctypes unsigned-int array for index data.

    This mirrors :func:`glfloatArray` and is used by higher-level GPU helpers
    to pass index buffers into OpenGL calls.
    """
    arr_t = c_uint * len(values)
    return arr_t(*[int(v) for v in values])


# --- Common GL/WGL constants (subset) ---

# Clear masks
GL_COLOR_BUFFER_BIT = 0x00004000
GL_DEPTH_BUFFER_BIT = 0x00000100
GL_STENCIL_BUFFER_BIT = 0x00000400

# Texture targets & formats
GL_TEXTURE_2D = 0x0DE1
GL_TEXTURE_CUBE_MAP = 0x8513
GL_TEXTURE_CUBE_MAP_POSITIVE_X = 0x8515
GL_TEXTURE_CUBE_MAP_NEGATIVE_X = 0x8516
GL_TEXTURE_CUBE_MAP_POSITIVE_Y = 0x8517
GL_TEXTURE_CUBE_MAP_NEGATIVE_Y = 0x8518
GL_TEXTURE_CUBE_MAP_POSITIVE_Z = 0x8519
GL_TEXTURE_CUBE_MAP_NEGATIVE_Z = 0x851A

GL_RGBA = 0x1908
GL_RGB = 0x1907
GL_DEPTH_COMPONENT = 0x1902
GL_STENCIL_INDEX = 0x1901

GL_RGB8 = 0x8051
GL_RGBA8 = 0x8058
GL_RGB16F = 0x881B
GL_RGB32F = 0x8815
GL_RGBA16F = 0x881A
GL_RGBA32F = 0x8814
GL_DEPTH_COMPONENT24 = 0x81A6
GL_DEPTH_COMPONENT32F = 0x8CAC
GL_STENCIL_INDEX8 = 0x8D48

# Data types
GL_UNSIGNED_BYTE = 0x1401
GL_UNSIGNED_SHORT = 0x1403
GL_UNSIGNED_INT = 0x1405
GL_FLOAT = 0x1406
GL_HALF_FLOAT = 0x140B

# Texture parameters
GL_TEXTURE_MAG_FILTER = 0x2800
GL_TEXTURE_MIN_FILTER = 0x2801
GL_TEXTURE_WRAP_S = 0x2802
GL_TEXTURE_WRAP_T = 0x2803
GL_TEXTURE_WRAP_R = 0x8072

GL_TEXTURE_LOD_BIAS = 0x84FD
GL_TEXTURE_MIN_LOD = 0x813A
GL_TEXTURE_MAX_LOD = 0x813B

# Wrapping modes
GL_CLAMP_TO_EDGE = 0x812F
GL_CLAMP_TO_BORDER = 0x812D
GL_MIRRORED_REPEAT = 0x8370
GL_REPEAT = 0x2901

# Filtering modes
GL_NEAREST = 0x2600
GL_LINEAR = 0x2601
GL_NEAREST_MIPMAP_NEAREST = 0x2700
GL_LINEAR_MIPMAP_NEAREST = 0x2701
GL_NEAREST_MIPMAP_LINEAR = 0x2702
GL_LINEAR_MIPMAP_LINEAR = 0x2703

# Texture units
GL_TEXTURE0 = 0x84C0

# Buffers
GL_ARRAY_BUFFER = 0x8892
GL_ELEMENT_ARRAY_BUFFER = 0x8893
GL_STATIC_DRAW = 0x88E4
GL_DYNAMIC_DRAW = 0x88E8
GL_STREAM_DRAW = 0x88E0

# Uniform buffers
GL_UNIFORM_BUFFER = 0x8A11

# Primitive types
GL_TRIANGLES = 0x0004
GL_TRIANGLE_STRIP = 0x0005
GL_QUADS = 0x0007  # legacy, still present in 1.1

# Fixed-function pipeline
GL_MODELVIEW = 0x1700
GL_PROJECTION = 0x1701

# Blending / depth
GL_BLEND = 0x0BE2
GL_SRC_ALPHA = 0x0302
GL_ONE_MINUS_SRC_ALPHA = 0x0303
GL_DEPTH_TEST = 0x0B71

# Extensions (anisotropy)
GL_TEXTURE_MAX_ANISOTROPY_EXT = 0x84FE
GL_MAX_TEXTURE_MAX_ANISOTROPY_EXT = 0x84FF

# Boolean constants
GL_FALSE = 0
GL_TRUE = 1

# Error codes
GL_NO_ERROR                      = 0
GL_INVALID_ENUM                  = 0x0500
GL_INVALID_VALUE                 = 0x0501
GL_INVALID_OPERATION             = 0x0502
GL_STACK_OVERFLOW                = 0x0503
GL_STACK_UNDERFLOW               = 0x0504
GL_OUT_OF_MEMORY                 = 0x0505
GL_INVALID_FRAMEBUFFER_OPERATION = 0x0506

# Query constants
GL_VENDOR     = 0x1F00
GL_RENDERER   = 0x1F01
GL_VERSION    = 0x1F02
GL_EXTENSIONS = 0x1F03
GL_MAX_TEXTURE_SIZE = 0x0D33
GL_MAX_VIEWPORT_DIMS = 0x0D3A

GL_COMPILE_STATUS = 0x8B81
GL_LINK_STATUS = 0x8B82
GL_VERTEX_SHADER = 0x8B31
GL_FRAGMENT_SHADER = 0x8B30

# --- Bindings ---

if opengl32:
    # WGL context management (opengl32)
    wglCreateContext: Callable[[HDC], HGLRC] = opengl32.wglCreateContext
    wglCreateContext.argtypes = [HDC]
    wglCreateContext.restype = HGLRC

    wglMakeCurrent: Callable[[HDC, HGLRC], c_int] = opengl32.wglMakeCurrent
    wglMakeCurrent.argtypes = [HDC, HGLRC]
    wglMakeCurrent.restype = c_int

    wglDeleteContext: Callable[[HGLRC], c_int] = opengl32.wglDeleteContext
    wglDeleteContext.argtypes = [HGLRC]
    wglDeleteContext.restype = c_int

    # Optional helpers
    try:
        wglGetCurrentContext: Callable[[], HGLRC] = opengl32.wglGetCurrentContext
        wglGetCurrentContext.argtypes = []
        wglGetCurrentContext.restype = HGLRC
    except AttributeError:
        pass

    try:
        wglGetCurrentDC: Callable[[], HDC] = opengl32.wglGetCurrentDC
        wglGetCurrentDC.argtypes = []
        wglGetCurrentDC.restype = HDC
    except AttributeError:
        pass

    # SwapBuffers is exported by gdi32 (not opengl32)
    if gdi32:
        wglSwapBuffers: Callable[[HDC], c_int] = gdi32.SwapBuffers
        wglSwapBuffers.argtypes = [HDC]
        wglSwapBuffers.restype = c_int

    # --- Core GL 1.1 (and common modern) functions ---

    # Buffer & viewport operations
    glClear = _deferred_gl_function("glClear", None, [c_uint])
    glClearColor = _deferred_gl_function("glClearColor", None, [c_float, c_float, c_float, c_float])
    glViewport = _deferred_gl_function("glViewport", None, [c_int, c_int, c_int, c_int])

    # Texture operations
    glGenTextures = _deferred_gl_function("glGenTextures", None, [c_int, POINTER(c_uint)])
    glDeleteTextures = _deferred_gl_function("glDeleteTextures", None, [c_int, POINTER(c_uint)])
    glBindTexture = _deferred_gl_function("glBindTexture", None, [c_int, c_uint])
    glTexImage2D = _deferred_gl_function(
        "glTexImage2D", None, [c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_void_p]
    )
    glTexSubImage2D = _deferred_gl_function(
        "glTexSubImage2D", None, [c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_void_p]
    )
    glTexParameteri = _deferred_gl_function("glTexParameteri", None, [c_int, c_int, c_int])
    glTexParameterf = _deferred_gl_function("glTexParameterf", None, [c_int, c_int, c_float])
    # Back-compat alias for misspelled request:
    glTexParamaterf = glTexParameterf

    # Buffer objects
    glGenBuffers = _deferred_gl_function("glGenBuffers", None, [c_int, POINTER(c_uint)])
    glDeleteBuffers = _deferred_gl_function("glDeleteBuffers", None, [c_int, POINTER(c_uint)])
    glBindBuffer = _deferred_gl_function("glBindBuffer", None, [c_int, c_uint])
    glBufferData = _deferred_gl_function("glBufferData", None, [c_int, ctypes.c_size_t, c_void_p, c_int])
    glBufferSubData = _deferred_gl_function("glBufferSubData", None, [c_int, ctypes.c_size_t, ctypes.c_size_t, c_void_p])

    # UBO/SSBO binding (missing feature)
    glBindBufferBase = _deferred_gl_function("glBindBufferBase", None, [c_uint, c_uint, c_uint])

    # Shaders
    glCreateShader = _deferred_gl_function("glCreateShader", c_uint, [c_int])
    glDeleteShader = _deferred_gl_function("glDeleteShader", None, [c_uint])
    glShaderSource = _deferred_gl_function("glShaderSource", None, [c_uint, c_int, POINTER(c_char_p), POINTER(c_int)])
    glCompileShader = _deferred_gl_function("glCompileShader", None, [c_uint])
    glGetShaderiv = _deferred_gl_function("glGetShaderiv", None, [c_uint, c_int, POINTER(c_int)])
    # Keep argument order compatible with existing call sites (shader, maxLen, buffer, lengthPtr)
    glGetShaderInfoLog = _deferred_gl_function("glGetShaderInfoLog", None, [c_uint, c_int, c_void_p, POINTER(c_int)])

    # Program
    glCreateProgram = _deferred_gl_function("glCreateProgram", c_uint, [])
    glDeleteProgram = _deferred_gl_function("glDeleteProgram", None, [c_uint])
    glAttachShader = _deferred_gl_function("glAttachShader", None, [c_uint, c_uint])
    glLinkProgram = _deferred_gl_function("glLinkProgram", None, [c_uint])
    glUseProgram = _deferred_gl_function("glUseProgram", None, [c_uint])
    glGetProgramiv = _deferred_gl_function("glGetProgramiv", None, [c_uint, c_int, POINTER(c_int)])
    # Keep argument order compatible with existing call sites (program, maxLen, buffer, lengthPtr)
    glGetProgramInfoLog = _deferred_gl_function("glGetProgramInfoLog", None, [c_uint, c_int, c_void_p, POINTER(c_int)])

    # Uniforms
    glGetUniformLocation = _deferred_gl_function("glGetUniformLocation", c_int, [c_uint, c_char_p])
    glUniform1f = _deferred_gl_function("glUniform1f", None, [c_int, c_float])
    glUniform2f = _deferred_gl_function("glUniform2f", None, [c_int, c_float, c_float])
    glUniform3f = _deferred_gl_function("glUniform3f", None, [c_int, c_float, c_float, c_float])
    glUniform4f = _deferred_gl_function("glUniform4f", None, [c_int, c_float, c_float, c_float, c_float])
    glUniformMatrix4fv = _deferred_gl_function("glUniformMatrix4fv", None, [c_int, c_int, c_int, POINTER(c_float)])

    # Texture unit & mipmap helpers (missing features)
    glActiveTexture = _deferred_gl_function("glActiveTexture", None, [c_uint])
    glGenerateMipmap = _deferred_gl_function("glGenerateMipmap", None, [c_uint])

    # Drawing
    glDrawArrays = _deferred_gl_function("glDrawArrays", None, [c_int, c_int, c_int])
    glDrawElements = _deferred_gl_function("glDrawElements", None, [c_int, c_int, c_int, c_void_p])

    # Vertex attributes
    glEnableVertexAttribArray = _deferred_gl_function("glEnableVertexAttribArray", None, [c_uint])
    glDisableVertexAttribArray = _deferred_gl_function("glDisableVertexAttribArray", None, [c_uint])
    glVertexAttribPointer = _deferred_gl_function("glVertexAttribPointer", None, [c_uint, c_int, c_int, c_int, c_int, c_void_p])

    # State
    glEnable = _deferred_gl_function("glEnable", None, [c_int])
    glDisable = _deferred_gl_function("glDisable", None, [c_int])
    glBlendFunc = _deferred_gl_function("glBlendFunc", None, [c_int, c_int])

    # --- Fixed-function (legacy, but still widely used for simple paths on Windows 1.1) ---
    glBegin = _deferred_gl_function("glBegin", None, [c_uint])
    glEnd = _deferred_gl_function("glEnd", None, [])
    glColor4f = _deferred_gl_function("glColor4f", None, [c_float, c_float, c_float, c_float])
    glVertex2f = _deferred_gl_function("glVertex2f", None, [c_float, c_float])
    glTexCoord2f = _deferred_gl_function("glTexCoord2f", None, [c_float, c_float])
    glRasterPos2f = _deferred_gl_function("glRasterPos2f", None, [c_float, c_float])
    glPushAttrib = _deferred_gl_function("glPushAttrib", None, [c_uint])
    glPopAttrib = _deferred_gl_function("glPopAttrib", None, [])
    glListBase = _deferred_gl_function("glListBase", None, [c_uint])
    glCallLists = _deferred_gl_function("glCallLists", None, [c_int, c_uint, c_void_p])

    glMatrixMode = _deferred_gl_function("glMatrixMode", None, [c_uint])
    glLoadIdentity = _deferred_gl_function("glLoadIdentity", None, [])
    # OpenGL spec uses GLdouble for glOrtho
    glOrtho = _deferred_gl_function("glOrtho", None, [c_double, c_double, c_double, c_double, c_double, c_double])

    # --- Vertex Array Objects (VAO) ---
    glGenVertexArrays = _deferred_gl_function("glGenVertexArrays", None, [c_int, POINTER(c_uint)])
    glDeleteVertexArrays = _deferred_gl_function("glDeleteVertexArrays", None, [c_int, POINTER(c_uint)])
    glBindVertexArray = _deferred_gl_function("glBindVertexArray", None, [c_uint])

    glVertexAttribDivisor = _deferred_gl_function(
        "glVertexAttribDivisor",
        None,
        [c_uint, c_uint]
    )

    glDetachShader = _deferred_gl_function("glDetachShader", None, [c_uint, c_uint])
    glDrawArraysInstanced = _deferred_gl_function("glDrawArraysInstanced", None, [c_int, c_int, c_int, c_int])
    glDrawElementsInstanced = _deferred_gl_function(
        "glDrawElementsInstanced",
        None,
        [c_int, c_int, c_int, c_void_p, c_int],
    )
    glGenSamplers = _deferred_gl_function("glGenSamplers", None, [c_int, POINTER(c_uint)])
    glDeleteSamplers = _deferred_gl_function("glDeleteSamplers", None, [c_int, POINTER(c_uint)])
    glBindSampler = _deferred_gl_function("glBindSampler", None, [c_uint, c_uint])
    glSamplerParameteri = _deferred_gl_function("glSamplerParameteri", None, [c_uint, c_uint, c_int])
    glSamplerParameterf = _deferred_gl_function("glSamplerParameterf", None, [c_uint, c_uint, c_float])

    # --- Error handling ---
    glGetError = _deferred_gl_function("glGetError", c_uint, [])

    # --- Queries ---
    glGetString = _deferred_gl_function("glGetString", c_char_p, [c_uint])
    glGetIntegerv = _deferred_gl_function("glGetIntegerv", None, [c_uint, POINTER(c_int)])


else:
    # Fallbacks that raise at call-time on unsupported systems
    def _opengl_not_available(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("OpenGL not available on this system")

    # WGL
    wglCreateContext = _opengl_not_available
    wglMakeCurrent = _opengl_not_available
    wglDeleteContext = _opengl_not_available
    wglSwapBuffers = _opengl_not_available

    # Core
    glClear = _opengl_not_available
    glClearColor = _opengl_not_available
    glViewport = _opengl_not_available

    glGenTextures = _opengl_not_available
    glDeleteTextures = _opengl_not_available
    glBindTexture = _opengl_not_available
    glTexImage2D = _opengl_not_available
    glTexSubImage2D = _opengl_not_available
    glTexParameteri = _opengl_not_available
    glTexParameterf = _opengl_not_available
    glTexParamaterf = glTexParameterf

    glGenBuffers = _opengl_not_available
    glDeleteBuffers = _opengl_not_available
    glBindBuffer = _opengl_not_available
    glBufferData = _opengl_not_available
    glBufferSubData = _opengl_not_available
    glBindBufferBase = _opengl_not_available

    glCreateShader = _opengl_not_available
    glDeleteShader = _opengl_not_available
    glShaderSource = _opengl_not_available
    glCompileShader = _opengl_not_available
    glGetShaderiv = _opengl_not_available
    glGetShaderInfoLog = _opengl_not_available

    glCreateProgram = _opengl_not_available
    glDeleteProgram = _opengl_not_available
    glAttachShader = _opengl_not_available
    glLinkProgram = _opengl_not_available
    glUseProgram = _opengl_not_available
    glGetProgramiv = _opengl_not_available
    glGetProgramInfoLog = _opengl_not_available

    glGetUniformLocation = _opengl_not_available
    glUniform1f = _opengl_not_available
    glUniform2f = _opengl_not_available
    glUniform3f = _opengl_not_available
    glUniform4f = _opengl_not_available
    glUniformMatrix4fv = _opengl_not_available

    glActiveTexture = _opengl_not_available
    glGenerateMipmap = _opengl_not_available

    glDrawArrays = _opengl_not_available
    glDrawElements = _opengl_not_available

    glEnableVertexAttribArray = _opengl_not_available
    glDisableVertexAttribArray = _opengl_not_available
    glVertexAttribPointer = _opengl_not_available

    glEnable = _opengl_not_available
    glDisable = _opengl_not_available
    glBlendFunc = _opengl_not_available

    # Fixed-function
    glBegin = _opengl_not_available
    glEnd = _opengl_not_available
    glColor4f = _opengl_not_available
    glVertex2f = _opengl_not_available
    glTexCoord2f = _opengl_not_available
    glRasterPos2f = _opengl_not_available
    glPushAttrib = _opengl_not_available
    glPopAttrib = _opengl_not_available
    glListBase = _opengl_not_available
    glCallLists = _opengl_not_available

    glMatrixMode = _opengl_not_available
    glLoadIdentity = _opengl_not_available
    glOrtho = _opengl_not_available


def is_available() -> bool:
    """Check if OpenGL is available on this system."""
    return opengl32 is not None


def _gl_filter(mode: FilterMode | int) -> int:
    from ornata.api.exports.definitions import FilterMode

    mapping = {
        FilterMode.NEAREST: GL_NEAREST,
        FilterMode.LINEAR: GL_LINEAR,
        FilterMode.NEAREST_MIPMAP_NEAREST: GL_NEAREST_MIPMAP_NEAREST,
        FilterMode.LINEAR_MIPMAP_NEAREST: GL_LINEAR_MIPMAP_NEAREST,
        FilterMode.NEAREST_MIPMAP_LINEAR: GL_NEAREST_MIPMAP_LINEAR,
        FilterMode.LINEAR_MIPMAP_LINEAR: GL_LINEAR_MIPMAP_LINEAR,
    }
    return mapping.get(mode, GL_LINEAR)


def _gl_wrap(mode: WrapMode | int) -> int:
    from ornata.api.exports.definitions import WrapMode

    mapping = {
        WrapMode.CLAMP_TO_EDGE: GL_CLAMP_TO_EDGE,
        WrapMode.CLAMP_TO_BORDER: GL_CLAMP_TO_BORDER,
        WrapMode.REPEAT: GL_REPEAT,
        WrapMode.MIRRORED_REPEAT: GL_MIRRORED_REPEAT,
    }
    return mapping.get(mode, GL_CLAMP_TO_EDGE)


# Convenience helper requested: build a c_float array from a Python sequence.
def glfloatArray(values: Sequence[float]) -> Any:
    """Create a ctypes float array suitable for passing to GL calls."""
    arr_t = c_float * len(values)
    return arr_t(*[float(v) for v in values])
