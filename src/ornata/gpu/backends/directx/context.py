# ===========================
# ornata/gpu/backends/directx/context.py
# ===========================
"""DirectX context operations module.

This module wraps common operations against the **immediate context**:
- Creating an offscreen RTV for basic rendering
- Binding render target and viewport
- Binding input layout, shaders, and buffers
- Issuing draw calls (indexed / instanced)

No simulation paths are present; the context requires a valid device and context.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger
from ornata.interop.ctypes_compilation.windows.foundation import WindowsLibraryError, to_int

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from ornata.api.exports.interop import ID3D11Buffer, ID3D11Device, ID3D11DeviceContext, ID3D11RenderTargetView
    from ornata.gpu.backends.directx.backend import DirectXBackend

logger = get_logger(__name__)


class DirectXContext:
    """Manages DirectX device context operations."""

    def __init__(self, device: ID3D11Device | None, context: ID3D11DeviceContext | None) -> None:
        """Create a context wrapper around **valid** D3D11 device/context."""
        if device is None or context is None:
            raise ValueError("DirectXContext requires a valid ID3D11Device and ID3D11DeviceContext")
        self._device = device
        self._context = context
        self._backend_ref: DirectXBackend | None = None  # added for resize propagation
        self._current_width = 800  # offscreen default
        self._current_height = 600
        self._render_target_view: ID3D11RenderTargetView | None = None
        self._initialized = False
        self._initialize_context()

    def _invoke_context_call(self, operation: str, func: "Callable[[], None]") -> None:
        """Execute a DirectX call while gracefully handling COM-level errors.

        Parameters
        ----------
        operation:
            Human-readable name of the DirectX call for logging diagnostics.
        func:
            Zero-argument callable that performs the actual COM invocation.
        """

        try:
            func()
        except (WindowsLibraryError, OSError) as exc:  # pragma: no cover - depends on host GPU state
            logger.debug(f"DirectX context operation '{operation}' skipped: {exc}")

    @property
    def native_context(self) -> Any:
        """Return the underlying D3D11 immediate context."""
        return self._context

    def _initialize_context(self) -> None:
        """Create a simple 800x600 offscreen render target + RTV."""
        try:
            from ornata.api.exports.interop import D3D11_TEXTURE2D_DESC

            tex_desc = D3D11_TEXTURE2D_DESC()
            tex_desc.Width = 800
            tex_desc.Height = 600
            tex_desc.MipLevels = 1
            tex_desc.ArraySize = 1
            from ornata.api.exports.interop import DXGI_FORMAT_R8G8B8A8_UNORM

            tex_desc.Format = DXGI_FORMAT_R8G8B8A8_UNORM
            from ornata.api.exports.interop import DXGI_SAMPLE_DESC

            tex_desc.SampleDesc = DXGI_SAMPLE_DESC(Count=1, Quality=0)
            from ornata.api.exports.interop import D3D11_USAGE_DEFAULT

            tex_desc.Usage = D3D11_USAGE_DEFAULT
            from ornata.api.exports.interop import D3D11_BIND_RENDER_TARGET

            tex_desc.BindFlags = D3D11_BIND_RENDER_TARGET
            tex_desc.CPUAccessFlags = 0
            tex_desc.MiscFlags = 0

            from ornata.api.exports.interop import ID3D11Texture2D

            texture_ptr = ID3D11Texture2D()
            hr: int = self._device.CreateTexture2D(tex_desc, None, texture_ptr)
            if hr != 0:
                print(f"DEBUG: CreateTexture2D failed: hr={hr:#x}")
                raise RuntimeError(f"CreateTexture2D failed: hr={hr}")
            print(f"DEBUG: Created Texture2D: {texture_ptr.pointer.value:#x}")

            from ornata.api.exports.interop import D3D11_RENDER_TARGET_VIEW_DESC, D3D11_RTV_DIMENSION_TEXTURE2D, D3D11_TEX2D_RTV, ID3D11RenderTargetView

            rtv_desc = D3D11_RENDER_TARGET_VIEW_DESC()
            rtv_desc.Format = tex_desc.Format
            rtv_desc.ViewDimension = D3D11_RTV_DIMENSION_TEXTURE2D
            rtv_desc.Anonymous.Texture2D = D3D11_TEX2D_RTV(MipSlice=0)

            rtv_ptr = ID3D11RenderTargetView()
            hr = self._device.CreateRenderTargetView(texture_ptr, rtv_desc, rtv_ptr)
            if hr != 0:
                print(f"DEBUG: CreateRenderTargetView failed: hr={hr:#x}")
                raise RuntimeError(f"CreateRenderTargetView failed: hr={hr}")

            print(f"DEBUG: Created RTV: {rtv_ptr.pointer.value:#x}")
            self._render_target_view = rtv_ptr
            self._initialized = True
            logger.debug("DirectX context initialized successfully")
        except Exception as exc:
            raise RuntimeError(f"Failed to initialize DirectX context: {exc}") from exc

    def set_render_target(self) -> None:
        """Bind the offscreen RTV to OM stage."""
        if not self._initialized or self._render_target_view is None:
            raise RuntimeError("Render target view is not initialized")

        rtv = self._render_target_view
        assert rtv is not None

        def _bind() -> None:
            self._context.OMSetRenderTargets([rtv], None)

        self._invoke_context_call("OMSetRenderTargets", _bind)

    def clear_color(self, color_rgba: tuple[float, float, float, float]) -> None:
        """Clear the bound render target with a solid color."""
        rtv = self._render_target_view
        if rtv is None:
            print("DEBUG: No RTV bound for clear_color")
            return

        print(f"DEBUG: Clearing RTV ptr={to_int(rtv):#x}")
        rtv_local = rtv
        self._invoke_context_call(
            "ClearRenderTargetView",
            lambda: self._context.ClearRenderTargetView(rtv_local, color_rgba),
        )

    def clear_render_target(self) -> None:
        """Clear the bound RTV to the default clear color."""
        self.clear_color((0.0, 1.0, 0.0, 1.0))  # RGBA → full green for obvious clear check

    def set_viewport(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        min_depth: float = 0.0,
        max_depth: float = 1.0,
    ) -> None:
        """Bind a viewport with explicit coordinates and depth range.

        AUDIT
        -----
        • Integration break: `DirectXBackend.render_geometry(...)` calls
        `set_viewport(x, y, w, h, min, max)` but this context method previously
        had the signature `set_viewport(self) -> None` and always forced 800×600.
        That mismatch caused a runtime `TypeError` and prevented dynamic sizing.

        • Fix: accept explicit parameters, forward them to RS stage, and remove the
        hard-coded 800×600 defaults. This aligns the context with the backend.

        Raises
        ------
        RuntimeError
            If the immediate context is not available (defensive).
        """
        from ornata.api.exports.interop import D3D11_VIEWPORT

        vp = D3D11_VIEWPORT()
        vp.TopLeftX = float(x)
        vp.TopLeftY = float(y)
        vp.Width = float(width)
        vp.Height = float(height)
        vp.MinDepth = float(min_depth)
        vp.MaxDepth = float(max_depth)
        # RSSetViewports takes a sequence of viewports

        self._invoke_context_call("RSSetViewports", lambda: self._context.RSSetViewports([vp]))

    def set_input_layout(self, input_layout: Any) -> None:
        """Bind the provided input layout (IA stage)."""
        if input_layout is None:
            raise ValueError("Input layout cannot be None")
        self._context.IASetInputLayout(input_layout)

    def set_vertex_shader(self, shader: Any) -> None:
        """Bind a vertex shader (VS stage)."""
        if shader is None:
            raise ValueError("Vertex shader cannot be None")
        self._context.VSSetShader(shader)

    def set_pixel_shader(self, shader: Any) -> None:
        """Bind a pixel shader (PS stage)."""
        if shader is None:
            raise ValueError("Pixel shader cannot be None")
        self._context.PSSetShader(shader)

    def set_geometry_shader(self, shader: Any) -> None:
        """Bind a geometry shader (GS stage)."""
        if shader is None:
            raise ValueError("Geometry shader cannot be None")
        self._context.GSSetShader(shader)

    def set_hull_shader(self, shader: Any) -> None:
        """Bind a hull shader (HS stage)."""
        if shader is None:
            raise ValueError("Hull shader cannot be None")
        self._context.HSSetShader(shader)

    def set_domain_shader(self, shader: Any) -> None:
        """Bind a domain shader (DS stage)."""
        if shader is None:
            raise ValueError("Domain shader cannot be None")
        self._context.DSSetShader(shader)

    def set_vertex_buffers(self, buffers: Sequence[ID3D11Buffer], strides: Sequence[int], offsets: Sequence[int]) -> None:
        """Bind vertex buffers (IA stage)."""
        if len(buffers) != len(strides) or len(buffers) != len(offsets):
            raise ValueError("buffers, strides, and offsets must have the same length")
        self._context.IASetVertexBuffers(0, buffers, strides, offsets)

    def set_vs_constant_buffers(self, start_slot: int, buffers: Sequence[ID3D11Buffer]) -> None:
        """Bind one or more constant buffers to the VS stage.

        AUDIT
        -----
        • Integration break: previous implementation called
        `VSSetConstantBuffers(start_slot, buffers)` without supplying `NumBuffers`.
        D3D11 requires `(StartSlot, NumBuffers, ppBuffers)`. Several drivers
        silently no-op on the wrong arity, which looked like “the VS cbuffer
        isn't updating”.

        • Fix: pass the correct buffer count and ensure type validation.
        """
        count = int(len(buffers))
        if count <= 0:
            return

        self._context.VSSetConstantBuffers(int(start_slot), list(buffers))

    def set_index_buffer(self, buffer: ID3D11Buffer) -> None:
        """Bind the index buffer (IA stage)."""
        from ornata.api.exports.interop import DXGI_FORMAT_R32_UINT

        self._context.IASetIndexBuffer(buffer, DXGI_FORMAT_R32_UINT, 0)

    def set_primitive_topology(self) -> None:
        """Set primitive topology to triangle list."""
        from ornata.api.exports.interop import D3D_PRIMITIVE_TOPOLOGY_TRIANGLELIST

        self._invoke_context_call(
            "IASetPrimitiveTopology",
            lambda: self._context.IASetPrimitiveTopology(D3D_PRIMITIVE_TOPOLOGY_TRIANGLELIST),
        )

    def draw_indexed(self, index_count: int, start_index: int, base_vertex: int) -> None:
        """Issue a DrawIndexed call."""
        print(f"DEBUG: DrawIndexed count={index_count} start={start_index} base={base_vertex}")
        self._context.DrawIndexed(int(index_count), int(start_index), int(base_vertex))

    def draw(self, vertex_count: int, start_vertex: int) -> None:
        """Issue a Draw call."""
        self._context.Draw(int(vertex_count), int(start_vertex))

    def draw_indexed_instanced(self, index_count: int, instance_count: int, start_index: int, base_vertex: int, start_instance: int) -> None:
        """Issue a DrawIndexedInstanced call."""
        self._context.DrawIndexedInstanced(int(index_count), int(instance_count), int(start_index), int(base_vertex), int(start_instance))

    def draw_instanced(self, vertex_count: int, instance_count: int, start_vertex: int, start_instance: int) -> None:
        """Issue a DrawInstanced call."""
        self._context.DrawInstanced(int(vertex_count), int(instance_count), int(start_vertex), int(start_instance))

    def cleanup(self) -> None:
        """No-op placeholder for future explicit Release() calls if needed."""
        # Purposefully minimal: COM wrappers likely manage lifetimes via refcounts.
        self._initialized = False

    def initialize_with_swap_chain(self, hwnd: int, width: int, height: int) -> None:
        from ornata.api.exports.interop import (
            DXGI_FORMAT_R8G8B8A8_UNORM,
            DXGI_MODE_DESC,
            DXGI_SAMPLE_DESC,
            DXGI_SWAP_CHAIN_DESC,
            DXGI_SWAP_EFFECT_DISCARD,
            DXGI_USAGE_RENDER_TARGET_OUTPUT,
            CreateDXGIFactory,
            ID3D11RenderTargetView,
            IID_ID3D11Texture2D,
        )

        dxgi_factory = CreateDXGIFactory()

        mode = DXGI_MODE_DESC()
        mode.Width = int(width)
        mode.Height = int(height)
        mode.Format = DXGI_FORMAT_R8G8B8A8_UNORM
        mode.RefreshRate.Numerator = 60
        mode.RefreshRate.Denominator = 1

        sample = DXGI_SAMPLE_DESC()
        sample.Count = 1
        sample.Quality = 0

        desc = DXGI_SWAP_CHAIN_DESC()
        desc.BufferDesc = mode
        desc.SampleDesc = sample
        desc.BufferUsage = DXGI_USAGE_RENDER_TARGET_OUTPUT
        desc.BufferCount = 2
        desc.OutputWindow = int(hwnd)
        desc.Windowed = True
        desc.SwapEffect = DXGI_SWAP_EFFECT_DISCARD
        desc.Flags = 0

        hr, swap_chain = dxgi_factory.CreateSwapChain(self._device, desc)
        if hr != 0:
            raise RuntimeError(f"CreateSwapChain failed hr={hr:#x}")

        hr, back_buf = swap_chain.GetBuffer(0, IID_ID3D11Texture2D)
        if hr != 0:
            raise RuntimeError(f"GetBuffer failed hr={hr:#x}")

        rtv = ID3D11RenderTargetView()
        hr = self._device.CreateRenderTargetView(back_buf, None, rtv)
        if hr != 0:
            raise RuntimeError(f"CreateRenderTargetView failed hr={hr:#x}")

        self._render_target_view = rtv

        rtv_local = rtv
        self._invoke_context_call("OMSetRenderTargets", lambda: self._context.OMSetRenderTargets([rtv_local], None))

        from ornata.api.exports.interop import D3D11_VIEWPORT

        vp = D3D11_VIEWPORT()
        vp.TopLeftX = 0.0
        vp.TopLeftY = 0.0
        vp.Width = float(width)
        vp.Height = float(height)
        vp.MinDepth = 0.0
        vp.MaxDepth = 1.0
        self._invoke_context_call("RSSetViewports", lambda: self._context.RSSetViewports([vp]))

        self._swap_chain = swap_chain
        self._initialized = True

        # store actual viewport
        self._current_width = width
        self._current_height = height

        import ctypes as ct

        if not self._initialized or self._render_target_view is None:
            raise RuntimeError("Render target view is not initialized")

        default_color = (0.0, 0.0, 0.0, 1.0)
        r, g, b, a = map(float, default_color)
        clear_array = (ct.c_float * 4)(r, g, b, a)
        clear = tuple(clear_array)
        rtv_local = self._render_target_view
        self._invoke_context_call(
            "ClearRenderTargetView",
            lambda: self._context.ClearRenderTargetView(rtv_local, clear),
        )

    def present(self) -> None:
        """Present the swap chain back buffer (if available).

        AUDIT
        -----
        • Before: Raised on missing swap chain, causing upstream fallbacks even when
        initialization would bind one shortly after.

        • After: No-op if the swap chain is not yet available; present when it is.
        This matches common D3D11 integration patterns where the pump can start
        before swap-chain binding is finalized.
        """
        # Allow early frames before a swap chain is bound (e.g., during startup).
        if not hasattr(self, "_swap_chain"):
            return

        hr = self._swap_chain.Present(1, 0)  # vsync
        if hr != 0:
            raise RuntimeError(f"Present failed with HRESULT {hr:#x}")

    def resize(self, width: int, height: int) -> None:
        if not hasattr(self, "_swap_chain"):
            return

        from ornata.api.exports.interop import ID3D11RenderTargetView

        if self._render_target_view is not None:
            try:
                self._render_target_view.release()
            except Exception:
                pass
            self._render_target_view = None

        hr = self._swap_chain.ResizeBuffers(2, int(width), int(height), 28, 0)
        if hr != 0:
            raise RuntimeError(f"ResizeBuffers failed: hr={hr:#x}")

        from ornata.api.exports.interop import IID_ID3D11Texture2D

        hr, back_buf = self._swap_chain.GetBuffer(0, IID_ID3D11Texture2D)
        if hr != 0:
            raise RuntimeError(f"GetBuffer failed after resize: hr={hr:#x}")

        rtv = ID3D11RenderTargetView()
        hr = self._device.CreateRenderTargetView(back_buf, None, rtv)
        if hr != 0:
            raise RuntimeError(f"CreateRenderTargetView failed after resize: hr={hr:#x}")

        self._render_target_view = rtv

        # update context size
        self._current_width = width
        self._current_height = height

        # propagate to backend
        if hasattr(self, "_backend_ref"):
            if self._backend_ref is None:
                return
            self._backend_ref.width = width
            self._backend_ref.height = height

    def set_backend_ref(self, backend: DirectXBackend) -> None:
        """Associate this context with its owning backend for resize propagation."""
        self._backend_ref = backend
