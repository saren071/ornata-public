"""Type stubs for the interop subsystem exports."""

from __future__ import annotations

from ornata.interop import ctypes_compilation as ctypes_compilation
from ornata.interop.ctypes_compilation import windows as windows
from ornata.interop.ctypes_compilation.registry import BindingGroup as BindingGroup
from ornata.interop.ctypes_compilation.registry import get_platform_bindings as get_platform_bindings
from ornata.interop.ctypes_compilation.windows import com as com
from ornata.interop.ctypes_compilation.windows import d3d11 as d3d11
from ornata.interop.ctypes_compilation.windows import d3dcompile as d3dcompile
from ornata.interop.ctypes_compilation.windows import dxgi as dxgi
from ornata.interop.ctypes_compilation.windows import foundation as foundation
from ornata.interop.ctypes_compilation.windows import gdi32 as gdi32
from ornata.interop.ctypes_compilation.windows import kernel32 as kernel32
from ornata.interop.ctypes_compilation.windows import ole32 as ole32
from ornata.interop.ctypes_compilation.windows import user32 as user32
from ornata.interop.ctypes_compilation.windows.com import COMInterface as COMInterface
from ornata.interop.ctypes_compilation.windows.com import COMPointer as COMPointer
from ornata.interop.ctypes_compilation.windows.com import IUnknown as IUnknown
from ornata.interop.ctypes_compilation.windows.com import IUnknownVTable as IUnknownVTable
from ornata.interop.ctypes_compilation.windows.com import declare_interface as declare_interface
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D11_BIND_CONSTANT_BUFFER as D3D11_BIND_CONSTANT_BUFFER
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D11_BIND_INDEX_BUFFER as D3D11_BIND_INDEX_BUFFER
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D11_BIND_RENDER_TARGET as D3D11_BIND_RENDER_TARGET
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D11_BIND_SHADER_RESOURCE as D3D11_BIND_SHADER_RESOURCE
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D11_BIND_VERTEX_BUFFER as D3D11_BIND_VERTEX_BUFFER
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D11_BLEND_DESC as D3D11_BLEND_DESC
from ornata.interop.ctypes_compilation.windows.d3d11 import (
    D3D11_BLEND_ONE,
    D3D11_BLEND_OP_ADD,
    D3D11_BLEND_ZERO,
    D3D11_COLOR_WRITE_ENABLE_ALL,
    D3D11_COMPARISON_ALWAYS,
    D3D11_COMPARISON_LESS,
    D3D11_CREATE_DEVICE_BGRA_SUPPORT,
    D3D11_CULL_BACK,
    D3D11_DEPTH_WRITE_MASK_ALL,
    D3D11_FILL_SOLID,
    D3D11_FILTER_MIN_MAG_MIP_LINEAR,
    D3D11_INPUT_PER_VERTEX_DATA,
    D3D11_MAPPED_SUBRESOURCE,
    D3D11_SDK_VERSION,
    D3D11_TEXTURE_ADDRESS_CLAMP,
    FLOAT,
)
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D11_BUFFER_DESC as D3D11_BUFFER_DESC
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D11_CPU_ACCESS_WRITE as D3D11_CPU_ACCESS_WRITE
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D11_DEPTH_STENCIL_DESC as D3D11_DEPTH_STENCIL_DESC
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D11_DEPTH_STENCILOP_DESC as D3D11_DEPTH_STENCILOP_DESC
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D11_INPUT_ELEMENT_DESC as D3D11_INPUT_ELEMENT_DESC
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D11_INPUT_PER_INSTANCE_DATA as D3D11_INPUT_PER_INSTANCE_DATA
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D11_MAP_WRITE_DISCARD as D3D11_MAP_WRITE_DISCARD
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D11_QUERY_DESC as D3D11_QUERY_DESC
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D11_QUERY_EVENT as D3D11_QUERY_EVENT
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D11_RASTERIZER_DESC as D3D11_RASTERIZER_DESC
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D11_RENDER_TARGET_BLEND_DESC as D3D11_RENDER_TARGET_BLEND_DESC
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D11_RENDER_TARGET_VIEW_DESC as D3D11_RENDER_TARGET_VIEW_DESC
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D11_RTV_DIMENSION_TEXTURE2D as D3D11_RTV_DIMENSION_TEXTURE2D
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D11_SAMPLER_DESC as D3D11_SAMPLER_DESC
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D11_SHADER_RESOURCE_VIEW_DESC as D3D11_SHADER_RESOURCE_VIEW_DESC
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D11_SRV_DIMENSION_TEXTURE2D as D3D11_SRV_DIMENSION_TEXTURE2D
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D11_SUBRESOURCE_DATA as D3D11_SUBRESOURCE_DATA
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D11_TEX2D_RTV as D3D11_TEX2D_RTV
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D11_TEX2D_SRV as D3D11_TEX2D_SRV
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D11_TEXTURE2D_DESC as D3D11_TEXTURE2D_DESC
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D11_USAGE_DEFAULT as D3D11_USAGE_DEFAULT
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D11_USAGE_DYNAMIC as D3D11_USAGE_DYNAMIC
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D11_VIEWPORT as D3D11_VIEWPORT
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D_DRIVER_TYPE as D3D_DRIVER_TYPE
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D_FEATURE_LEVEL as D3D_FEATURE_LEVEL
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D_PRIMITIVE_TOPOLOGY_TRIANGLELIST as D3D_PRIMITIVE_TOPOLOGY_TRIANGLELIST
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D11CreateDevice as D3D11CreateDevice
from ornata.interop.ctypes_compilation.windows.d3d11 import D3D11CreateDeviceAndSwapChain as D3D11CreateDeviceAndSwapChain
from ornata.interop.ctypes_compilation.windows.d3d11 import IASetIndexBuffer as IASetIndexBuffer
from ornata.interop.ctypes_compilation.windows.d3d11 import IASetInputLayout as IASetInputLayout
from ornata.interop.ctypes_compilation.windows.d3d11 import ID3D11BlendState as ID3D11BlendState
from ornata.interop.ctypes_compilation.windows.d3d11 import ID3D11Buffer as ID3D11Buffer
from ornata.interop.ctypes_compilation.windows.d3d11 import ID3D11ComputeShader as ID3D11ComputeShader
from ornata.interop.ctypes_compilation.windows.d3d11 import ID3D11DepthStencilState as ID3D11DepthStencilState
from ornata.interop.ctypes_compilation.windows.d3d11 import ID3D11Device as ID3D11Device
from ornata.interop.ctypes_compilation.windows.d3d11 import ID3D11DeviceContext as ID3D11DeviceContext
from ornata.interop.ctypes_compilation.windows.d3d11 import ID3D11DomainShader as ID3D11DomainShader
from ornata.interop.ctypes_compilation.windows.d3d11 import ID3D11GeometryShader as ID3D11GeometryShader
from ornata.interop.ctypes_compilation.windows.d3d11 import ID3D11HullShader as ID3D11HullShader
from ornata.interop.ctypes_compilation.windows.d3d11 import ID3D11InputLayout as ID3D11InputLayout
from ornata.interop.ctypes_compilation.windows.d3d11 import ID3D11PixelShader as ID3D11PixelShader
from ornata.interop.ctypes_compilation.windows.d3d11 import ID3D11Query as ID3D11Query
from ornata.interop.ctypes_compilation.windows.d3d11 import ID3D11RasterizerState as ID3D11RasterizerState
from ornata.interop.ctypes_compilation.windows.d3d11 import ID3D11RenderTargetView as ID3D11RenderTargetView
from ornata.interop.ctypes_compilation.windows.d3d11 import ID3D11SamplerState as ID3D11SamplerState
from ornata.interop.ctypes_compilation.windows.d3d11 import ID3D11ShaderResourceView as ID3D11ShaderResourceView
from ornata.interop.ctypes_compilation.windows.d3d11 import ID3D11Texture2D as ID3D11Texture2D
from ornata.interop.ctypes_compilation.windows.d3d11 import ID3D11VertexShader as ID3D11VertexShader
from ornata.interop.ctypes_compilation.windows.d3d11 import IID_ID3D11Texture2D as IID_ID3D11Texture2D
from ornata.interop.ctypes_compilation.windows.d3d11 import _as_cvoidp as _as_cvoidp  #type: ignore
from ornata.interop.ctypes_compilation.windows.d3d11 import _D3D11CreateDeviceProto as _D3D11CreateDeviceProto  #type: ignore
from ornata.interop.ctypes_compilation.windows.d3d11 import _ptr_val as _ptr_val  #type: ignore
from ornata.interop.ctypes_compilation.windows.d3d11_devicecontext1 import ID3D11DeviceContext1 as ID3D11DeviceContext1
from ornata.interop.ctypes_compilation.windows.d3d11_devicecontext1 import PSSetConstantBuffers1 as PSSetConstantBuffers1
from ornata.interop.ctypes_compilation.windows.d3d11_devicecontext1 import VSSetConstantBuffers1 as VSSetConstantBuffers1
from ornata.interop.ctypes_compilation.windows.d3dcompile import D3DCompile as D3DCompile
from ornata.interop.ctypes_compilation.windows.d3dcompile import ID3DBlob as ID3DBlob
from ornata.interop.ctypes_compilation.windows.d3dcompile import blob_to_bytes as blob_to_bytes
from ornata.interop.ctypes_compilation.windows.dxgi import DXGI_FORMAT as DXGI_FORMAT
from ornata.interop.ctypes_compilation.windows.dxgi import DXGI_FORMAT_R8G8B8A8_UNORM as DXGI_FORMAT_R8G8B8A8_UNORM
from ornata.interop.ctypes_compilation.windows.dxgi import DXGI_FORMAT_R16_UINT as DXGI_FORMAT_R16_UINT
from ornata.interop.ctypes_compilation.windows.dxgi import DXGI_FORMAT_R32_UINT as DXGI_FORMAT_R32_UINT
from ornata.interop.ctypes_compilation.windows.dxgi import DXGI_FORMAT_R32G32_FLOAT as DXGI_FORMAT_R32G32_FLOAT
from ornata.interop.ctypes_compilation.windows.dxgi import DXGI_FORMAT_R32G32B32_FLOAT as DXGI_FORMAT_R32G32B32_FLOAT
from ornata.interop.ctypes_compilation.windows.dxgi import DXGI_FORMAT_R32G32B32A32_FLOAT as DXGI_FORMAT_R32G32B32A32_FLOAT
from ornata.interop.ctypes_compilation.windows.dxgi import DXGI_MODE_DESC as DXGI_MODE_DESC
from ornata.interop.ctypes_compilation.windows.dxgi import DXGI_MODE_SCALING_UNSPECIFIED as DXGI_MODE_SCALING_UNSPECIFIED
from ornata.interop.ctypes_compilation.windows.dxgi import DXGI_MODE_SCANLINE_ORDER_UNSPECIFIED as DXGI_MODE_SCANLINE_ORDER_UNSPECIFIED
from ornata.interop.ctypes_compilation.windows.dxgi import DXGI_RATIONAL as DXGI_RATIONAL
from ornata.interop.ctypes_compilation.windows.dxgi import DXGI_SAMPLE_DESC as DXGI_SAMPLE_DESC
from ornata.interop.ctypes_compilation.windows.dxgi import DXGI_SWAP_CHAIN_DESC as DXGI_SWAP_CHAIN_DESC
from ornata.interop.ctypes_compilation.windows.dxgi import DXGI_SWAP_EFFECT_DISCARD as DXGI_SWAP_EFFECT_DISCARD
from ornata.interop.ctypes_compilation.windows.dxgi import DXGI_SWAP_EFFECT_FLIP_DISCARD as DXGI_SWAP_EFFECT_FLIP_DISCARD
from ornata.interop.ctypes_compilation.windows.dxgi import DXGI_SWAP_EFFECT_FLIP_SEQUENTIAL as DXGI_SWAP_EFFECT_FLIP_SEQUENTIAL
from ornata.interop.ctypes_compilation.windows.dxgi import DXGI_SWAP_EFFECT_SEQUENTIAL as DXGI_SWAP_EFFECT_SEQUENTIAL
from ornata.interop.ctypes_compilation.windows.dxgi import DXGI_USAGE_RENDER_TARGET_OUTPUT as DXGI_USAGE_RENDER_TARGET_OUTPUT
from ornata.interop.ctypes_compilation.windows.dxgi import DXGI_USAGE_SHADER_INPUT as DXGI_USAGE_SHADER_INPUT
from ornata.interop.ctypes_compilation.windows.dxgi import CreateDXGIFactory as CreateDXGIFactory
from ornata.interop.ctypes_compilation.windows.dxgi import IDXGIFactory as IDXGIFactory
from ornata.interop.ctypes_compilation.windows.dxgi import IDXGISwapChain as IDXGISwapChain
from ornata.interop.ctypes_compilation.windows.dxgi import _as_void_ptr as _as_void_ptr  #type: ignore
from ornata.interop.ctypes_compilation.windows.foundation import GUID as GUID
from ornata.interop.ctypes_compilation.windows.foundation import HWND as HWND
from ornata.interop.ctypes_compilation.windows.foundation import LUID as LUID
from ornata.interop.ctypes_compilation.windows.foundation import PAINTSTRUCT as PAINTSTRUCT
from ornata.interop.ctypes_compilation.windows.foundation import POINT as POINT
from ornata.interop.ctypes_compilation.windows.foundation import RECT as RECT
from ornata.interop.ctypes_compilation.windows.foundation import SIZE as SIZE
from ornata.interop.ctypes_compilation.windows.foundation import WindowsLibraryError as WindowsLibraryError
from ornata.interop.ctypes_compilation.windows.foundation import check_hresult as check_hresult
from ornata.interop.ctypes_compilation.windows.foundation import ensure_windows as ensure_windows
from ornata.interop.ctypes_compilation.windows.foundation import load_library as load_library
from ornata.interop.ctypes_compilation.windows.gdi32 import PIXELFORMATDESCRIPTOR as PIXELFORMATDESCRIPTOR
from ornata.interop.ctypes_compilation.windows.gdi32 import ChoosePixelFormat as ChoosePixelFormat
from ornata.interop.ctypes_compilation.windows.gdi32 import CreateFontW as CreateFontW
from ornata.interop.ctypes_compilation.windows.gdi32 import DeleteObject as DeleteObject
from ornata.interop.ctypes_compilation.windows.gdi32 import SelectObject as SelectObject
from ornata.interop.ctypes_compilation.windows.gdi32 import SetPixelFormat as SetPixelFormat
from ornata.interop.ctypes_compilation.windows.gdi32 import SwapBuffers as SwapBuffers
from ornata.interop.ctypes_compilation.windows.gdi32 import ctwt as ctwt
from ornata.interop.ctypes_compilation.windows.kernel32 import GetModuleHandleW as GetModuleHandleW
from ornata.interop.ctypes_compilation.windows.opengl import GL_ARRAY_BUFFER as GL_ARRAY_BUFFER
from ornata.interop.ctypes_compilation.windows.opengl import GL_BLEND as GL_BLEND
from ornata.interop.ctypes_compilation.windows.opengl import GL_CLAMP_TO_BORDER as GL_CLAMP_TO_BORDER
from ornata.interop.ctypes_compilation.windows.opengl import GL_CLAMP_TO_EDGE as GL_CLAMP_TO_EDGE
from ornata.interop.ctypes_compilation.windows.opengl import GL_COLOR_BUFFER_BIT as GL_COLOR_BUFFER_BIT
from ornata.interop.ctypes_compilation.windows.opengl import GL_COMPILE_STATUS as GL_COMPILE_STATUS
from ornata.interop.ctypes_compilation.windows.opengl import GL_DEPTH_BUFFER_BIT as GL_DEPTH_BUFFER_BIT
from ornata.interop.ctypes_compilation.windows.opengl import GL_DEPTH_COMPONENT as GL_DEPTH_COMPONENT
from ornata.interop.ctypes_compilation.windows.opengl import GL_DEPTH_COMPONENT24 as GL_DEPTH_COMPONENT24
from ornata.interop.ctypes_compilation.windows.opengl import GL_DEPTH_COMPONENT32F as GL_DEPTH_COMPONENT32F
from ornata.interop.ctypes_compilation.windows.opengl import GL_DEPTH_TEST as GL_DEPTH_TEST
from ornata.interop.ctypes_compilation.windows.opengl import GL_DYNAMIC_DRAW as GL_DYNAMIC_DRAW
from ornata.interop.ctypes_compilation.windows.opengl import GL_ELEMENT_ARRAY_BUFFER as GL_ELEMENT_ARRAY_BUFFER
from ornata.interop.ctypes_compilation.windows.opengl import GL_EXTENSIONS as GL_EXTENSIONS
from ornata.interop.ctypes_compilation.windows.opengl import GL_FALSE as GL_FALSE
from ornata.interop.ctypes_compilation.windows.opengl import GL_FLOAT as GL_FLOAT
from ornata.interop.ctypes_compilation.windows.opengl import GL_FRAGMENT_SHADER as GL_FRAGMENT_SHADER
from ornata.interop.ctypes_compilation.windows.opengl import GL_HALF_FLOAT as GL_HALF_FLOAT
from ornata.interop.ctypes_compilation.windows.opengl import GL_INVALID_ENUM as GL_INVALID_ENUM
from ornata.interop.ctypes_compilation.windows.opengl import GL_INVALID_FRAMEBUFFER_OPERATION as GL_INVALID_FRAMEBUFFER_OPERATION
from ornata.interop.ctypes_compilation.windows.opengl import GL_INVALID_OPERATION as GL_INVALID_OPERATION
from ornata.interop.ctypes_compilation.windows.opengl import GL_INVALID_VALUE as GL_INVALID_VALUE
from ornata.interop.ctypes_compilation.windows.opengl import GL_LINEAR as GL_LINEAR
from ornata.interop.ctypes_compilation.windows.opengl import GL_LINEAR_MIPMAP_LINEAR as GL_LINEAR_MIPMAP_LINEAR
from ornata.interop.ctypes_compilation.windows.opengl import GL_LINEAR_MIPMAP_NEAREST as GL_LINEAR_MIPMAP_NEAREST
from ornata.interop.ctypes_compilation.windows.opengl import GL_LINK_STATUS as GL_LINK_STATUS
from ornata.interop.ctypes_compilation.windows.opengl import GL_MAX_TEXTURE_SIZE as GL_MAX_TEXTURE_SIZE
from ornata.interop.ctypes_compilation.windows.opengl import GL_MAX_VIEWPORT_DIMS as GL_MAX_VIEWPORT_DIMS
from ornata.interop.ctypes_compilation.windows.opengl import GL_MIRRORED_REPEAT as GL_MIRRORED_REPEAT
from ornata.interop.ctypes_compilation.windows.opengl import GL_MODELVIEW as GL_MODELVIEW
from ornata.interop.ctypes_compilation.windows.opengl import GL_NEAREST as GL_NEAREST
from ornata.interop.ctypes_compilation.windows.opengl import GL_NEAREST_MIPMAP_LINEAR as GL_NEAREST_MIPMAP_LINEAR
from ornata.interop.ctypes_compilation.windows.opengl import GL_NEAREST_MIPMAP_NEAREST as GL_NEAREST_MIPMAP_NEAREST
from ornata.interop.ctypes_compilation.windows.opengl import GL_NO_ERROR as GL_NO_ERROR
from ornata.interop.ctypes_compilation.windows.opengl import GL_ONE_MINUS_SRC_ALPHA as GL_ONE_MINUS_SRC_ALPHA
from ornata.interop.ctypes_compilation.windows.opengl import GL_OUT_OF_MEMORY as GL_OUT_OF_MEMORY
from ornata.interop.ctypes_compilation.windows.opengl import GL_PROJECTION as GL_PROJECTION
from ornata.interop.ctypes_compilation.windows.opengl import GL_QUADS as GL_QUADS
from ornata.interop.ctypes_compilation.windows.opengl import GL_RENDERER as GL_RENDERER
from ornata.interop.ctypes_compilation.windows.opengl import GL_REPEAT as GL_REPEAT
from ornata.interop.ctypes_compilation.windows.opengl import GL_RGB as GL_RGB
from ornata.interop.ctypes_compilation.windows.opengl import GL_RGB8 as GL_RGB8
from ornata.interop.ctypes_compilation.windows.opengl import GL_RGB16F as GL_RGB16F
from ornata.interop.ctypes_compilation.windows.opengl import GL_RGB32F as GL_RGB32F
from ornata.interop.ctypes_compilation.windows.opengl import GL_RGBA as GL_RGBA
from ornata.interop.ctypes_compilation.windows.opengl import GL_RGBA8 as GL_RGBA8
from ornata.interop.ctypes_compilation.windows.opengl import GL_RGBA16F as GL_RGBA16F
from ornata.interop.ctypes_compilation.windows.opengl import GL_RGBA32F as GL_RGBA32F
from ornata.interop.ctypes_compilation.windows.opengl import GL_SRC_ALPHA as GL_SRC_ALPHA
from ornata.interop.ctypes_compilation.windows.opengl import GL_STACK_OVERFLOW as GL_STACK_OVERFLOW
from ornata.interop.ctypes_compilation.windows.opengl import GL_STACK_UNDERFLOW as GL_STACK_UNDERFLOW
from ornata.interop.ctypes_compilation.windows.opengl import GL_STATIC_DRAW as GL_STATIC_DRAW
from ornata.interop.ctypes_compilation.windows.opengl import GL_STENCIL_BUFFER_BIT as GL_STENCIL_BUFFER_BIT
from ornata.interop.ctypes_compilation.windows.opengl import GL_STENCIL_INDEX as GL_STENCIL_INDEX
from ornata.interop.ctypes_compilation.windows.opengl import GL_STENCIL_INDEX8 as GL_STENCIL_INDEX8
from ornata.interop.ctypes_compilation.windows.opengl import GL_STREAM_DRAW as GL_STREAM_DRAW
from ornata.interop.ctypes_compilation.windows.opengl import GL_TEXTURE0 as GL_TEXTURE0
from ornata.interop.ctypes_compilation.windows.opengl import GL_TEXTURE_2D as GL_TEXTURE_2D
from ornata.interop.ctypes_compilation.windows.opengl import GL_TEXTURE_CUBE_MAP as GL_TEXTURE_CUBE_MAP
from ornata.interop.ctypes_compilation.windows.opengl import GL_TEXTURE_CUBE_MAP_NEGATIVE_X as GL_TEXTURE_CUBE_MAP_NEGATIVE_X
from ornata.interop.ctypes_compilation.windows.opengl import GL_TEXTURE_CUBE_MAP_NEGATIVE_Y as GL_TEXTURE_CUBE_MAP_NEGATIVE_Y
from ornata.interop.ctypes_compilation.windows.opengl import GL_TEXTURE_CUBE_MAP_NEGATIVE_Z as GL_TEXTURE_CUBE_MAP_NEGATIVE_Z
from ornata.interop.ctypes_compilation.windows.opengl import GL_TEXTURE_CUBE_MAP_POSITIVE_X as GL_TEXTURE_CUBE_MAP_POSITIVE_X
from ornata.interop.ctypes_compilation.windows.opengl import GL_TEXTURE_CUBE_MAP_POSITIVE_Y as GL_TEXTURE_CUBE_MAP_POSITIVE_Y
from ornata.interop.ctypes_compilation.windows.opengl import GL_TEXTURE_CUBE_MAP_POSITIVE_Z as GL_TEXTURE_CUBE_MAP_POSITIVE_Z
from ornata.interop.ctypes_compilation.windows.opengl import GL_TEXTURE_LOD_BIAS as GL_TEXTURE_LOD_BIAS
from ornata.interop.ctypes_compilation.windows.opengl import GL_TEXTURE_MAG_FILTER as GL_TEXTURE_MAG_FILTER
from ornata.interop.ctypes_compilation.windows.opengl import GL_TEXTURE_MAX_ANISOTROPY_EXT as GL_TEXTURE_MAX_ANISOTROPY_EXT
from ornata.interop.ctypes_compilation.windows.opengl import GL_TEXTURE_MAX_LOD as GL_TEXTURE_MAX_LOD
from ornata.interop.ctypes_compilation.windows.opengl import GL_TEXTURE_MIN_FILTER as GL_TEXTURE_MIN_FILTER
from ornata.interop.ctypes_compilation.windows.opengl import GL_TEXTURE_MIN_LOD as GL_TEXTURE_MIN_LOD
from ornata.interop.ctypes_compilation.windows.opengl import GL_TEXTURE_WRAP_R as GL_TEXTURE_WRAP_R
from ornata.interop.ctypes_compilation.windows.opengl import GL_TEXTURE_WRAP_S as GL_TEXTURE_WRAP_S
from ornata.interop.ctypes_compilation.windows.opengl import GL_TEXTURE_WRAP_T as GL_TEXTURE_WRAP_T
from ornata.interop.ctypes_compilation.windows.opengl import GL_TRIANGLE_STRIP as GL_TRIANGLE_STRIP
from ornata.interop.ctypes_compilation.windows.opengl import GL_TRIANGLES as GL_TRIANGLES
from ornata.interop.ctypes_compilation.windows.opengl import GL_TRUE as GL_TRUE
from ornata.interop.ctypes_compilation.windows.opengl import GL_UNIFORM_BUFFER as GL_UNIFORM_BUFFER
from ornata.interop.ctypes_compilation.windows.opengl import GL_UNSIGNED_BYTE as GL_UNSIGNED_BYTE
from ornata.interop.ctypes_compilation.windows.opengl import GL_UNSIGNED_INT as GL_UNSIGNED_INT
from ornata.interop.ctypes_compilation.windows.opengl import GL_UNSIGNED_SHORT as GL_UNSIGNED_SHORT
from ornata.interop.ctypes_compilation.windows.opengl import GL_VENDOR as GL_VENDOR
from ornata.interop.ctypes_compilation.windows.opengl import GL_VERSION as GL_VERSION
from ornata.interop.ctypes_compilation.windows.opengl import GL_VERTEX_SHADER as GL_VERTEX_SHADER
from ornata.interop.ctypes_compilation.windows.opengl import GLuintArray as GLuintArray
from ornata.interop.ctypes_compilation.windows.opengl import _gl_filter as _gl_filter
from ornata.interop.ctypes_compilation.windows.opengl import _gl_wrap as _gl_wrap
from ornata.interop.ctypes_compilation.windows.opengl import glActiveTexture as glActiveTexture
from ornata.interop.ctypes_compilation.windows.opengl import glAttachShader as glAttachShader
from ornata.interop.ctypes_compilation.windows.opengl import glBegin as glBegin
from ornata.interop.ctypes_compilation.windows.opengl import glBindBuffer as glBindBuffer
from ornata.interop.ctypes_compilation.windows.opengl import glBindBufferBase as glBindBufferBase
from ornata.interop.ctypes_compilation.windows.opengl import glBindSampler as glBindSampler
from ornata.interop.ctypes_compilation.windows.opengl import glBindTexture as glBindTexture
from ornata.interop.ctypes_compilation.windows.opengl import glBindVertexArray as glBindVertexArray
from ornata.interop.ctypes_compilation.windows.opengl import glBlendFunc as glBlendFunc
from ornata.interop.ctypes_compilation.windows.opengl import glBufferData as glBufferData
from ornata.interop.ctypes_compilation.windows.opengl import glBufferSubData as glBufferSubData
from ornata.interop.ctypes_compilation.windows.opengl import glCallLists as glCallLists
from ornata.interop.ctypes_compilation.windows.opengl import glClear as glClear
from ornata.interop.ctypes_compilation.windows.opengl import glClearColor as glClearColor
from ornata.interop.ctypes_compilation.windows.opengl import glColor4f as glColor4f
from ornata.interop.ctypes_compilation.windows.opengl import glCompileShader as glCompileShader
from ornata.interop.ctypes_compilation.windows.opengl import glCreateProgram as glCreateProgram
from ornata.interop.ctypes_compilation.windows.opengl import glCreateShader as glCreateShader
from ornata.interop.ctypes_compilation.windows.opengl import glDeleteBuffers as glDeleteBuffers
from ornata.interop.ctypes_compilation.windows.opengl import glDeleteProgram as glDeleteProgram
from ornata.interop.ctypes_compilation.windows.opengl import glDeleteShader as glDeleteShader
from ornata.interop.ctypes_compilation.windows.opengl import glDeleteTextures as glDeleteTextures
from ornata.interop.ctypes_compilation.windows.opengl import glDeleteVertexArrays as glDeleteVertexArrays
from ornata.interop.ctypes_compilation.windows.opengl import glDetachShader as glDetachShader
from ornata.interop.ctypes_compilation.windows.opengl import glDisable as glDisable
from ornata.interop.ctypes_compilation.windows.opengl import glDisableVertexAttribArray as glDisableVertexAttribArray
from ornata.interop.ctypes_compilation.windows.opengl import glDrawArrays as glDrawArrays
from ornata.interop.ctypes_compilation.windows.opengl import glDrawArraysInstanced as glDrawArraysInstanced
from ornata.interop.ctypes_compilation.windows.opengl import glDrawElements as glDrawElements
from ornata.interop.ctypes_compilation.windows.opengl import glDrawElementsInstanced as glDrawElementsInstanced
from ornata.interop.ctypes_compilation.windows.opengl import glEnable as glEnable
from ornata.interop.ctypes_compilation.windows.opengl import glEnableVertexAttribArray as glEnableVertexAttribArray
from ornata.interop.ctypes_compilation.windows.opengl import glEnd as glEnd
from ornata.interop.ctypes_compilation.windows.opengl import glfloatArray as glfloatArray
from ornata.interop.ctypes_compilation.windows.opengl import glGenBuffers as glGenBuffers
from ornata.interop.ctypes_compilation.windows.opengl import glGenerateMipmap as glGenerateMipmap
from ornata.interop.ctypes_compilation.windows.opengl import glGenSamplers as glGenSamplers
from ornata.interop.ctypes_compilation.windows.opengl import glGenTextures as glGenTextures
from ornata.interop.ctypes_compilation.windows.opengl import glGenVertexArrays as glGenVertexArrays
from ornata.interop.ctypes_compilation.windows.opengl import glGetError as glGetError
from ornata.interop.ctypes_compilation.windows.opengl import glGetIntegerv as glGetIntegerv
from ornata.interop.ctypes_compilation.windows.opengl import glGetProgramInfoLog as glGetProgramInfoLog
from ornata.interop.ctypes_compilation.windows.opengl import glGetProgramiv as glGetProgramiv
from ornata.interop.ctypes_compilation.windows.opengl import glGetShaderInfoLog as glGetShaderInfoLog
from ornata.interop.ctypes_compilation.windows.opengl import glGetShaderiv as glGetShaderiv
from ornata.interop.ctypes_compilation.windows.opengl import glGetString as glGetString
from ornata.interop.ctypes_compilation.windows.opengl import glGetUniformLocation as glGetUniformLocation
from ornata.interop.ctypes_compilation.windows.opengl import glLinkProgram as glLinkProgram
from ornata.interop.ctypes_compilation.windows.opengl import glListBase as glListBase
from ornata.interop.ctypes_compilation.windows.opengl import glLoadIdentity as glLoadIdentity
from ornata.interop.ctypes_compilation.windows.opengl import glMatrixMode as glMatrixMode
from ornata.interop.ctypes_compilation.windows.opengl import glOrtho as glOrtho
from ornata.interop.ctypes_compilation.windows.opengl import glPopAttrib as glPopAttrib
from ornata.interop.ctypes_compilation.windows.opengl import glPushAttrib as glPushAttrib
from ornata.interop.ctypes_compilation.windows.opengl import glRasterPos2f as glRasterPos2f
from ornata.interop.ctypes_compilation.windows.opengl import glSamplerParameterf as glSamplerParameterf
from ornata.interop.ctypes_compilation.windows.opengl import glSamplerParameteri as glSamplerParameteri
from ornata.interop.ctypes_compilation.windows.opengl import glShaderSource as glShaderSource
from ornata.interop.ctypes_compilation.windows.opengl import glTexCoord2f as glTexCoord2f
from ornata.interop.ctypes_compilation.windows.opengl import glTexImage2D as glTexImage2D
from ornata.interop.ctypes_compilation.windows.opengl import glTexParamaterf as glTexParamaterf
from ornata.interop.ctypes_compilation.windows.opengl import glTexParameterf as glTexParameterf
from ornata.interop.ctypes_compilation.windows.opengl import glTexParameteri as glTexParameteri
from ornata.interop.ctypes_compilation.windows.opengl import glTexSubImage2D as glTexSubImage2D
from ornata.interop.ctypes_compilation.windows.opengl import glUniform1f as glUniform1f
from ornata.interop.ctypes_compilation.windows.opengl import glUniform2f as glUniform2f
from ornata.interop.ctypes_compilation.windows.opengl import glUniform3f as glUniform3f
from ornata.interop.ctypes_compilation.windows.opengl import glUniform4f as glUniform4f
from ornata.interop.ctypes_compilation.windows.opengl import glUniformMatrix4fv as glUniformMatrix4fv
from ornata.interop.ctypes_compilation.windows.opengl import glUseProgram as glUseProgram
from ornata.interop.ctypes_compilation.windows.opengl import glVertex2f as glVertex2f
from ornata.interop.ctypes_compilation.windows.opengl import glVertexAttribDivisor as glVertexAttribDivisor
from ornata.interop.ctypes_compilation.windows.opengl import glVertexAttribPointer as glVertexAttribPointer
from ornata.interop.ctypes_compilation.windows.opengl import glViewport as glViewport
from ornata.interop.ctypes_compilation.windows.opengl import is_available as is_available
from ornata.interop.ctypes_compilation.windows.opengl import wglCreateContext as wglCreateContext
from ornata.interop.ctypes_compilation.windows.opengl import wglDeleteContext as wglDeleteContext
from ornata.interop.ctypes_compilation.windows.opengl import wglGetCurrentContext as wglGetCurrentContext
from ornata.interop.ctypes_compilation.windows.opengl import wglGetCurrentDC as wglGetCurrentDC
from ornata.interop.ctypes_compilation.windows.opengl import wglMakeCurrent as wglMakeCurrent
from ornata.interop.ctypes_compilation.windows.opengl import wglSwapBuffers as wglSwapBuffers
from ornata.interop.ctypes_compilation.windows.user32 import CFunctionPointer as CFunctionPointer
from ornata.interop.ctypes_compilation.windows.user32 import GetDC as GetDC
from ornata.interop.ctypes_compilation.windows.user32 import PostQuitMessage as PostQuitMessage
from ornata.interop.ctypes_compilation.windows.user32 import ReleaseDC as ReleaseDC
from ornata.interop.ctypes_compilation.windows.user32 import _proc as _proc  #type: ignore

__all__ = [
    "BindingGroup",
    "CFunctionPointer",
    "COMInterface",
    "COMPointer",
    "CreateDXGIFactory",
    "D3D11CreateDevice",
    "D3D11_BLEND_DESC",
    "D3D11_BUFFER_DESC",
    "D3D11_DEPTH_STENCILOP_DESC",
    "D3D11_DEPTH_STENCIL_DESC",
    "D3D11_INPUT_ELEMENT_DESC",
    "D3D11_QUERY_DESC",
    "D3D11_RASTERIZER_DESC",
    "D3D11_RENDER_TARGET_BLEND_DESC",
    "D3D11_RENDER_TARGET_VIEW_DESC",
    "D3D11_SAMPLER_DESC",
    "D3D11_SHADER_RESOURCE_VIEW_DESC",
    "D3D11_SUBRESOURCE_DATA",
    "D3D11_TEX2D_RTV",
    "D3D11_TEX2D_SRV",
    "D3D11_TEXTURE2D_DESC",
    "D3D11_VIEWPORT",
    "D3DCompile",
    "D3D_DRIVER_TYPE",
    "D3D_FEATURE_LEVEL",
    "DXGI_FORMAT",
    "DXGI_MODE_DESC",
    "DXGI_RATIONAL",
    "DXGI_SAMPLE_DESC",
    "DXGI_SWAP_CHAIN_DESC",
    "GUID",
    "ID3D11BlendState",
    "ID3D11Buffer",
    "ID3D11ComputeShader",
    "ID3D11DepthStencilState",
    "ID3D11Device",
    "ID3D11DeviceContext",
    "ID3D11DomainShader",
    "ID3D11GeometryShader",
    "ID3D11HullShader",
    "ID3D11InputLayout",
    "ID3D11PixelShader",
    "ID3D11Query",
    "ID3D11RasterizerState",
    "ID3D11RenderTargetView",
    "ID3D11SamplerState",
    "ID3D11ShaderResourceView",
    "ID3D11Texture2D",
    "ID3D11VertexShader",
    "ID3DBlob",
    "IDXGIFactory",
    "IDXGISwapChain",
    "IUnknown",
    "IUnknownVTable",
    "LUID",
    "PAINTSTRUCT",
    "POINT",
    "RECT",
    "SIZE",
    "WindowsLibraryError",
    "_D3D11CreateDeviceProto",
    "_as_cvoidp",
    "_as_void_ptr",
    "_proc",
    "_ptr_val",
    "blob_to_bytes",
    "check_hresult",
    "com",
    "ctypes_compilation",
    "d3d11",
    "d3dcompile",
    "declare_interface",
    "dxgi",
    "ensure_windows",
    "foundation",
    "gdi32",
    "get_platform_bindings",
    "is_available",
    "kernel32",
    "load_library",
    "ole32",
    "user32",
    "windows",
    "D3D11_USAGE_DEFAULT",
    "D3D11_SRV_DIMENSION_TEXTURE2D",
    "D3D11_BIND_SHADER_RESOURCE",
    "DXGI_FORMAT_R8G8B8A8_UNORM",
    "D3D11_QUERY_EVENT",
    "DXGI_MODE_SCALING_UNSPECIFIED",
    "DXGI_MODE_SCANLINE_ORDER_UNSPECIFIED",
    "DXGI_SWAP_EFFECT_DISCARD",
    "DXGI_USAGE_RENDER_TARGET_OUTPUT",
    "D3D11_COMPARISON_ALWAYS",
    "D3D11_FILTER_MIN_MAG_MIP_LINEAR",
    "D3D11_TEXTURE_ADDRESS_CLAMP",
    "D3D11_BLEND_ONE",
    "D3D11_BLEND_OP_ADD",
    "D3D11_BLEND_ZERO",
    "D3D11_COLOR_WRITE_ENABLE_ALL",
    "D3D11_COMPARISON_LESS",
    "D3D11_CULL_BACK",
    "D3D11_DEPTH_WRITE_MASK_ALL",
    "D3D11_FILL_SOLID",
    "D3D11_INPUT_PER_VERTEX_DATA",
    "DXGI_FORMAT_R32G32_FLOAT",
    "DXGI_FORMAT_R32G32B32_FLOAT",
    "D3D11_CREATE_DEVICE_BGRA_SUPPORT",
    "D3D11_SDK_VERSION",
    "D3D11_BIND_RENDER_TARGET",
    "D3D11_RTV_DIMENSION_TEXTURE2D",
    "D3D_PRIMITIVE_TOPOLOGY_TRIANGLELIST",
    "DXGI_FORMAT_R32_UINT",
    "D3D11_BIND_INDEX_BUFFER",
    "D3D11_BIND_VERTEX_BUFFER",
    "DXGI_SWAP_EFFECT_FLIP_DISCARD",
    "DXGI_SWAP_EFFECT_FLIP_SEQUENTIAL",
    "DXGI_SWAP_EFFECT_SEQUENTIAL",
    "DXGI_USAGE_SHADER_INPUT",
    "D3D11CreateDeviceAndSwapChain",
    "IID_ID3D11Texture2D",
    "GL_ARRAY_BUFFER",
    "GL_BLEND",
    "GL_COLOR_BUFFER_BIT",
    "GL_DEPTH_BUFFER_BIT",
    "GL_DYNAMIC_DRAW",
    "GL_ELEMENT_ARRAY_BUFFER",
    "GL_FLOAT",
    "GL_ONE_MINUS_SRC_ALPHA",
    "GL_QUADS",
    "GL_RGBA",
    "GL_SRC_ALPHA",
    "GL_STATIC_DRAW",
    "GL_STENCIL_BUFFER_BIT",
    "GL_TEXTURE_2D",
    "GL_TRIANGLE_STRIP",
    "GL_TRIANGLES",
    "GL_UNSIGNED_BYTE",
    "glAttachShader",
    "glBindBuffer",
    "glBindTexture",
    "glBlendFunc",
    "glBufferData",
    "glBufferSubData",
    "glClear",
    "glClearColor",
    "glCompileShader",
    "glCreateProgram",
    "glCreateShader",
    "glDeleteBuffers",
    "glDeleteProgram",
    "glDeleteShader",
    "glDeleteTextures",
    "glDisable",
    "glDisableVertexAttribArray",
    "glDrawArrays",
    "glDrawElements",
    "glEnable",
    "glEnableVertexAttribArray",
    "glGenBuffers",
    "glGenTextures",
    "glGetProgramInfoLog",
    "glGetProgramiv",
    "glGetShaderInfoLog",
    "glGetShaderiv",
    "glGetUniformLocation",
    "glLinkProgram",
    "glShaderSource",
    "glTexImage2D",
    "glTexParameteri",
    "glUniform1f",
    "glUniform2f",
    "glUniform3f",
    "glUniform4f",
    "glUniformMatrix4fv",
    "glUseProgram",
    "glVertexAttribPointer",
    "glViewport",
    "GL_RGB",
    "GL_UNSIGNED_SHORT",
    "GL_TEXTURE_MAG_FILTER",
    "GL_TEXTURE_MIN_FILTER",
    "GL_LINEAR",
    "GL_MODELVIEW",
    "GL_PROJECTION",
    "glBegin",
    "glEnd",
    "glColor4f",
    "glVertex2f",
    "glTexCoord2f",
    "glRasterPos2f",
    "glPushAttrib",
    "glPopAttrib",
    "glListBase",
    "glCallLists",
    "glMatrixMode",
    "glLoadIdentity",
    "glOrtho",
    "glTexSubImage2D",
    "wglSwapBuffers",
    "wglCreateContext",
    "wglMakeCurrent",
    "wglDeleteContext",
    "wglGetCurrentContext",
    "wglGetCurrentDC",
    "GL_DEPTH_TEST",
    "DeleteObject",
    "SelectObject",
    "ctwt",
    "PIXELFORMATDESCRIPTOR",
    "ChoosePixelFormat",
    "GetDC",
    "ReleaseDC",
    "SetPixelFormat",
    "SwapBuffers",
    "HWND",
    "CreateFontW",
    "GetModuleHandleW",
    "D3D11_BIND_CONSTANT_BUFFER",
    "D3D11_INPUT_PER_INSTANCE_DATA",
    "D3D11_USAGE_DYNAMIC",
    "DXGI_FORMAT_R16_UINT",
    "DXGI_FORMAT_R32G32B32A32_FLOAT",
    "GL_UNIFORM_BUFFER",
    "glBindBufferBase",
    "GL_STREAM_DRAW",
    "GL_TEXTURE_WRAP_S",
    "GL_TEXTURE_WRAP_T",
    "glTexParameterf",
    "GL_CLAMP_TO_BORDER",
    "GL_CLAMP_TO_EDGE",
    "GL_MIRRORED_REPEAT",
    "GL_REPEAT",
    "GL_LINEAR_MIPMAP_LINEAR",
    "GL_LINEAR_MIPMAP_NEAREST",
    "GL_NEAREST",
    "GL_NEAREST_MIPMAP_LINEAR",
    "GL_NEAREST_MIPMAP_NEAREST",
    "GL_DEPTH_COMPONENT",
    "GL_DEPTH_COMPONENT24",
    "GL_DEPTH_COMPONENT32F",
    "GL_HALF_FLOAT",
    "GL_RGB8",
    "GL_RGB16F",
    "GL_RGB32F",
    "GL_RGBA8",
    "GL_STENCIL_INDEX",
    "GL_STENCIL_INDEX8",
    "GL_UNSIGNED_INT",
    "GL_TEXTURE0",
    "glActiveTexture",
    "glGenerateMipmap",
    "GL_TEXTURE_CUBE_MAP",
    "GL_TEXTURE_WRAP_R",
    "glTexParamaterf",
    "GL_TEXTURE_CUBE_MAP_NEGATIVE_X",
    "GL_TEXTURE_CUBE_MAP_NEGATIVE_Y",
    "GL_TEXTURE_CUBE_MAP_NEGATIVE_Z",
    "GL_TEXTURE_CUBE_MAP_POSITIVE_X",
    "GL_TEXTURE_CUBE_MAP_POSITIVE_Y",
    "GL_TEXTURE_CUBE_MAP_POSITIVE_Z",
    "D3D11_MAP_WRITE_DISCARD",
    "IASetIndexBuffer",
    "D3D11_MAPPED_SUBRESOURCE",
    "D3D11_CPU_ACCESS_WRITE",
    "IASetInputLayout",
    "GL_RGBA16F",
    "GL_RGBA32F",
    "GL_TEXTURE_MAX_ANISOTROPY_EXT",
    "FLOAT",
    "PostQuitMessage",
    "GLuintArray",
    "glGenVertexArrays",
    "glBindVertexArray",
    "glVertexAttribDivisor",
    "GL_FALSE",
    "GL_TRUE",
    "GL_INVALID_ENUM",
    "GL_INVALID_FRAMEBUFFER_OPERATION",
    "GL_INVALID_OPERATION",
    "GL_INVALID_VALUE",
    "GL_NO_ERROR",
    "GL_OUT_OF_MEMORY",
    "GL_STACK_OVERFLOW",
    "GL_STACK_UNDERFLOW",
    "glGetError",
    "GL_VERSION",
    "GL_EXTENSIONS",
    "glGetString",
    "GL_MAX_TEXTURE_SIZE",
    "glGetIntegerv",
    "glDeleteVertexArrays",
    "GL_MAX_VIEWPORT_DIMS",
    "GL_RENDERER",
    "GL_VENDOR",
    "glDetachShader",
    "glDrawArraysInstanced",
    "glDrawElementsInstanced",
    "GL_COMPILE_STATUS",
    "GL_FRAGMENT_SHADER",
    "GL_LINK_STATUS",
    "GL_VERTEX_SHADER",
    "glfloatArray",
    "GLuintArray",
    "GL_TEXTURE_LOD_BIAS",
    "GL_TEXTURE_MAX_LOD",
    "GL_TEXTURE_MIN_LOD",
    "_gl_filter",
    "_gl_wrap",
    "glGenSamplers",
    "glSamplerParameterf",
    "glSamplerParameteri",
    "glBindSampler",
]