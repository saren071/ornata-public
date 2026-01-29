"""Direct3D 11 ctypes bindings used by Ornata."""

from __future__ import annotations

import ctypes as ct
import enum
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from ornata.interop.ctypes_compilation.windows import dxgi
from ornata.interop.ctypes_compilation.windows.com import COMInterface, COMPointer
from ornata.interop.ctypes_compilation.windows.foundation import (
    BOOL,
    BYTE,
    FLOAT,
    GUID,
    HRESULT,
    INT,
    UINT,
    WindowsLibraryError,
    ensure_windows,
    load_library,
    to_int,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


def _ptr_val(obj: COMPointer | None) -> int:
    """Return the integer address for a COMPointer (or 0 if None)."""
    if obj is None:
        return 0
    raw = obj.pointer.value
    return to_int(raw)


def _as_cvoidp(p: ct.c_void_p | COMPointer | int | None) -> ct.c_void_p:
    """Normalize to a c_void_p without ever constructing it from None."""
    if isinstance(p, COMPointer):
        return ct.c_void_p(_ptr_val(p))
    if isinstance(p, ct.c_void_p):
        v = p.value
        return ct.c_void_p(to_int(v) if v is not None else 0)
    if p is None:
        return ct.c_void_p(0)
    return ct.c_void_p(to_int(p))


class D3D_DRIVER_TYPE(enum.IntEnum):
    """Driver types supported by ``D3D11CreateDevice``."""

    UNKNOWN = 0
    HARDWARE = 1
    REFERENCE = 2
    NULL = 3
    SOFTWARE = 4
    WARP = 5


class D3D_FEATURE_LEVEL(enum.IntEnum):
    """Feature levels supported by Direct3D."""

    LEVEL_9_1 = 0x9100
    LEVEL_9_2 = 0x9200
    LEVEL_9_3 = 0x9300
    LEVEL_10_0 = 0xA000
    LEVEL_10_1 = 0xA100
    LEVEL_11_0 = 0xB000
    LEVEL_11_1 = 0xB100


D3D11_SDK_VERSION = 7
D3D11_CREATE_DEVICE_BGRA_SUPPORT = 0x20

D3D11_BIND_VERTEX_BUFFER = 0x0001
D3D11_BIND_INDEX_BUFFER = 0x0002
D3D11_BIND_CONSTANT_BUFFER = 0x0004
D3D11_BIND_SHADER_RESOURCE = 0x0008
D3D11_BIND_STREAM_OUTPUT = 0x0010
D3D11_BIND_RENDER_TARGET = 0x0020
D3D11_BIND_DEPTH_STENCIL = 0x0040
D3D11_BIND_UNORDERED_ACCESS = 0x0080

D3D11_USAGE_DEFAULT = 0
D3D11_USAGE_IMMUTABLE = 1
D3D11_USAGE_DYNAMIC = 2
D3D11_USAGE_STAGING = 3

# CPU access flags (missing feature)
D3D11_CPU_ACCESS_WRITE = 0x00010000

D3D11_INPUT_PER_VERTEX_DATA = 0
D3D11_INPUT_PER_INSTANCE_DATA = 1

D3D11_RTV_DIMENSION_TEXTURE2D = 4
D3D11_SRV_DIMENSION_TEXTURE2D = 3

D3D11_FILTER_MIN_MAG_MIP_LINEAR = 0x15
D3D11_TEXTURE_ADDRESS_WRAP = 1
D3D11_TEXTURE_ADDRESS_MIRROR = 2
D3D11_TEXTURE_ADDRESS_CLAMP = 3
D3D11_TEXTURE_ADDRESS_BORDER = 4
D3D11_TEXTURE_ADDRESS_MIRROR_ONCE = 5

D3D11_COMPARISON_NEVER = 1
D3D11_COMPARISON_LESS = 2
D3D11_COMPARISON_ALWAYS = 8

D3D11_QUERY_EVENT = 0

D3D11_FILL_SOLID = 3
D3D11_CULL_BACK = 3

D3D11_DEPTH_WRITE_MASK_ZERO = 0
D3D11_DEPTH_WRITE_MASK_ALL = 1

D3D11_BLEND_ZERO = 1
D3D11_BLEND_ONE = 2
D3D11_BLEND_OP_ADD = 1
D3D11_COLOR_WRITE_ENABLE_ALL = 0x0F

D3D_PRIMITIVE_TOPOLOGY_TRIANGLELIST = 4
IID_ID3D11Texture2D = GUID("{6F15AAF2-D208-4E89-9AB4-489535D34F9C}")

# Map flags (missing feature)
# Full enum values for reference:
# READ=1, WRITE=2, READ_WRITE=3, WRITE_DISCARD=4, WRITE_NO_OVERWRITE=5
D3D11_MAP_WRITE_DISCARD = 4


class D3D11_BUFFER_DESC(ct.Structure):
    """Description used when creating buffers."""

    _fields_ = [
        ("ByteWidth", UINT),
        ("Usage", UINT),
        ("BindFlags", UINT),
        ("CPUAccessFlags", UINT),
        ("MiscFlags", UINT),
        ("StructureByteStride", UINT),
    ]


class D3D11_SUBRESOURCE_DATA(ct.Structure):
    """Initial data passed to ``CreateBuffer`` and similar methods."""

    _fields_ = [
        ("pSysMem", ct.c_void_p),
        ("SysMemPitch", UINT),
        ("SysMemSlicePitch", UINT),
    ]


class D3D11_MAPPED_SUBRESOURCE(ct.Structure):
    """Result of ``ID3D11DeviceContext::Map`` (missing feature)."""

    _fields_ = [
        ("pData", ct.c_void_p),
        ("RowPitch", UINT),
        ("DepthPitch", UINT),
    ]


class D3D11_VIEWPORT(ct.Structure):
    """Viewport description for ``RSSetViewports``."""

    _fields_ = [
        ("TopLeftX", FLOAT),
        ("TopLeftY", FLOAT),
        ("Width", FLOAT),
        ("Height", FLOAT),
        ("MinDepth", FLOAT),
        ("MaxDepth", FLOAT),
    ]


class D3D11_TEX2D_RTV(ct.Structure):
    """Texture2D slice selection for render target views."""

    _fields_ = [("MipSlice", UINT)]


class D3D11_RENDER_TARGET_VIEW_DESC(ct.Structure):
    """Render target view description."""

    class _Anonymous(ct.Union):
        _fields_ = [("Texture2D", D3D11_TEX2D_RTV)]

    _anonymous_ = ("Anonymous",)
    _fields_ = [
        ("Format", UINT),
        ("ViewDimension", UINT),
        ("Anonymous", _Anonymous),
    ]


class D3D11_TEXTURE2D_DESC(ct.Structure):
    """Texture2D description."""

    _fields_ = [
        ("Width", UINT),
        ("Height", UINT),
        ("MipLevels", UINT),
        ("ArraySize", UINT),
        ("Format", UINT),
        ("SampleDesc", dxgi.DXGI_SAMPLE_DESC),
        ("Usage", UINT),
        ("BindFlags", UINT),
        ("CPUAccessFlags", UINT),
        ("MiscFlags", UINT),
    ]


class D3D11_INPUT_ELEMENT_DESC(ct.Structure):
    """Vertex input layout element description."""

    _fields_ = [
        ("SemanticName", ct.c_char_p),
        ("SemanticIndex", UINT),
        ("Format", UINT),
        ("InputSlot", UINT),
        ("AlignedByteOffset", UINT),
        ("InputSlotClass", UINT),
        ("InstanceDataStepRate", UINT),
    ]


class D3D11_SAMPLER_DESC(ct.Structure):
    """Sampler state description."""

    _fields_ = [
        ("Filter", UINT),
        ("AddressU", UINT),
        ("AddressV", UINT),
        ("AddressW", UINT),
        ("MipLODBias", FLOAT),
        ("MaxAnisotropy", UINT),
        ("ComparisonFunc", UINT),
        ("BorderColor", FLOAT * 4),
        ("MinLOD", FLOAT),
        ("MaxLOD", FLOAT),
    ]


class D3D11_QUERY_DESC(ct.Structure):
    """Query description used for GPU synchronization primitives."""

    _fields_ = [("Query", UINT), ("MiscFlags", UINT)]


class D3D11_DEPTH_STENCILOP_DESC(ct.Structure):
    """Stencil operation description used inside depth stencil state."""

    _fields_ = [
        ("StencilFailOp", UINT),
        ("StencilDepthFailOp", UINT),
        ("StencilPassOp", UINT),
        ("StencilFunc", UINT),
    ]


class D3D11_DEPTH_STENCIL_DESC(ct.Structure):
    """Depth stencil state description."""

    _fields_ = [
        ("DepthEnable", BOOL),
        ("DepthWriteMask", UINT),
        ("DepthFunc", UINT),
        ("StencilEnable", BOOL),
        ("StencilReadMask", ct.c_ubyte),
        ("StencilWriteMask", ct.c_ubyte),
        ("FrontFace", D3D11_DEPTH_STENCILOP_DESC),
        ("BackFace", D3D11_DEPTH_STENCILOP_DESC),
    ]


class D3D11_RASTERIZER_DESC(ct.Structure):
    """Rasterizer state description."""

    _fields_ = [
        ("FillMode", UINT),
        ("CullMode", UINT),
        ("FrontCounterClockwise", BOOL),
        ("DepthBias", INT),
        ("DepthBiasClamp", FLOAT),
        ("SlopeScaledDepthBias", FLOAT),
        ("DepthClipEnable", BOOL),
        ("ScissorEnable", BOOL),
        ("MultisampleEnable", BOOL),
        ("AntialiasedLineEnable", BOOL),
    ]


class D3D11_RENDER_TARGET_BLEND_DESC(ct.Structure):
    """Per render target blend state configuration."""

    _fields_ = [
        ("BlendEnable", BOOL),
        ("SrcBlend", UINT),
        ("DestBlend", UINT),
        ("BlendOp", UINT),
        ("SrcBlendAlpha", UINT),
        ("DestBlendAlpha", UINT),
        ("BlendOpAlpha", UINT),
        ("RenderTargetWriteMask", ct.c_ubyte),
    ]


class D3D11_BLEND_DESC(ct.Structure):
    """Blend state description."""

    _fields_ = [
        ("AlphaToCoverageEnable", BOOL),
        ("IndependentBlendEnable", BOOL),
        ("RenderTarget", D3D11_RENDER_TARGET_BLEND_DESC * 8),
    ]


class D3D11_TEX2D_SRV(ct.Structure):
    """Texture2D view selection for shader resource views."""

    _fields_ = [
        ("MostDetailedMip", UINT),
        ("MipLevels", UINT),
    ]


class D3D11_SHADER_RESOURCE_VIEW_DESC(ct.Structure):
    """Shader resource view description."""

    class _Anonymous(ct.Union):
        _fields_ = [("Texture2D", D3D11_TEX2D_SRV)]

    _anonymous_ = ("Anonymous",)
    _fields_ = [
        ("Format", UINT),
        ("ViewDimension", UINT),
        ("Anonymous", _Anonymous),
    ]


class ID3D11Buffer(COMInterface):
    """Opaque pointer to ``ID3D11Buffer``."""

    _methods_ = {
        "QueryInterface": (0, HRESULT, (ct.POINTER(GUID), ct.POINTER(ct.c_void_p))),
        "AddRef": (1, UINT, ()),
        "Release": (2, UINT, ()),
    }


class ID3D11Texture2D(COMInterface):
    """Opaque pointer to ``ID3D11Texture2D``."""

    _methods_ = {
        "QueryInterface": (0, HRESULT, (ct.POINTER(GUID), ct.POINTER(ct.c_void_p))),
        "AddRef": (1, UINT, ()),
        "Release": (2, UINT, ()),
    }


class ID3D11RenderTargetView(COMInterface):
    """Opaque pointer to ``ID3D11RenderTargetView``."""

    _methods_ = {
        "QueryInterface": (0, HRESULT, (ct.POINTER(GUID), ct.POINTER(ct.c_void_p))),
        "AddRef": (1, UINT, ()),
        "Release": (2, UINT, ()),
    }


class ID3D11InputLayout(COMInterface):
    """Opaque pointer to ``ID3D11InputLayout``."""

    _methods_ = {
        "QueryInterface": (0, HRESULT, (ct.POINTER(GUID), ct.POINTER(ct.c_void_p))),
        "AddRef": (1, UINT, ()),
        "Release": (2, UINT, ()),
    }


class ID3D11SamplerState(COMInterface):
    """Opaque pointer to ``ID3D11SamplerState``."""

    _methods_ = {
        "QueryInterface": (0, HRESULT, (ct.POINTER(GUID), ct.POINTER(ct.c_void_p))),
        "AddRef": (1, UINT, ()),
        "Release": (2, UINT, ()),
    }


class ID3D11VertexShader(COMInterface):
    """Opaque pointer to ``ID3D11VertexShader``."""

    _methods_ = {
        "QueryInterface": (0, HRESULT, (ct.POINTER(GUID), ct.POINTER(ct.c_void_p))),
        "AddRef": (1, UINT, ()),
        "Release": (2, UINT, ()),
    }


class ID3D11PixelShader(COMInterface):
    """Opaque pointer to ``ID3D11PixelShader``."""

    _methods_ = {
        "QueryInterface": (0, HRESULT, (ct.POINTER(GUID), ct.POINTER(ct.c_void_p))),
        "AddRef": (1, UINT, ()),
        "Release": (2, UINT, ()),
    }


class ID3D11ShaderResourceView(COMInterface):
    """Opaque pointer to ``ID3D11ShaderResourceView``."""

    _methods_ = {
        "QueryInterface": (0, HRESULT, (ct.POINTER(GUID), ct.POINTER(ct.c_void_p))),
        "AddRef": (1, UINT, ()),
        "Release": (2, UINT, ()),
    }


class ID3D11Query(COMInterface):
    """Opaque pointer to ``ID3D11Query``."""

    _methods_ = {
        "QueryInterface": (0, HRESULT, (ct.POINTER(GUID), ct.POINTER(ct.c_void_p))),
        "AddRef": (1, UINT, ()),
        "Release": (2, UINT, ()),
    }


class ID3D11RasterizerState(COMInterface):
    """Opaque pointer to ``ID3D11RasterizerState``."""

    _methods_ = {
        "QueryInterface": (0, HRESULT, (ct.POINTER(GUID), ct.POINTER(ct.c_void_p))),
        "AddRef": (1, UINT, ()),
        "Release": (2, UINT, ()),
    }


class ID3D11DepthStencilState(COMInterface):
    """Opaque pointer to ``ID3D11DepthStencilState``."""

    _methods_ = {
        "QueryInterface": (0, HRESULT, (ct.POINTER(GUID), ct.POINTER(ct.c_void_p))),
        "AddRef": (1, UINT, ()),
        "Release": (2, UINT, ()),
    }


class ID3D11BlendState(COMInterface):
    """Opaque pointer to ``ID3D11BlendState``."""

    _methods_ = {
        "QueryInterface": (0, HRESULT, (ct.POINTER(GUID), ct.POINTER(ct.c_void_p))),
        "AddRef": (1, UINT, ()),
        "Release": (2, UINT, ()),
    }


class ID3D11HullShader(COMInterface):
    _methods_ = {
        "QueryInterface": (0, HRESULT, (ct.POINTER(GUID), ct.POINTER(ct.c_void_p))),
        "AddRef": (1, UINT, ()),
        "Release": (2, UINT, ()),
    }


class ID3D11DomainShader(COMInterface):
    _methods_ = {
        "QueryInterface": (0, HRESULT, (ct.POINTER(GUID), ct.POINTER(ct.c_void_p))),
        "AddRef": (1, UINT, ()),
        "Release": (2, UINT, ()),
    }


class ID3D11ComputeShader(COMInterface):
    _methods_ = {
        "QueryInterface": (0, HRESULT, (ct.POINTER(GUID), ct.POINTER(ct.c_void_p))),
        "AddRef": (1, UINT, ()),
        "Release": (2, UINT, ()),
    }


class ID3D11GeometryShader(COMInterface):
    _methods_ = {
        "QueryInterface": (0, HRESULT, (ct.POINTER(GUID), ct.POINTER(ct.c_void_p))),
        "AddRef": (1, UINT, ()),
        "Release": (2, UINT, ()),
    }


class ID3D11DeviceChild(COMInterface):
    """Base class for D3D11 objects that are children of a device."""

    _methods_ = {
        "GetDevice": (3, None, (ct.POINTER(ct.c_void_p),)),
    }


class ID3D11Device(COMInterface):
    """Minimal subset of the ``ID3D11Device`` COM interface."""

    _methods_ = {
        # buffers/textures
        "CreateBuffer": (
            3,
            HRESULT,
            (ct.POINTER(D3D11_BUFFER_DESC), ct.POINTER(D3D11_SUBRESOURCE_DATA), ct.POINTER(ct.c_void_p)),
        ),
        "CreateTexture2D": (5, HRESULT, (ct.POINTER(D3D11_TEXTURE2D_DESC), ct.c_void_p, ct.POINTER(ct.c_void_p))),
        # views
        "CreateShaderResourceView": (
            7,
            HRESULT,
            (ct.c_void_p, ct.POINTER(D3D11_SHADER_RESOURCE_VIEW_DESC), ct.POINTER(ct.c_void_p)),
        ),
        "CreateRenderTargetView": (
            9,
            HRESULT,
            (ct.c_void_p, ct.POINTER(D3D11_RENDER_TARGET_VIEW_DESC), ct.POINTER(ct.c_void_p)),
        ),
        # input layout + shaders
        "CreateInputLayout": (
            11,
            HRESULT,
            (ct.POINTER(D3D11_INPUT_ELEMENT_DESC), UINT, ct.c_void_p, ct.c_size_t, ct.POINTER(ct.c_void_p)),
        ),
        "CreateVertexShader": (12, HRESULT, (ct.c_void_p, ct.c_size_t, ct.c_void_p, ct.POINTER(ct.c_void_p))),
        "CreateGeometryShader": (13, HRESULT, (ct.c_void_p, ct.c_size_t, ct.c_void_p, ct.POINTER(ct.c_void_p))),
        "CreatePixelShader": (15, HRESULT, (ct.c_void_p, ct.c_size_t, ct.c_void_p, ct.POINTER(ct.c_void_p))),
        "CreateHullShader": (16, HRESULT, (ct.c_void_p, ct.c_size_t, ct.c_void_p, ct.POINTER(ct.c_void_p))),
        "CreateDomainShader": (17, HRESULT, (ct.c_void_p, ct.c_size_t, ct.c_void_p, ct.POINTER(ct.c_void_p))),
        "CreateComputeShader": (18, HRESULT, (ct.c_void_p, ct.c_size_t, ct.c_void_p, ct.POINTER(ct.c_void_p))),
        # pipeline states
        "CreateBlendState": (20, HRESULT, (ct.POINTER(D3D11_BLEND_DESC), ct.POINTER(ct.c_void_p))),
        "CreateDepthStencilState": (21, HRESULT, (ct.POINTER(D3D11_DEPTH_STENCIL_DESC), ct.POINTER(ct.c_void_p))),
        "CreateRasterizerState": (22, HRESULT, (ct.POINTER(D3D11_RASTERIZER_DESC), ct.POINTER(ct.c_void_p))),
        "CreateSamplerState": (23, HRESULT, (ct.POINTER(D3D11_SAMPLER_DESC), ct.POINTER(ct.c_void_p))),
        # sync/query
        "CreateQuery": (24, HRESULT, (ct.POINTER(D3D11_QUERY_DESC), ct.POINTER(ct.c_void_p))),
        "Release": (2, UINT, ()),
        "AddRef": (1, UINT, ()),
    }

    def CreateInputLayout(
        self,
        descs: Sequence[D3D11_INPUT_ELEMENT_DESC],
        count: UINT,
        bytecode_ptr: ct.c_void_p | int,
        bytecode_length: int,
        out_layout: ID3D11InputLayout,
    ) -> int:
        arr_t = D3D11_INPUT_ELEMENT_DESC * to_int(count, UINT)
        arr = arr_t(*descs)
        bc = _as_cvoidp(bytecode_ptr)
        return to_int(
            self._invoke(
                "CreateInputLayout",
                arr,
                to_int(count, UINT),
                bc,
                ct.c_size_t(to_int(bytecode_length)),
                out_layout.out_param(),
            ),
            HRESULT,
        )

    def CreateVertexShader(
        self,
        bytecode_ptr: ct.c_void_p | int,
        bytecode_length: int,
        class_linkage: ct.c_void_p | int | None,
        out_shader: ID3D11VertexShader,
    ) -> int:
        bc = _as_cvoidp(bytecode_ptr)
        cl = _as_cvoidp(class_linkage) if class_linkage is not None else ct.c_void_p(0)
        return to_int(self._invoke("CreateVertexShader", bc, ct.c_size_t(to_int(bytecode_length)), cl, out_shader.out_param()), HRESULT)

    def CreatePixelShader(
        self,
        bytecode_ptr: ct.c_void_p | int,
        bytecode_length: int,
        class_linkage: ct.c_void_p | int | None,
        out_shader: ID3D11PixelShader,
    ) -> int:
        bc = _as_cvoidp(bytecode_ptr)
        cl = _as_cvoidp(class_linkage) if class_linkage is not None else ct.c_void_p(0)
        return to_int(self._invoke("CreatePixelShader", bc, ct.c_size_t(to_int(bytecode_length)), cl, out_shader.out_param()), HRESULT)

    def CreateGeometryShader(
        self,
        bytecode_ptr: ct.c_void_p | int,
        bytecode_length: int,
        class_linkage: ct.c_void_p | int | None,
        out_shader: ID3D11GeometryShader,
    ) -> int:
        bc = _as_cvoidp(bytecode_ptr)
        cl = _as_cvoidp(class_linkage) if class_linkage is not None else ct.c_void_p(0)
        return to_int(self._invoke("CreateGeometryShader", bc, ct.c_size_t(to_int(bytecode_length)), cl, out_shader.out_param()), HRESULT)

    def CreateHullShader(
        self,
        bytecode_ptr: ct.c_void_p | int,
        bytecode_length: int,
        class_linkage: ct.c_void_p | int | None,
        out_shader: ID3D11HullShader,
    ) -> int:
        bc = _as_cvoidp(bytecode_ptr)
        cl = _as_cvoidp(class_linkage) if class_linkage is not None else ct.c_void_p(0)
        return to_int(self._invoke("CreateHullShader", bc, ct.c_size_t(to_int(bytecode_length)), cl, out_shader.out_param()), HRESULT)

    def CreateDomainShader(
        self,
        bytecode_ptr: ct.c_void_p | int,
        bytecode_length: int,
        class_linkage: ct.c_void_p | int | None,
        out_shader: ID3D11DomainShader,
    ) -> int:
        bc = _as_cvoidp(bytecode_ptr)
        cl = _as_cvoidp(class_linkage) if class_linkage is not None else ct.c_void_p(0)
        return to_int(self._invoke("CreateDomainShader", bc, ct.c_size_t(to_int(bytecode_length)), cl, out_shader.out_param()), HRESULT)

    def CreateComputeShader(
        self,
        bytecode_ptr: ct.c_void_p | int,
        bytecode_length: int,
        class_linkage: ct.c_void_p | int | None,
        out_shader: ID3D11ComputeShader,
    ) -> int:
        bc = _as_cvoidp(bytecode_ptr)
        cl = _as_cvoidp(class_linkage) if class_linkage is not None else ct.c_void_p(0)
        return to_int(self._invoke("CreateComputeShader", bc, ct.c_size_t(to_int(bytecode_length)), cl, out_shader.out_param()), HRESULT)

    def CreateBuffer(
        self,
        desc: D3D11_BUFFER_DESC,
        init_data: D3D11_SUBRESOURCE_DATA | None,
        out_buffer: ID3D11Buffer,
    ) -> int:
        desc_p = ct.byref(desc)
        init_p = ct.byref(init_data) if isinstance(init_data, D3D11_SUBRESOURCE_DATA) else None
        return to_int(self._invoke("CreateBuffer", desc_p, init_p, out_buffer.out_param()), HRESULT)

    def CreateTexture2D(
        self,
        desc: D3D11_TEXTURE2D_DESC,
        init_data_blob: ct.c_void_p | int | None,
        out_tex: ID3D11Texture2D,
    ) -> int:
        desc_p = ct.byref(desc)
        init_arg = _as_cvoidp(init_data_blob)
        return to_int(self._invoke("CreateTexture2D", desc_p, init_arg, out_tex.out_param()), HRESULT)

    def CreateRenderTargetView(
        self,
        resource: COMPointer | ct.c_void_p | int | None,
        desc: D3D11_RENDER_TARGET_VIEW_DESC | None,
        out_rtv: ID3D11RenderTargetView,
    ) -> int:
        res_ptr = _as_cvoidp(resource)
        desc_p = ct.byref(desc) if isinstance(desc, D3D11_RENDER_TARGET_VIEW_DESC) else None
        return to_int(self._invoke("CreateRenderTargetView", res_ptr, desc_p, out_rtv.out_param()), HRESULT)

    def CreateShaderResourceView(
        self,
        resource: COMPointer | ct.c_void_p | int | None,
        desc: D3D11_SHADER_RESOURCE_VIEW_DESC | None,
        out_srv: ID3D11ShaderResourceView,
    ) -> int:
        res_ptr = _as_cvoidp(resource)
        desc_p = ct.byref(desc) if isinstance(desc, D3D11_SHADER_RESOURCE_VIEW_DESC) else None
        return to_int(self._invoke("CreateShaderResourceView", res_ptr, desc_p, out_srv.out_param()), HRESULT)

    def CreateBlendState(self, desc: D3D11_BLEND_DESC, out_state: ID3D11BlendState) -> int:
        return to_int(self._invoke("CreateBlendState", ct.byref(desc), out_state.out_param()), HRESULT)

    def CreateDepthStencilState(self, desc: D3D11_DEPTH_STENCIL_DESC, out_state: ID3D11DepthStencilState) -> int:
        return to_int(self._invoke("CreateDepthStencilState", ct.byref(desc), out_state.out_param()), HRESULT)

    def CreateRasterizerState(self, desc: D3D11_RASTERIZER_DESC, out_state: ID3D11RasterizerState) -> int:
        return to_int(self._invoke("CreateRasterizerState", ct.byref(desc), out_state.out_param()), HRESULT)

    def CreateSamplerState(self, desc: D3D11_SAMPLER_DESC, out_state: ID3D11SamplerState) -> int:
        return to_int(self._invoke("CreateSamplerState", ct.byref(desc), out_state.out_param()), HRESULT)

    def CreateQuery(self, desc: D3D11_QUERY_DESC, out_query: ID3D11Query) -> int:
        return to_int(self._invoke("CreateQuery", ct.byref(desc), out_query.out_param()), HRESULT)


class ID3D11DeviceContext(COMInterface):
    """Thin wrapper that adapts Python-friendly signatures to the COM vtable."""

    _methods_ = {
        "QueryInterface": (0, HRESULT, (ct.POINTER(GUID), ct.POINTER(ct.c_void_p))),
        "AddRef": (1, UINT, ()),
        "Release": (2, UINT, ()),
        "GetDevice": (3, None, (ct.POINTER(ct.c_void_p),)),
        "VSSetConstantBuffers": (7, None, (UINT, UINT, ct.POINTER(ct.c_void_p))),
        "PSSetShaderResources": (8, None, (UINT, UINT, ct.POINTER(ct.c_void_p))),
        "PSSetSamplers": (9, None, (UINT, UINT, ct.POINTER(ct.c_void_p))),
        "PSSetShader": (10, None, (ct.c_void_p, ct.c_void_p, UINT)),
        "VSSetShader": (11, None, (ct.c_void_p, ct.c_void_p, UINT)),
        "DrawIndexed": (12, None, (UINT, UINT, INT)),
        "Draw": (13, None, (UINT, UINT)),
        "GSSetConstantBuffers": (14, None, (UINT, UINT, ct.POINTER(ct.c_void_p))),
        "GSSetShader": (15, None, (ct.c_void_p, ct.c_void_p, UINT)),
        "IASetPrimitiveTopology": (24, None, (UINT,)),
        "IASetInputLayout": (17, None, (ct.c_void_p,)),
        "IASetVertexBuffers": (18, None, (UINT, UINT, ct.POINTER(ct.c_void_p), ct.POINTER(UINT), ct.POINTER(UINT))),
        "IASetIndexBuffer": (19, None, (ct.c_void_p, UINT, UINT)),
        "DrawIndexedInstanced": (20, None, (UINT, UINT, UINT, INT, UINT)),
        "DrawInstanced": (21, None, (UINT, UINT, UINT, UINT)),
        "GSSetShaderResources": (22, None, (UINT, UINT, ct.POINTER(ct.c_void_p))),
        "OMSetRenderTargets": (33, None, (UINT, ct.POINTER(ct.c_void_p), ct.c_void_p)),
        "OMSetBlendState": (35, None, (ct.c_void_p, ct.POINTER(FLOAT), UINT)),
        "OMSetDepthStencilState": (36, None, (ct.c_void_p, UINT)),
        "RSSetViewports": (44, None, (UINT, ct.POINTER(D3D11_VIEWPORT))),
        "RSSetScissorRects": (45, None, (UINT, ct.c_void_p)),
        "ClearRenderTargetView": (47, None, (ct.c_void_p, ct.POINTER(FLOAT))),
        "ClearDepthStencilView": (48, None, (ct.c_void_p, UINT, FLOAT, BYTE)),
        "HSSetShader": (58, None, (ct.c_void_p, ct.c_void_p, UINT)),
        "DSSetShader": (61, None, (ct.c_void_p, ct.c_void_p, UINT)),
    }

    def RSSetViewports(self, viewports: Sequence[D3D11_VIEWPORT]) -> None:
        num = UINT(len(viewports))
        vp_arr_t = D3D11_VIEWPORT * int(num.value)
        vp_arr = vp_arr_t(*viewports)
        self._invoke("RSSetViewports", num, vp_arr)

    def OMSetRenderTargets(self, rtvs: Sequence[COMPointer], dsv: COMPointer | None) -> None:
        num = UINT(len(rtvs))
        if int(num.value) == 0:
            self._invoke("OMSetRenderTargets", num, ct.POINTER(ct.c_void_p)(), ct.c_void_p(0))
            return

        arr_t = ct.c_void_p * int(num.value)
        arr = arr_t(*[ct.c_void_p(_ptr_val(r)) for r in rtvs])
        arr_ptr = ct.cast(arr, ct.POINTER(ct.c_void_p))
        dsv_ptr = ct.c_void_p(_ptr_val(dsv))
        self._invoke("OMSetRenderTargets", num, arr_ptr, dsv_ptr)

    def ClearRenderTargetView(self, rtv: COMPointer, color_rgba: tuple[float, float, float, float]) -> None:
        print(f"DEBUG: ClearRenderTargetView rtv={rtv}")
        color_t = FLOAT * 4
        col = color_t(*[float(c) for c in color_rgba])
        # Cast array to proper pointer type for COM invocation
        self._invoke("ClearRenderTargetView", ct.c_void_p(_ptr_val(rtv)), ct.cast(col, ct.POINTER(FLOAT)))

    def VSSetShader(self, shader: ID3D11VertexShader | None) -> None:
        self._invoke("VSSetShader", ct.c_void_p(_ptr_val(shader)), ct.c_void_p(0), UINT(0))

    def PSSetShader(self, shader: ID3D11PixelShader | None) -> None:
        self._invoke("PSSetShader", ct.c_void_p(_ptr_val(shader)), ct.c_void_p(0), UINT(0))

    def GSSetShader(self, shader: ID3D11GeometryShader | None) -> None:
        self._invoke("GSSetShader", ct.c_void_p(_ptr_val(shader)), ct.c_void_p(0), UINT(0))

    def HSSetShader(self, shader: ID3D11HullShader | None) -> None:
        self._invoke("HSSetShader", ct.c_void_p(_ptr_val(shader)), ct.c_void_p(0), UINT(0))

    def DSSetShader(self, shader: ID3D11DomainShader | None) -> None:
        self._invoke("DSSetShader", ct.c_void_p(_ptr_val(shader)), ct.c_void_p(0), UINT(0))

    def IASetInputLayout(self, layout: ID3D11InputLayout | None) -> None:
        self._invoke("IASetInputLayout", ct.c_void_p(_ptr_val(layout)))

    def IASetIndexBuffer(self, buffer: ID3D11Buffer | None, fmt_uint: int, offset_bytes: int) -> None:
        self._invoke("IASetIndexBuffer", ct.c_void_p(_ptr_val(buffer)), UINT(int(fmt_uint)), UINT(int(offset_bytes)))

    def VSSetConstantBuffers(self, start_slot: int, buffers: Sequence[ID3D11Buffer]) -> None:
        n = len(buffers)
        buf_arr = (ct.c_void_p * n)(*[ct.c_void_p(_ptr_val(b)) for b in buffers])
        self._invoke("VSSetConstantBuffers", UINT(int(start_slot)), UINT(n), buf_arr)

    def IASetVertexBuffers(
        self,
        start_slot: int,
        buffers: Sequence[ID3D11Buffer],
        strides: Sequence[int],
        offsets: Sequence[int],
    ) -> None:
        n = len(buffers)
        buf_arr = (ct.c_void_p * n)(*[ct.c_void_p(_ptr_val(b)) for b in buffers])
        stride_arr = (UINT * n)(*[UINT(int(s)) for s in strides])
        offset_arr = (UINT * n)(*[UINT(int(o)) for o in offsets])
        self._invoke("IASetVertexBuffers", UINT(int(start_slot)), UINT(n), buf_arr, stride_arr, offset_arr)

    def IASetPrimitiveTopology(self, topology: int) -> None:
        self._invoke("IASetPrimitiveTopology", UINT(int(topology)))

    def DrawIndexed(self, index_count: int, start_index: int, base_vertex: int) -> None:
        self._invoke("DrawIndexed", UINT(int(index_count)), UINT(int(start_index)), INT(int(base_vertex)))

    def Draw(self, vertex_count: int, start_vertex: int) -> None:
        self._invoke("Draw", UINT(int(vertex_count)), UINT(int(start_vertex)))

    def DrawIndexedInstanced(
        self,
        index_count: int,
        instance_count: int,
        start_index: int,
        base_vertex: int,
        start_instance: int,
    ) -> None:
        self._invoke(
            "DrawIndexedInstanced",
            UINT(int(index_count)),
            UINT(int(instance_count)),
            UINT(int(start_index)),
            INT(int(base_vertex)),
            UINT(int(start_instance)),
        )

    def DrawInstanced(self, vertex_count: int, instance_count: int, start_vertex: int, start_instance: int) -> None:
        self._invoke(
            "DrawInstanced",
            UINT(int(vertex_count)),
            UINT(int(instance_count)),
            UINT(int(start_vertex)),
            UINT(int(start_instance)),
        )


try:
    _d3d11 = load_library("d3d11")
except WindowsLibraryError:
    _d3d11 = None


@runtime_checkable
class _D3D11CreateDeviceProto(Protocol):
    def __call__(
        self,
        pAdapter: ct.c_void_p,
        DriverType: UINT,
        Software: ct.c_void_p,
        Flags: UINT,
        pFeatureLevels: Any,
        FeatureLevels: UINT,
        SDKVersion: UINT,
        ppDevice: Any,
        pFeatureLevel: Any,
        ppImmediateContext: Any,
    ) -> HRESULT: ...


_D3D11CreateDevice: _D3D11CreateDeviceProto | None = None

if _d3d11 is not None:
    _D3D11CreateDevice = ct.WINFUNCTYPE(
        HRESULT,
        ct.c_void_p,  # pAdapter (IDXGIAdapter*)
        UINT,  # DriverType (D3D_DRIVER_TYPE)
        ct.c_void_p,  # Software (HMODULE)
        UINT,  # Flags
        ct.POINTER(UINT),  # pFeatureLevels
        UINT,  # FeatureLevels
        UINT,  # SDKVersion
        ct.POINTER(ct.c_void_p),  # ppDevice
        ct.POINTER(UINT),  # pFeatureLevel
        ct.POINTER(ct.c_void_p),  # ppImmediateContext
    )(("D3D11CreateDevice", _d3d11))


@runtime_checkable
class _D3D11CreateDeviceAndSwapChainProto(Protocol):
    def __call__(
        self,
        pAdapter: ct.c_void_p,
        DriverType: UINT,
        Software: ct.c_void_p,
        Flags: UINT,
        pFeatureLevels: Any,
        FeatureLevels: UINT,
        SDKVersion: UINT,
        pSwapChainDesc: Any,
        ppSwapChain: Any,
        ppDevice: Any,
        pFeatureLevel: Any,
        ppImmediateContext: Any,
    ) -> HRESULT: ...


_D3D11CreateDeviceAndSwapChain: _D3D11CreateDeviceAndSwapChainProto | None = None

if _d3d11 is not None:
    _D3D11CreateDeviceAndSwapChain = ct.WINFUNCTYPE(
        HRESULT,
        ct.c_void_p,  # pAdapter
        UINT,  # DriverType
        ct.c_void_p,  # Software
        UINT,  # Flags
        ct.POINTER(UINT),  # pFeatureLevels
        UINT,  # FeatureLevels
        UINT,  # SDKVersion
        ct.c_void_p,  # pSwapChainDesc (DXGI_SWAP_CHAIN_DESC*)
        ct.POINTER(ct.c_void_p),  # ppSwapChain
        ct.POINTER(ct.c_void_p),  # ppDevice
        ct.POINTER(UINT),  # pFeatureLevel
        ct.POINTER(ct.c_void_p),  # ppImmediateContext
    )(("D3D11CreateDeviceAndSwapChain", _d3d11))


def D3D11CreateDeviceAndSwapChain(
    adapter: COMPointer | None,
    driver_type: int,
    software: COMPointer | None,
    flags: int,
    feature_levels: Sequence[int],
    sdk_version: int,
    swap_chain_desc: ct.c_void_p,
) -> tuple[int, ct.c_void_p, ID3D11Device, D3D_FEATURE_LEVEL, ID3D11DeviceContext]:
    """Full D3D11 device + swap chain creation."""
    ensure_windows()
    if _D3D11CreateDeviceAndSwapChain is None:
        raise WindowsLibraryError("d3d11.dll is not available")

    levels = (UINT * len(feature_levels))(*[UINT(int(level)) for level in feature_levels])
    pp_swap = ct.c_void_p()
    pp_dev = ct.c_void_p()
    pp_ctx = ct.c_void_p()
    out_level = UINT(0)

    adapter_ptr = _as_cvoidp(adapter)
    software_ptr = _as_cvoidp(software)

    hr: int = int(
        _D3D11CreateDeviceAndSwapChain(
            adapter_ptr,
            UINT(driver_type),
            software_ptr,
            UINT(flags),
            levels,
            UINT(len(feature_levels)),
            UINT(sdk_version),
            swap_chain_desc,
            ct.byref(pp_swap),
            ct.byref(pp_dev),
            ct.byref(out_level),
            ct.byref(pp_ctx),
        )
    )

    dev = ID3D11Device()
    dev.assign(pp_dev)

    ctx = ID3D11DeviceContext()
    ctx.assign(pp_ctx)

    return hr, pp_swap, dev, D3D_FEATURE_LEVEL(int(out_level.value)), ctx


def D3D11CreateDevice(
    adapter: COMPointer | None,
    driver_type: int,
    software: COMPointer | None,
    flags: int,
    feature_levels: Sequence[int],
    sdk_version: int,
) -> tuple[int, ID3D11Device, D3D_FEATURE_LEVEL, ID3D11DeviceContext]:
    ensure_windows()
    if _D3D11CreateDevice is None:
        raise WindowsLibraryError("d3d11.dll is not available")

    levels = (UINT * len(feature_levels))(*[UINT(int(level)) for level in feature_levels])
    pp_dev = ct.c_void_p()
    pp_ctx = ct.c_void_p()
    out_level = UINT(0)

    adapter_ptr = _as_cvoidp(adapter)
    software_ptr = _as_cvoidp(software)

    hr: int = int(
        _D3D11CreateDevice(
            adapter_ptr,
            UINT(int(driver_type)),
            software_ptr,
            UINT(int(flags)),
            levels,
            UINT(len(feature_levels)),
            UINT(int(sdk_version)),
            ct.byref(pp_dev),
            ct.byref(out_level),
            ct.byref(pp_ctx),
        )
    )

    dev = ID3D11Device()
    dev.assign(pp_dev)

    ctx = ID3D11DeviceContext()
    ctx.assign(pp_ctx)

    return hr, dev, D3D_FEATURE_LEVEL(int(out_level.value)), ctx


# Convenience wrapper to satisfy __all__ export (missing feature)
def IASetIndexBuffer(
    ctx: ID3D11DeviceContext,
    buffer: ID3D11Buffer | None,
    fmt_uint: int,
    offset_bytes: int,
) -> None:
    """Module-level helper that forwards to ``ID3D11DeviceContext::IASetIndexBuffer``."""
    ctx.IASetIndexBuffer(buffer, fmt_uint, offset_bytes)


def IASetInputLayout(
    ctx: ID3D11DeviceContext,
    layout: ID3D11InputLayout | None,
) -> None:
    """Module-level helper that forwards to ``ID3D11DeviceContext::IASetInputLayout``."""
    ctx.IASetInputLayout(layout)


__all__ = [
    # Interfaces
    "ID3D11Device",
    "ID3D11DeviceContext",
    "ID3D11Buffer",
    "ID3D11Texture2D",
    "ID3D11RenderTargetView",
    "ID3D11InputLayout",
    "ID3D11SamplerState",
    "ID3D11ShaderResourceView",
    "ID3D11Query",
    "ID3D11RasterizerState",
    "ID3D11DepthStencilState",
    "ID3D11BlendState",
    "ID3D11VertexShader",
    "ID3D11PixelShader",
    "ID3D11GeometryShader",
    "ID3D11HullShader",
    "ID3D11DomainShader",
    "ID3D11ComputeShader",
    # Structs
    "D3D11_BUFFER_DESC",
    "D3D11_SUBRESOURCE_DATA",
    "D3D11_MAPPED_SUBRESOURCE",
    "D3D11_VIEWPORT",
    "D3D11_TEX2D_RTV",
    "D3D11_RENDER_TARGET_VIEW_DESC",
    "D3D11_TEXTURE2D_DESC",
    "D3D11_INPUT_ELEMENT_DESC",
    "D3D11_SAMPLER_DESC",
    "D3D11_QUERY_DESC",
    "D3D11_DEPTH_STENCILOP_DESC",
    "D3D11_DEPTH_STENCIL_DESC",
    "D3D11_RASTERIZER_DESC",
    "D3D11_RENDER_TARGET_BLEND_DESC",
    "D3D11_BLEND_DESC",
    "D3D11_TEX2D_SRV",
    "D3D11_SHADER_RESOURCE_VIEW_DESC",
    # Constants / enums
    "D3D11_SDK_VERSION",
    "D3D11_CREATE_DEVICE_BGRA_SUPPORT",
    "D3D11_BIND_VERTEX_BUFFER",
    "D3D11_BIND_INDEX_BUFFER",
    "D3D11_BIND_CONSTANT_BUFFER",
    "D3D11_BIND_SHADER_RESOURCE",
    "D3D11_BIND_STREAM_OUTPUT",
    "D3D11_BIND_RENDER_TARGET",
    "D3D11_BIND_DEPTH_STENCIL",
    "D3D11_BIND_UNORDERED_ACCESS",
    "D3D11_USAGE_DEFAULT",
    "D3D11_USAGE_IMMUTABLE",
    "D3D11_USAGE_DYNAMIC",
    "D3D11_USAGE_STAGING",
    "D3D11_CPU_ACCESS_WRITE",
    "D3D11_INPUT_PER_VERTEX_DATA",
    "D3D11_INPUT_PER_INSTANCE_DATA",
    "D3D11_RTV_DIMENSION_TEXTURE2D",
    "D3D11_SRV_DIMENSION_TEXTURE2D",
    "D3D11_FILTER_MIN_MAG_MIP_LINEAR",
    "D3D11_TEXTURE_ADDRESS_WRAP",
    "D3D11_TEXTURE_ADDRESS_MIRROR",
    "D3D11_TEXTURE_ADDRESS_CLAMP",
    "D3D11_TEXTURE_ADDRESS_BORDER",
    "D3D11_TEXTURE_ADDRESS_MIRROR_ONCE",
    "D3D11_COMPARISON_NEVER",
    "D3D11_COMPARISON_LESS",
    "D3D11_COMPARISON_ALWAYS",
    "D3D11_QUERY_EVENT",
    "D3D11_FILL_SOLID",
    "D3D11_CULL_BACK",
    "D3D11_DEPTH_WRITE_MASK_ZERO",
    "D3D11_DEPTH_WRITE_MASK_ALL",
    "D3D11_BLEND_ZERO",
    "D3D11_BLEND_ONE",
    "D3D11_BLEND_OP_ADD",
    "D3D11_COLOR_WRITE_ENABLE_ALL",
    "D3D11_MAP_WRITE_DISCARD",
    "D3D_PRIMITIVE_TOPOLOGY_TRIANGLELIST",
    # Helpers
    "D3D_DRIVER_TYPE",
    "D3D_FEATURE_LEVEL",
    "D3D11CreateDevice",
    "D3D11CreateDeviceAndSwapChain",
    "IID_ID3D11Texture2D",
    "IASetIndexBuffer",
    "IASetInputLayout",
    "FLOAT",
]
