"""Auto-generated lazy exports for the interop subsystem."""

from __future__ import annotations

from importlib import import_module

from ornata.api._warnings import setup_internal_warnings

setup_internal_warnings()

_EXPORT_TARGETS: dict[str, str] = {
    "CONSOLE_SCREEN_BUFFER_INFO": "ornata.interop.ctypes_compilation.windows.kernel32:CONSOLE_SCREEN_BUFFER_INFO",
    "BindingGroup": "ornata.interop.ctypes_compilation.registry:BindingGroup",
    "CFunctionPointer": "ornata.interop.ctypes_compilation.windows.user32:CFunctionPointer",
    "COMInterface": "ornata.interop.ctypes_compilation.windows.com:COMInterface",
    "COMPointer": "ornata.interop.ctypes_compilation.windows.com:COMPointer",
    "CreateDXGIFactory": "ornata.interop.ctypes_compilation.windows.dxgi:CreateDXGIFactory",
    "D3D11CreateDevice": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11CreateDevice",
    "D3D11_BLEND_DESC": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_BLEND_DESC",
    "D3D11_BUFFER_DESC": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_BUFFER_DESC",
    "D3D11_DEPTH_STENCILOP_DESC": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_DEPTH_STENCILOP_DESC",
    "D3D11_DEPTH_STENCIL_DESC": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_DEPTH_STENCIL_DESC",
    "D3D11_INPUT_ELEMENT_DESC": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_INPUT_ELEMENT_DESC",
    "D3D11_QUERY_DESC": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_QUERY_DESC",
    "D3D11_RASTERIZER_DESC": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_RASTERIZER_DESC",
    "D3D11_RENDER_TARGET_BLEND_DESC": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_RENDER_TARGET_BLEND_DESC",
    "D3D11_RENDER_TARGET_VIEW_DESC": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_RENDER_TARGET_VIEW_DESC",
    "D3D11_SAMPLER_DESC": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_SAMPLER_DESC",
    "D3D11_SHADER_RESOURCE_VIEW_DESC": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_SHADER_RESOURCE_VIEW_DESC",
    "D3D11_SUBRESOURCE_DATA": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_SUBRESOURCE_DATA",
    "D3D11_TEX2D_RTV": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_TEX2D_RTV",
    "D3D11_TEX2D_SRV": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_TEX2D_SRV",
    "D3D11_TEXTURE2D_DESC": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_TEXTURE2D_DESC",
    "D3D11_VIEWPORT": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_VIEWPORT",
    "D3DCompile": "ornata.interop.ctypes_compilation.windows.d3dcompile:D3DCompile",
    "D3D_DRIVER_TYPE": "ornata.interop.ctypes_compilation.windows.d3d11:D3D_DRIVER_TYPE",
    "D3D_FEATURE_LEVEL": "ornata.interop.ctypes_compilation.windows.d3d11:D3D_FEATURE_LEVEL",
    "DXGI_FORMAT": "ornata.interop.ctypes_compilation.windows.dxgi:DXGI_FORMAT",
    "DXGI_MODE_DESC": "ornata.interop.ctypes_compilation.windows.dxgi:DXGI_MODE_DESC",
    "DXGI_RATIONAL": "ornata.interop.ctypes_compilation.windows.dxgi:DXGI_RATIONAL",
    "DXGI_SAMPLE_DESC": "ornata.interop.ctypes_compilation.windows.dxgi:DXGI_SAMPLE_DESC",
    "DXGI_SWAP_CHAIN_DESC": "ornata.interop.ctypes_compilation.windows.dxgi:DXGI_SWAP_CHAIN_DESC",
    "GUID": "ornata.interop.ctypes_compilation.windows.foundation:GUID",
    "HWND": "ornata.interop.ctypes_compilation.windows.foundation:HWND",
    "ID3D11BlendState": "ornata.interop.ctypes_compilation.windows.d3d11:ID3D11BlendState",
    "ID3D11Buffer": "ornata.interop.ctypes_compilation.windows.d3d11:ID3D11Buffer",
    "ID3D11ComputeShader": "ornata.interop.ctypes_compilation.windows.d3d11:ID3D11ComputeShader",
    "ID3D11DepthStencilState": "ornata.interop.ctypes_compilation.windows.d3d11:ID3D11DepthStencilState",
    "ID3D11Device": "ornata.interop.ctypes_compilation.windows.d3d11:ID3D11Device",
    "ID3D11DeviceContext": "ornata.interop.ctypes_compilation.windows.d3d11:ID3D11DeviceContext",
    "ID3D11DomainShader": "ornata.interop.ctypes_compilation.windows.d3d11:ID3D11DomainShader",
    "ID3D11GeometryShader": "ornata.interop.ctypes_compilation.windows.d3d11:ID3D11GeometryShader",
    "ID3D11HullShader": "ornata.interop.ctypes_compilation.windows.d3d11:ID3D11HullShader",
    "ID3D11InputLayout": "ornata.interop.ctypes_compilation.windows.d3d11:ID3D11InputLayout",
    "ID3D11PixelShader": "ornata.interop.ctypes_compilation.windows.d3d11:ID3D11PixelShader",
    "ID3D11Query": "ornata.interop.ctypes_compilation.windows.d3d11:ID3D11Query",
    "ID3D11RasterizerState": "ornata.interop.ctypes_compilation.windows.d3d11:ID3D11RasterizerState",
    "ID3D11RenderTargetView": "ornata.interop.ctypes_compilation.windows.d3d11:ID3D11RenderTargetView",
    "ID3D11SamplerState": "ornata.interop.ctypes_compilation.windows.d3d11:ID3D11SamplerState",
    "ID3D11ShaderResourceView": "ornata.interop.ctypes_compilation.windows.d3d11:ID3D11ShaderResourceView",
    "ID3D11Texture2D": "ornata.interop.ctypes_compilation.windows.d3d11:ID3D11Texture2D",
    "ID3D11VertexShader": "ornata.interop.ctypes_compilation.windows.d3d11:ID3D11VertexShader",
    "ID3DBlob": "ornata.interop.ctypes_compilation.windows.d3dcompile:ID3DBlob",
    "IDXGIFactory": "ornata.interop.ctypes_compilation.windows.dxgi:IDXGIFactory",
    "IDXGISwapChain": "ornata.interop.ctypes_compilation.windows.dxgi:IDXGISwapChain",
    "IUnknown": "ornata.interop.ctypes_compilation.windows.com:IUnknown",
    "IUnknownVTable": "ornata.interop.ctypes_compilation.windows.com:IUnknownVTable",
    "LUID": "ornata.interop.ctypes_compilation.windows.foundation:LUID",
    "PAINTSTRUCT": "ornata.interop.ctypes_compilation.windows.foundation:PAINTSTRUCT",
    "POINT": "ornata.interop.ctypes_compilation.windows.foundation:POINT",
    "RECT": "ornata.interop.ctypes_compilation.windows.foundation:RECT",
    "SIZE": "ornata.interop.ctypes_compilation.windows.foundation:SIZE",
    "WindowsLibraryError": "ornata.interop.ctypes_compilation.windows.foundation:WindowsLibraryError",
    "_D3D11CreateDeviceProto": "ornata.interop.ctypes_compilation.windows.d3d11:_D3D11CreateDeviceProto",
    "_as_cvoidp": "ornata.interop.ctypes_compilation.windows.d3d11:_as_cvoidp",
    "_as_void_ptr": "ornata.interop.ctypes_compilation.windows.dxgi:_as_void_ptr",
    "_proc": "ornata.interop.ctypes_compilation.windows.user32:_proc",
    "_ptr_val": "ornata.interop.ctypes_compilation.windows.d3d11:_ptr_val",
    "blob_to_bytes": "ornata.interop.ctypes_compilation.windows.d3dcompile:blob_to_bytes",
    "check_hresult": "ornata.interop.ctypes_compilation.windows.foundation:check_hresult",
    "com": "ornata.interop.ctypes_compilation.windows:com",
    "ctypes_compilation": "ornata.interop:ctypes_compilation",
    "d3d11": "ornata.interop.ctypes_compilation.windows:d3d11",
    "d3dcompile": "ornata.interop.ctypes_compilation.windows:d3dcompile",
    "declare_interface": "ornata.interop.ctypes_compilation.windows.com:declare_interface",
    "dxgi": "ornata.interop.ctypes_compilation.windows:dxgi",
    "ensure_windows": "ornata.interop.ctypes_compilation.windows.foundation:ensure_windows",
    "foundation": "ornata.interop.ctypes_compilation.windows:foundation",
    "gdi32": "ornata.interop.ctypes_compilation.windows:gdi32",
    "get_platform_bindings": "ornata.interop.ctypes_compilation.registry:get_platform_bindings",
    "kernel32": "ornata.interop.ctypes_compilation.windows:kernel32",
    "load_library": "ornata.interop.ctypes_compilation.windows.foundation:load_library",
    "ole32": "ornata.interop.ctypes_compilation.windows:ole32",
    "user32": "ornata.interop.ctypes_compilation.windows:user32",
    "windows": "ornata.interop.ctypes_compilation:windows",
    "D3D11_USAGE_DEFAULT": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_USAGE_DEFAULT",
    "D3D11_SRV_DIMENSION_TEXTURE2D": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_SRV_DIMENSION_TEXTURE2D",
    "D3D11_BIND_SHADER_RESOURCE": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_BIND_SHADER_RESOURCE",
    "D3D11_BIND_CONSTANT_BUFFER": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_BIND_CONSTANT_BUFFER",
    "D3D11_QUERY_EVENT": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_QUERY_EVENT",
    "DXGI_MODE_SCALING_UNSPECIFIED": "ornata.interop.ctypes_compilation.windows.dxgi:DXGI_MODE_SCALING_UNSPECIFIED",
    "DXGI_MODE_SCANLINE_ORDER_UNSPECIFIED": "ornata.interop.ctypes_compilation.windows.dxgi:DXGI_MODE_SCANLINE_ORDER_UNSPECIFIED",
    "DXGI_SWAP_EFFECT_DISCARD": "ornata.interop.ctypes_compilation.windows.dxgi:DXGI_SWAP_EFFECT_DISCARD",
    "DXGI_USAGE_RENDER_TARGET_OUTPUT": "ornata.interop.ctypes_compilation.windows.dxgi:DXGI_USAGE_RENDER_TARGET_OUTPUT",
    "D3D11_COMPARISON_ALWAYS": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_COMPARISON_ALWAYS",
    "D3D11_FILTER_MIN_MAG_MIP_LINEAR": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_FILTER_MIN_MAG_MIP_LINEAR",
    "D3D11_TEXTURE_ADDRESS_CLAMP": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_TEXTURE_ADDRESS_CLAMP",
    "D3D11_BLEND_ONE": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_BLEND_ONE",
    "D3D11_BLEND_OP_ADD": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_BLEND_OP_ADD",
    "D3D11_BLEND_ZERO": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_BLEND_ZERO",
    "D3D11_COLOR_WRITE_ENABLE_ALL": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_COLOR_WRITE_ENABLE_ALL",
    "D3D11_COMPARISON_LESS": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_COMPARISON_LESS",
    "D3D11_CULL_BACK": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_CULL_BACK",
    "D3D11_DEPTH_WRITE_MASK_ALL": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_DEPTH_WRITE_MASK_ALL",
    "D3D11_FILL_SOLID": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_FILL_SOLID",
    "D3D11_INPUT_PER_VERTEX_DATA": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_INPUT_PER_VERTEX_DATA",
    "DXGI_FORMAT_R32G32_FLOAT": "ornata.interop.ctypes_compilation.windows.dxgi:DXGI_FORMAT_R32G32_FLOAT",
    "DXGI_FORMAT_R32G32B32_FLOAT": "ornata.interop.ctypes_compilation.windows.dxgi:DXGI_FORMAT_R32G32B32_FLOAT",
    "D3D11_CREATE_DEVICE_BGRA_SUPPORT": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_CREATE_DEVICE_BGRA_SUPPORT",
    "D3D11_SDK_VERSION": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_SDK_VERSION",
    "D3D11_BIND_RENDER_TARGET": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_BIND_RENDER_TARGET",
    "D3D11_RTV_DIMENSION_TEXTURE2D": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_RTV_DIMENSION_TEXTURE2D",
    "D3D_PRIMITIVE_TOPOLOGY_TRIANGLELIST": "ornata.interop.ctypes_compilation.windows.d3d11:D3D_PRIMITIVE_TOPOLOGY_TRIANGLELIST",
    "DXGI_FORMAT_R32_UINT": "ornata.interop.ctypes_compilation.windows.dxgi:DXGI_FORMAT_R32_UINT",
    "D3D11_BIND_INDEX_BUFFER": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_BIND_INDEX_BUFFER",
    "D3D11_BIND_VERTEX_BUFFER": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_BIND_VERTEX_BUFFER",
    "DXGI_SWAP_EFFECT_FLIP_DISCARD": "ornata.interop.ctypes_compilation.windows.dxgi:DXGI_SWAP_EFFECT_FLIP_DISCARD",
    "DXGI_SWAP_EFFECT_FLIP_SEQUENTIAL": "ornata.interop.ctypes_compilation.windows.dxgi:DXGI_SWAP_EFFECT_FLIP_SEQUENTIAL",
    "DXGI_SWAP_EFFECT_SEQUENTIAL": "ornata.interop.ctypes_compilation.windows.dxgi:DXGI_SWAP_EFFECT_SEQUENTIAL",
    "DXGI_USAGE_SHADER_INPUT": "ornata.interop.ctypes_compilation.windows.dxgi:DXGI_USAGE_SHADER_INPUT",
    "D3D11CreateDeviceAndSwapChain": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11CreateDeviceAndSwapChain",
    "IID_ID3D11Texture2D": "ornata.interop.ctypes_compilation.windows.d3d11:IID_ID3D11Texture2D",
    "GL_ARRAY_BUFFER": "ornata.interop.ctypes_compilation.windows.opengl:GL_ARRAY_BUFFER",
    "GL_BLEND": "ornata.interop.ctypes_compilation.windows.opengl:GL_BLEND",
    "GL_COLOR_BUFFER_BIT": "ornata.interop.ctypes_compilation.windows.opengl:GL_COLOR_BUFFER_BIT",
    "GL_COMPILE_STATUS": "ornata.interop.ctypes_compilation.windows.opengl:GL_COMPILE_STATUS",
    "GL_DEPTH_BUFFER_BIT": "ornata.interop.ctypes_compilation.windows.opengl:GL_DEPTH_BUFFER_BIT",
    "GL_DYNAMIC_DRAW": "ornata.interop.ctypes_compilation.windows.opengl:GL_DYNAMIC_DRAW",
    "GL_ELEMENT_ARRAY_BUFFER": "ornata.interop.ctypes_compilation.windows.opengl:GL_ELEMENT_ARRAY_BUFFER",
    "GL_FLOAT": "ornata.interop.ctypes_compilation.windows.opengl:GL_FLOAT",
    "GL_FRAGMENT_SHADER": "ornata.interop.ctypes_compilation.windows.opengl:GL_FRAGMENT_SHADER",
    "GL_LINK_STATUS": "ornata.interop.ctypes_compilation.windows.opengl:GL_LINK_STATUS",
    "GL_ONE_MINUS_SRC_ALPHA": "ornata.interop.ctypes_compilation.windows.opengl:GL_ONE_MINUS_SRC_ALPHA",
    "GL_QUADS": "ornata.interop.ctypes_compilation.windows.opengl:GL_QUADS",
    "GL_RGBA": "ornata.interop.ctypes_compilation.windows.opengl:GL_RGBA",
    "GL_SRC_ALPHA": "ornata.interop.ctypes_compilation.windows.opengl:GL_SRC_ALPHA",
    "GL_STATIC_DRAW": "ornata.interop.ctypes_compilation.windows.opengl:GL_STATIC_DRAW",
    "GL_STENCIL_BUFFER_BIT": "ornata.interop.ctypes_compilation.windows.opengl:GL_STENCIL_BUFFER_BIT",
    "GL_TEXTURE_2D": "ornata.interop.ctypes_compilation.windows.opengl:GL_TEXTURE_2D",
    "GL_TRIANGLE_STRIP": "ornata.interop.ctypes_compilation.windows.opengl:GL_TRIANGLE_STRIP",
    "GL_TRIANGLES": "ornata.interop.ctypes_compilation.windows.opengl:GL_TRIANGLES",
    "GL_UNSIGNED_BYTE": "ornata.interop.ctypes_compilation.windows.opengl:GL_UNSIGNED_BYTE",
    "GL_VERTEX_SHADER": "ornata.interop.ctypes_compilation.windows.opengl:GL_VERTEX_SHADER",
    "glAttachShader": "ornata.interop.ctypes_compilation.windows.opengl:glAttachShader",
    "glBindBuffer": "ornata.interop.ctypes_compilation.windows.opengl:glBindBuffer",
    "glBindTexture": "ornata.interop.ctypes_compilation.windows.opengl:glBindTexture",
    "glBlendFunc": "ornata.interop.ctypes_compilation.windows.opengl:glBlendFunc",
    "glBufferData": "ornata.interop.ctypes_compilation.windows.opengl:glBufferData",
    "glBufferSubData": "ornata.interop.ctypes_compilation.windows.opengl:glBufferSubData",
    "glClear": "ornata.interop.ctypes_compilation.windows.opengl:glClear",
    "glClearColor": "ornata.interop.ctypes_compilation.windows.opengl:glClearColor",
    "glCompileShader": "ornata.interop.ctypes_compilation.windows.opengl:glCompileShader",
    "glCreateProgram": "ornata.interop.ctypes_compilation.windows.opengl:glCreateProgram",
    "glCreateShader": "ornata.interop.ctypes_compilation.windows.opengl:glCreateShader",
    "glDeleteBuffers": "ornata.interop.ctypes_compilation.windows.opengl:glDeleteBuffers",
    "glDeleteProgram": "ornata.interop.ctypes_compilation.windows.opengl:glDeleteProgram",
    "glDeleteShader": "ornata.interop.ctypes_compilation.windows.opengl:glDeleteShader",
    "glDeleteTextures": "ornata.interop.ctypes_compilation.windows.opengl:glDeleteTextures",
    "glDisable": "ornata.interop.ctypes_compilation.windows.opengl:glDisable",
    "glDisableVertexAttribArray": "ornata.interop.ctypes_compilation.windows.opengl:glDisableVertexAttribArray",
    "glDrawArrays": "ornata.interop.ctypes_compilation.windows.opengl:glDrawArrays",
    "glDrawElements": "ornata.interop.ctypes_compilation.windows.opengl:glDrawElements",
    "glEnable": "ornata.interop.ctypes_compilation.windows.opengl:glEnable",
    "glEnableVertexAttribArray": "ornata.interop.ctypes_compilation.windows.opengl:glEnableVertexAttribArray",
    "glGenBuffers": "ornata.interop.ctypes_compilation.windows.opengl:glGenBuffers",
    "glGenTextures": "ornata.interop.ctypes_compilation.windows.opengl:glGenTextures",
    "glGetProgramInfoLog": "ornata.interop.ctypes_compilation.windows.opengl:glGetProgramInfoLog",
    "glGetProgramiv": "ornata.interop.ctypes_compilation.windows.opengl:glGetProgramiv",
    "glGetShaderInfoLog": "ornata.interop.ctypes_compilation.windows.opengl:glGetShaderInfoLog",
    "glGetShaderiv": "ornata.interop.ctypes_compilation.windows.opengl:glGetShaderiv",
    "glGetUniformLocation": "ornata.interop.ctypes_compilation.windows.opengl:glGetUniformLocation",
    "glLinkProgram": "ornata.interop.ctypes_compilation.windows.opengl:glLinkProgram",
    "glShaderSource": "ornata.interop.ctypes_compilation.windows.opengl:glShaderSource",
    "glTexImage2D": "ornata.interop.ctypes_compilation.windows.opengl:glTexImage2D",
    "glTexParameteri": "ornata.interop.ctypes_compilation.windows.opengl:glTexParameteri",
    "glUniform1f": "ornata.interop.ctypes_compilation.windows.opengl:glUniform1f",
    "glUniform2f": "ornata.interop.ctypes_compilation.windows.opengl:glUniform2f",
    "glUniform3f": "ornata.interop.ctypes_compilation.windows.opengl:glUniform3f",
    "glUniform4f": "ornata.interop.ctypes_compilation.windows.opengl:glUniform4f",
    "glUniformMatrix4fv": "ornata.interop.ctypes_compilation.windows.opengl:glUniformMatrix4fv",
    "glUseProgram": "ornata.interop.ctypes_compilation.windows.opengl:glUseProgram",
    "glVertexAttribPointer": "ornata.interop.ctypes_compilation.windows.opengl:glVertexAttribPointer",
    "glViewport": "ornata.interop.ctypes_compilation.windows.opengl:glViewport",
    "glDetachShader": "ornata.interop.ctypes_compilation.windows.opengl:glDetachShader",
    "glDrawArraysInstanced": "ornata.interop.ctypes_compilation.windows.opengl:glDrawArraysInstanced",
    "glDrawElementsInstanced": "ornata.interop.ctypes_compilation.windows.opengl:glDrawElementsInstanced",
    "is_available": "ornata.interop.ctypes_compilation.windows.opengl:is_available",
    "GL_RGB": "ornata.interop.ctypes_compilation.windows.opengl:GL_RGB",
    "GL_UNSIGNED_SHORT": "ornata.interop.ctypes_compilation.windows.opengl:GL_UNSIGNED_SHORT",
    "GL_TEXTURE_MAG_FILTER": "ornata.interop.ctypes_compilation.windows.opengl:GL_TEXTURE_MAG_FILTER",
    "GL_TEXTURE_MIN_FILTER": "ornata.interop.ctypes_compilation.windows.opengl:GL_TEXTURE_MIN_FILTER",
    "GL_LINEAR": "ornata.interop.ctypes_compilation.windows.opengl:GL_LINEAR",
    "GL_MODELVIEW": "ornata.interop.ctypes_compilation.windows.opengl:GL_MODELVIEW",
    "GL_PROJECTION": "ornata.interop.ctypes_compilation.windows.opengl:GL_PROJECTION",
    "glBegin": "ornata.interop.ctypes_compilation.windows.opengl:glBegin",
    "glEnd": "ornata.interop.ctypes_compilation.windows.opengl:glEnd",
    "glColor4f": "ornata.interop.ctypes_compilation.windows.opengl:glColor4f",
    "glVertex2f": "ornata.interop.ctypes_compilation.windows.opengl:glVertex2f",
    "glTexCoord2f": "ornata.interop.ctypes_compilation.windows.opengl:glTexCoord2f",
    "glRasterPos2f": "ornata.interop.ctypes_compilation.windows.opengl:glRasterPos2f",
    "glPushAttrib": "ornata.interop.ctypes_compilation.windows.opengl:glPushAttrib",
    "glPopAttrib": "ornata.interop.ctypes_compilation.windows.opengl:glPopAttrib",
    "glListBase": "ornata.interop.ctypes_compilation.windows.opengl:glListBase",
    "glCallLists": "ornata.interop.ctypes_compilation.windows.opengl:glCallLists",
    "glMatrixMode": "ornata.interop.ctypes_compilation.windows.opengl:glMatrixMode",
    "glLoadIdentity": "ornata.interop.ctypes_compilation.windows.opengl:glLoadIdentity",
    "glOrtho": "ornata.interop.ctypes_compilation.windows.opengl:glOrtho",
    "glTexSubImage2D": "ornata.interop.ctypes_compilation.windows.opengl:glTexSubImage2D",
    "wglSwapBuffers": "ornata.interop.ctypes_compilation.windows.opengl:wglSwapBuffers",
    "wglCreateContext": "ornata.interop.ctypes_compilation.windows.opengl:wglCreateContext",
    "wglMakeCurrent": "ornata.interop.ctypes_compilation.windows.opengl:wglMakeCurrent",
    "wglDeleteContext": "ornata.interop.ctypes_compilation.windows.opengl:wglDeleteContext",
    "wglGetCurrentContext": "ornata.interop.ctypes_compilation.windows.opengl:wglGetCurrentContext",
    "wglGetCurrentDC": "ornata.interop.ctypes_compilation.windows.opengl:wglGetCurrentDC",
    "GL_DEPTH_TEST": "ornata.interop.ctypes_compilation.windows.opengl:GL_DEPTH_TEST",
    "DeleteObject": "ornata.interop.ctypes_compilation.windows.gdi32:DeleteObject",
    "SelectObject": "ornata.interop.ctypes_compilation.windows.gdi32:SelectObject",
    "ctwt": "ornata.interop.ctypes_compilation.windows.gdi32:ctwt",
    "PIXELFORMATDESCRIPTOR": "ornata.interop.ctypes_compilation.windows.gdi32:PIXELFORMATDESCRIPTOR",
    "ChoosePixelFormat": "ornata.interop.ctypes_compilation.windows.gdi32:ChoosePixelFormat",
    "GetDC": "ornata.interop.ctypes_compilation.windows.user32:GetDC",
    "ReleaseDC": "ornata.interop.ctypes_compilation.windows.user32:ReleaseDC",
    "SetPixelFormat": "ornata.interop.ctypes_compilation.windows.gdi32:SetPixelFormat",
    "SwapBuffers": "ornata.interop.ctypes_compilation.windows.gdi32:SwapBuffers",
    "CreateFontW": "ornata.interop.ctypes_compilation.windows.gdi32:CreateFontW",
    "GetModuleHandleW": "ornata.interop.ctypes_compilation.windows.kernel32:GetModuleHandleW",
    "GL_UNIFORM_BUFFER": "ornata.interop.ctypes_compilation.windows.opengl:GL_UNIFORM_BUFFER",
    "glfloatArray": "ornata.interop.ctypes_compilation.windows.opengl:glfloatArray",
    "glBindBufferBase": "ornata.interop.ctypes_compilation.windows.opengl:glBindBufferBase",
    "GL_STREAM_DRAW": "ornata.interop.ctypes_compilation.windows.opengl:GL_STREAM_DRAW",
    "GL_TEXTURE_MAX_ANISOTROPY_EXT": "ornata.interop.ctypes_compilation.windows.opengl:GL_TEXTURE_MAX_ANISOTROPY_EXT",
    "GL_TEXTURE_WRAP_S": "ornata.interop.ctypes_compilation.windows.opengl:GL_TEXTURE_WRAP_S",
    "GL_TEXTURE_WRAP_T": "ornata.interop.ctypes_compilation.windows.opengl:GL_TEXTURE_WRAP_T",
    "glTexParameterf": "ornata.interop.ctypes_compilation.windows.opengl:glTexParameterf",
    "GL_CLAMP_TO_BORDER": "ornata.interop.ctypes_compilation.windows.opengl:GL_CLAMP_TO_BORDER",
    "GL_CLAMP_TO_EDGE": "ornata.interop.ctypes_compilation.windows.opengl:GL_CLAMP_TO_EDGE",
    "GL_MIRRORED_REPEAT": "ornata.interop.ctypes_compilation.windows.opengl:GL_MIRRORED_REPEAT",
    "GL_REPEAT": "ornata.interop.ctypes_compilation.windows.opengl:GL_REPEAT",
    "GL_LINEAR_MIPMAP_LINEAR": "ornata.interop.ctypes_compilation.windows.opengl:GL_LINEAR_MIPMAP_LINEAR",
    "GL_LINEAR_MIPMAP_NEAREST": "ornata.interop.ctypes_compilation.windows.opengl:GL_LINEAR_MIPMAP_NEAREST",
    "GL_NEAREST": "ornata.interop.ctypes_compilation.windows.opengl:GL_NEAREST",
    "GL_NEAREST_MIPMAP_LINEAR": "ornata.interop.ctypes_compilation.windows.opengl:GL_NEAREST_MIPMAP_LINEAR",
    "GL_NEAREST_MIPMAP_NEAREST": "ornata.interop.ctypes_compilation.windows.opengl:GL_NEAREST_MIPMAP_NEAREST",
    "GL_DEPTH_COMPONENT": "ornata.interop.ctypes_compilation.windows.opengl:GL_DEPTH_COMPONENT",
    "GL_DEPTH_COMPONENT24": "ornata.interop.ctypes_compilation.windows.opengl:GL_DEPTH_COMPONENT24",
    "GL_DEPTH_COMPONENT32F": "ornata.interop.ctypes_compilation.windows.opengl:GL_DEPTH_COMPONENT32F",
    "GL_HALF_FLOAT": "ornata.interop.ctypes_compilation.windows.opengl:GL_HALF_FLOAT",
    "GL_RGB8": "ornata.interop.ctypes_compilation.windows.opengl:GL_RGB8",
    "GL_RGB16F": "ornata.interop.ctypes_compilation.windows.opengl:GL_RGB16F",
    "GL_RGB32F": "ornata.interop.ctypes_compilation.windows.opengl:GL_RGB32F",
    "GL_RGBA8": "ornata.interop.ctypes_compilation.windows.opengl:GL_RGBA8",
    "GL_RGBA16F": "ornata.interop.ctypes_compilation.windows.opengl:GL_RGBA16F",
    "GL_RGBA32F": "ornata.interop.ctypes_compilation.windows.opengl:GL_RGBA32F",
    "GL_STENCIL_INDEX": "ornata.interop.ctypes_compilation.windows.opengl:GL_STENCIL_INDEX",
    "GL_STENCIL_INDEX8": "ornata.interop.ctypes_compilation.windows.opengl:GL_STENCIL_INDEX8",
    "GL_UNSIGNED_INT": "ornata.interop.ctypes_compilation.windows.opengl:GL_UNSIGNED_INT",
    "GL_TEXTURE0": "ornata.interop.ctypes_compilation.windows.opengl:GL_TEXTURE0",
    "glActiveTexture": "ornata.interop.ctypes_compilation.windows.opengl:glActiveTexture",
    "glGenerateMipmap": "ornata.interop.ctypes_compilation.windows.opengl:glGenerateMipmap",
    "GL_TEXTURE_CUBE_MAP": "ornata.interop.ctypes_compilation.windows.opengl:GL_TEXTURE_CUBE_MAP",
    "GL_TEXTURE_WRAP_R": "ornata.interop.ctypes_compilation.windows.opengl:GL_TEXTURE_WRAP_R",
    "glTexParamaterf": "ornata.interop.ctypes_compilation.windows.opengl:glTexParamaterf",
    "GL_TEXTURE_CUBE_MAP_NEGATIVE_X": "ornata.interop.ctypes_compilation.windows.opengl:GL_TEXTURE_CUBE_MAP_NEGATIVE_X",
    "GL_TEXTURE_CUBE_MAP_NEGATIVE_Y": "ornata.interop.ctypes_compilation.windows.opengl:GL_TEXTURE_CUBE_MAP_NEGATIVE_Y",
    "GL_TEXTURE_CUBE_MAP_NEGATIVE_Z": "ornata.interop.ctypes_compilation.windows.opengl:GL_TEXTURE_CUBE_MAP_NEGATIVE_Z",
    "GL_TEXTURE_CUBE_MAP_POSITIVE_X": "ornata.interop.ctypes_compilation.windows.opengl:GL_TEXTURE_CUBE_MAP_POSITIVE_X",
    "GL_TEXTURE_CUBE_MAP_POSITIVE_Y": "ornata.interop.ctypes_compilation.windows.opengl:GL_TEXTURE_CUBE_MAP_POSITIVE_Y",
    "GL_TEXTURE_CUBE_MAP_POSITIVE_Z": "ornata.interop.ctypes_compilation.windows.opengl:GL_TEXTURE_CUBE_MAP_POSITIVE_Z",
    "GetConsoleScreenBufferInfo": "ornata.interop.ctypes_compilation.windows.kernel32:GetConsoleScreenBufferInfo",
    "GetStdHandle": "ornata.interop.ctypes_compilation.windows.kernel32:GetStdHandle",
    "STD_ERROR_HANDLE": "ornata.interop.ctypes_compilation.windows.kernel32:STD_ERROR_HANDLE",
    "STD_INPUT_HANDLE": "ornata.interop.ctypes_compilation.windows.kernel32:STD_INPUT_HANDLE",
    "STD_OUTPUT_HANDLE": "ornata.interop.ctypes_compilation.windows.kernel32:STD_OUTPUT_HANDLE",
    "DXGI_FORMAT_R16_UINT": "ornata.interop.ctypes_compilation.windows.dxgi:DXGI_FORMAT_R16_UINT",
    "DXGI_FORMAT_R32G32B32A32_FLOAT": "ornata.interop.ctypes_compilation.windows.dxgi:DXGI_FORMAT_R32G32B32A32_FLOAT",
    "D3D11_INPUT_PER_INSTANCE_DATA": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_INPUT_PER_INSTANCE_DATA",
    "D3D11_USAGE_DYNAMIC": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_USAGE_DYNAMIC",
    "ID3D11DeviceContext1": "ornata.interop.ctypes_compilation.windows.d3d11_devicecontext1:ID3D11DeviceContext1",
    "PSSetConstantBuffers1": "ornata.interop.ctypes_compilation.windows.d3d11_devicecontext1:PSSetConstantBuffers1",
    "VSSetConstantBuffers1": "ornata.interop.ctypes_compilation.windows.d3d11_devicecontext1:VSSetConstantBuffers1",
    "D3D11_MAP_WRITE_DISCARD": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_MAP_WRITE_DISCARD",
    "IASetIndexBuffer": "ornata.interop.ctypes_compilation.windows.d3d11:IASetIndexBuffer",
    "D3D11_MAPPED_SUBRESOURCE": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_MAPPED_SUBRESOURCE",
    "D3D11_CPU_ACCESS_WRITE": "ornata.interop.ctypes_compilation.windows.d3d11:D3D11_CPU_ACCESS_WRITE",
    "IASetInputLayout": "ornata.interop.ctypes_compilation.windows.d3d11:IASetInputLayout",
    "DXGI_FORMAT_R8G8B8A8_UNORM": "ornata.interop.ctypes_compilation.windows.dxgi:DXGI_FORMAT_R8G8B8A8_UNORM",
    "FLOAT": "ornata.interop.ctypes_compilation.windows.d3d11:FLOAT",
    "PostQuitMessage": "ornata.interop.ctypes_compilation.windows.user32:PostQuitMessage",
    "GLuintArray": "ornata.interop.ctypes_compilation.windows.opengl:GLuintArray",
    "glGenVertexArrays": "ornata.interop.ctypes_compilation.windows.opengl:glGenVertexArrays",
    "glBindVertexArray": "ornata.interop.ctypes_compilation.windows.opengl:glBindVertexArray",
    "glVertexAttribDivisor": "ornata.interop.ctypes_compilation.windows.opengl:glVertexAttribDivisor",
    "GL_FALSE": "ornata.interop.ctypes_compilation.windows.opengl:GL_FALSE",
    "GL_TRUE": "ornata.interop.ctypes_compilation.windows.opengl:GL_TRUE",
    "GL_INVALID_ENUM": "ornata.interop.ctypes_compilation.windows.opengl:GL_INVALID_ENUM",
    "GL_INVALID_FRAMEBUFFER_OPERATION": "ornata.interop.ctypes_compilation.windows.opengl:GL_INVALID_FRAMEBUFFER_OPERATION",
    "GL_INVALID_OPERATION": "ornata.interop.ctypes_compilation.windows.opengl:GL_INVALID_OPERATION",
    "GL_INVALID_VALUE": "ornata.interop.ctypes_compilation.windows.opengl:GL_INVALID_VALUE",
    "GL_NO_ERROR": "ornata.interop.ctypes_compilation.windows.opengl:GL_NO_ERROR",
    "GL_OUT_OF_MEMORY": "ornata.interop.ctypes_compilation.windows.opengl:GL_OUT_OF_MEMORY",
    "GL_STACK_OVERFLOW": "ornata.interop.ctypes_compilation.windows.opengl:GL_STACK_OVERFLOW",
    "GL_STACK_UNDERFLOW": "ornata.interop.ctypes_compilation.windows.opengl:GL_STACK_UNDERFLOW",
    "glGetError": "ornata.interop.ctypes_compilation.windows.opengl:glGetError",
    "GL_VERSION": "ornata.interop.ctypes_compilation.windows.opengl:GL_VERSION",
    "GL_EXTENSIONS": "ornata.interop.ctypes_compilation.windows.opengl:GL_EXTENSIONS",
    "glGetString": "ornata.interop.ctypes_compilation.windows.opengl:glGetString",
    "GL_MAX_TEXTURE_SIZE": "ornata.interop.ctypes_compilation.windows.opengl:GL_MAX_TEXTURE_SIZE",
    "glGetIntegerv": "ornata.interop.ctypes_compilation.windows.opengl:glGetIntegerv",
    "glDeleteVertexArrays": "ornata.interop.ctypes_compilation.windows.opengl:glDeleteVertexArrays",
    "GL_MAX_VIEWPORT_DIMS": "ornata.interop.ctypes_compilation.windows.opengl:GL_MAX_VIEWPORT_DIMS",
    "GL_RENDERER": "ornata.interop.ctypes_compilation.windows.opengl:GL_RENDERER",
    "GL_VENDOR": "ornata.interop.ctypes_compilation.windows.opengl:GL_VENDOR",
    "GL_TEXTURE_LOD_BIAS": "ornata.interop.ctypes_compilation.windows.opengl:GL_TEXTURE_LOD_BIAS",
    "GL_TEXTURE_MAX_LOD": "ornata.interop.ctypes_compilation.windows.opengl:GL_TEXTURE_MAX_LOD",
    "GL_TEXTURE_MIN_LOD": "ornata.interop.ctypes_compilation.windows.opengl:GL_TEXTURE_MIN_LOD",
    "_gl_filter": "ornata.interop.ctypes_compilation.windows.opengl:_gl_filter",
    "_gl_wrap": "ornata.interop.ctypes_compilation.windows.opengl:_gl_wrap",
    "glGenSamplers": "ornata.interop.ctypes_compilation.windows.opengl:glGenSamplers",
    "glSamplerParameterf": "ornata.interop.ctypes_compilation.windows.opengl:glSamplerParameterf",
    "glSamplerParameteri": "ornata.interop.ctypes_compilation.windows.opengl:glSamplerParameteri",
    "glBindSampler": "ornata.interop.ctypes_compilation.windows.opengl:glBindSampler",
}

_RESOLVED_EXPORTS: dict[str, object] = {}

__all__ = ["__getattr__"]

def _load_target(name: str) -> object:
    """Load and cache ``name`` for this subsystem.

    Parameters
    ----------
    name : str
        Export name to resolve.

    Returns
    -------
    object
        Resolved attribute from the owning module.

    Raises
    ------
    AttributeError
        If ``name`` is unknown to this subsystem.
    """

    target = _EXPORT_TARGETS.get(name)
    if target is None:
        raise AttributeError(
            "module 'ornata.api.exports.interop' has no attribute {name!r}"
        )
    module_name, _, attr_name = target.partition(':')
    module = import_module(module_name)
    value = getattr(module, attr_name)
    _RESOLVED_EXPORTS[name] = value
    globals()[name] = value
    return value

def __getattr__(name: str) -> object:
    """Resolve an export attribute on first access.

    Parameters
    ----------
    name : str
        Export name requested from this module.

    Returns
    -------
    object
        Resolved export value.

    Raises
    ------
    AttributeError
        If ``name`` is not part of this subsystem.
    """

    if name in _RESOLVED_EXPORTS:
        return _RESOLVED_EXPORTS[name]
    return _load_target(name)

def __dir__() -> list[str]:
    """Return the sorted list of exportable names.

    Returns
    -------
    list[str]
        Sorted names available via this module.
    """

    names = ['__getattr__']
    names.extend(_EXPORT_TARGETS)
    return sorted(names)
