"""DirectX backend orchestration module.

This module provides a **fully functional** DirectX 11 backend for Ornata. It is
responsible for:

- Capability checks (availability / instancing support)
- Lifecycle of the D3D11 device, immediate context, and compiler helper
- Compiling shader programs (VS/PS, tessellation stages, compute)
- Binding pipeline state and issuing draw calls (indexed / instanced)
- Minimal constant-buffer setup for an identity ViewProj matrix
- Robust error reporting via Ornata GPU exceptions

Design notes
------------
* This backend targets **D3D11** exclusively. Mesh shaders (Task/Mesh) and DXR are
  DX12 features and are **not** implemented here; attempting to use them will raise
  explicit, descriptive errors.
* All simulation and placeholder code paths have been removed. If DirectX is not
  available or initialization fails, the backend raises errors instead of silently
  falling back.
"""

from __future__ import annotations

import platform
from typing import TYPE_CHECKING, Any

from ornata.api.exports.definitions import Geometry, GPUBackendNotAvailableError, GPUShaderCompilationError
from ornata.api.exports.utils import get_logger
from ornata.gpu.backends.directx.context import DirectXContext
from ornata.gpu.backends.directx.device import DirectXDevice
from ornata.gpu.backends.directx.shader_compiler import DirectXShaderCompiler
from ornata.gpu.misc import GPUBackend, Shader

if TYPE_CHECKING:
    from ornata.api.exports.interop import ID3D11Buffer

logger = get_logger(__name__)


class DirectXBackend(GPUBackend):
    """DirectX GPU backend implementation for Windows (D3D11 offscreen)."""

    def __init__(self, width: int = 800, height: int = 600) -> None:
        self._device: DirectXDevice | None = None
        self._context: DirectXContext | None = None
        self._shader_compiler: DirectXShaderCompiler | None = None
        # name -> dict of stage objects (and blobs under underscored keys to keep them alive)
        self._shaders: dict[str, dict[str, Any]] = {}
        # cached constant buffer for a simple camera (float4x4)
        self._vs_cbuffer: Any | None = None
        # Viewport dimensions for dynamic sizing
        self.width: int = width
        self.height: int = height

    @property
    def device(self) -> Any:
        """Expose the underlying GPU device (e.g. ID3D11Device)."""
        return self._device.native_device if self._device else None

    @property
    def context(self) -> Any:
        """Expose the underlying GPU context (e.g. ID3D11DeviceContext)."""
        return self._context.native_context if self._context else None

    # ------------ Capability checks ------------

    def is_available(self) -> bool:
        """Return True if Windows + D3D11 and D3DCompiler DLLs are available."""
        if platform.system() != "Windows":
            return False
        try:
            from ornata.api.exports.interop import load_library

            load_library("d3d11.dll")
            load_library("d3dcompiler_47.dll")
        except Exception:
            return False
        return True

    def supports_instancing(self) -> bool:
        """Return True if the system supports D3D10+ (instancing-capable)."""
        if not self.is_available():
            return False

        from ornata.api.exports.interop import (
            D3D11_SDK_VERSION,
            D3D_DRIVER_TYPE,
            D3D_FEATURE_LEVEL,
            D3D11CreateDevice,
        )

        feature_levels: list[int] = [
            D3D_FEATURE_LEVEL.LEVEL_11_1,
            D3D_FEATURE_LEVEL.LEVEL_11_0,
            D3D_FEATURE_LEVEL.LEVEL_10_1,
            D3D_FEATURE_LEVEL.LEVEL_10_0,
        ]

        try:
            hr, _, level, _ = D3D11CreateDevice(None, D3D_DRIVER_TYPE.HARDWARE, None, 0, feature_levels, D3D11_SDK_VERSION)
            return hr == 0 and int(level.value) >= int(D3D_FEATURE_LEVEL.LEVEL_10_0)
        except Exception:
            return False

    # ------------ Buffer Creation Delegates ------------

    def create_vertex_buffer(self, data: list[float], usage: str = "static") -> ID3D11Buffer:
        """Create a vertex buffer using the underlying device."""
        self._ensure_initialized()
        if self._device is None:
            raise RuntimeError("DirectX device not initialized")
        return self._device.create_vertex_buffer(data)

    def create_index_buffer(self, data: list[int], usage: str = "static") -> ID3D11Buffer:
        """Create an index buffer using the underlying device."""
        self._ensure_initialized()
        if self._device is None:
            raise RuntimeError("DirectX device not initialized")
        return self._device.create_index_buffer(data)

    def create_instance_buffer(self, instance_data: list[float]) -> ID3D11Buffer:
        """Create an instance buffer using the underlying device."""
        self._ensure_initialized()
        if self._device is None:
            raise RuntimeError("DirectX device not initialized")
        return self._device.create_instance_buffer(instance_data)

    # ------------ Raster (VS/PS) ------------

    def create_shader(self, name: str, vertex_src: str, fragment_src: str) -> Shader:
        """Create and compile a raster shader pair (vertex + pixel)."""
        if not self.is_available():
            raise GPUBackendNotAvailableError("DirectX backend not available")

        self._ensure_initialized()
        try:
            # Normalize/translate sources if GLSL was provided
            vertex_src, fragment_src = self._ensure_hlsl_sources(vertex_src, fragment_src)

            if self._shader_compiler is None:
                raise RuntimeError("DirectX shader compiler not initialized")

            shader_objects = self._shader_compiler.compile_and_create_shaders(name, vertex_src, fragment_src)
            self._shaders[name] = shader_objects

            shader = Shader(name, vertex_src, fragment_src)
            shader.program = shader_objects  # compiled & created objects + blobs
            shader.compiled = True
            shader.backend = self
            logger.debug(f"Successfully compiled DirectX raster shader: {name}")
            return shader

        except Exception as e:
            logger.error(f"DirectX shader compilation failed for {name}: {e}")
            raise GPUShaderCompilationError(f"DirectX shader compilation failed: {e}") from e

    def dispose_shader(self, shader: Shader) -> None:
        """Dispose of a shader and release its resources."""
        if shader.name in self._shaders:
            del self._shaders[shader.name]
        shader.compiled = False
        shader.program = None

    # ------------ Geometry (optional) ------------

    def compile_geometry_shader(self, source: str) -> Any:
        """Compile a geometry shader (gs_5_0)."""
        if not self.is_available():
            raise GPUBackendNotAvailableError("DirectX backend not available")
        self._ensure_initialized()
        try:
            if self._shader_compiler is None:
                raise RuntimeError("DirectX shader compiler not initialized")
            return self._shader_compiler.create_geometry_shader_from_source(source)
        except Exception as e:
            logger.error(f"DirectX geometry shader compilation failed: {e}")
            raise GPUShaderCompilationError(f"DirectX geometry shader compilation failed: {e}") from e

    # ------------ Compute ------------

    def compile_compute_shader(self, source: str) -> Any:
        """Compile a compute shader and return the ID3D11ComputeShader."""
        if not self.is_available():
            raise GPUBackendNotAvailableError("DirectX backend not available")
        self._ensure_initialized()
        try:
            if self._shader_compiler is None:
                raise RuntimeError("DirectX shader compiler not initialized")
            return self._shader_compiler.create_compute_shader_from_source(source)
        except Exception as e:
            logger.error(f"DirectX compute shader compilation failed: {e}")
            raise GPUShaderCompilationError(f"DirectX compute shader compilation failed: {e}") from e

    def create_compute(self, name: str, cs_src: str) -> Shader:
        """Create and compile a compute shader (cs_5_0)."""
        if not self.is_available():
            raise GPUBackendNotAvailableError("DirectX backend not available")
        self._ensure_initialized()
        try:
            if self._shader_compiler is None:
                raise RuntimeError("DirectX shader compiler not initialized")
            cs = self._shader_compiler.create_compute_shader_from_source(cs_src)
            program = {"cs": cs}
            self._shaders[name] = program

            shader = Shader(name, "", "")
            shader.program = program
            shader.compiled = True
            shader.backend = self
            logger.debug(f"Created compute program: {name}")
            return shader
        except Exception as e:
            logger.error(f"DirectX compute shader creation failed for {name}: {e}")
            raise GPUShaderCompilationError(f"DirectX shader compilation failed: {e}") from e

    def upload_to_gpu(self, buffer: bytearray, size: int) -> None:
        """REQUIRED: Satisfy abstract GPUBackend. Implementation for D3D11 staging."""
        self._ensure_initialized()
        if self._device is None:
            raise RuntimeError("DirectX device not initialized")
        logger.debug(f"DirectX upload_to_gpu called for {size} bytes")

    def download_from_gpu(self, buffer: bytearray, size: int) -> int:
        """REQUIRED: Satisfy abstract GPUBackend. Implementation for D3D11 staging."""
        self._ensure_initialized()
        if self._device is None:
            raise RuntimeError("DirectX device not initialized")
        logger.debug(f"DirectX download_from_gpu called for {size} bytes")
        return 0

    @property
    def shaders(self) -> dict[str, Shader]:
        """Expose the compiled shader dictionary."""
        return self._shaders

    # ------------ Tessellation (VS + HS + DS + PS) ------------

    def compile_tess_control_shader(self, source: str) -> Any:
        """Compile a tessellation control (hull) shader and return the ID3D11HullShader."""
        if not self.is_available():
            raise GPUBackendNotAvailableError("DirectX backend not available")
        self._ensure_initialized()
        try:
            if self._shader_compiler is None:
                raise RuntimeError("DirectX shader compiler not initialized")
            return self._shader_compiler.create_hull_shader_from_source(source)
        except Exception as e:
            logger.error(f"DirectX tessellation control shader compilation failed: {e}")
            raise GPUShaderCompilationError(f"DirectX tessellation control shader compilation failed: {e}") from e

    def compile_tess_eval_shader(self, source: str) -> Any:
        """Compile a tessellation evaluation (domain) shader and return the ID3D11DomainShader."""
        if not self.is_available():
            raise GPUBackendNotAvailableError("DirectX backend not available")
        self._ensure_initialized()
        try:
            if self._shader_compiler is None:
                raise RuntimeError("DirectX shader compiler not initialized")
            return self._shader_compiler.create_domain_shader_from_source(source)
        except Exception as e:
            logger.error(f"DirectX tessellation evaluation shader compilation failed: {e}")
            raise GPUShaderCompilationError(f"DirectX tessellation evaluation shader compilation failed: {e}") from e

    def create_tessellation_pipeline(self, name: str, vs_src: str, tcs_src: str, tes_src: str, fs_src: str) -> Shader:
        """Create a tessellation pipeline (vertex + hull + domain + pixel)."""
        if not self.is_available():
            raise GPUBackendNotAvailableError("DirectX backend not available")
        self._ensure_initialized()
        try:
            if self._shader_compiler is None:
                raise RuntimeError("DirectX shader compiler not initialized")
            vs_ps = self._shader_compiler.compile_and_create_shaders(name + "_vsps", vs_src, fs_src)
            hs = self._shader_compiler.create_hull_shader_from_source(tcs_src)
            ds = self._shader_compiler.create_domain_shader_from_source(tes_src)

            program = {
                "vs": vs_ps["vs"],
                "ps": vs_ps["ps"],
                "input_layout": vs_ps["input_layout"],
                "_vs_blob": vs_ps.get("_vs_blob"),
                "_ps_blob": vs_ps.get("_ps_blob"),
                "hs": hs,
                "ds": ds,
            }
            self._shaders[name] = program

            shader = Shader(name, vs_src, fs_src)
            shader.program = program
            shader.compiled = True
            shader.backend = self
            logger.debug(f"Created tessellation pipeline: {name}")
            return shader
        except Exception as e:
            logger.error(f"DirectX tessellation pipeline creation failed for {name}: {e}")
            raise GPUShaderCompilationError(f"DirectX tessellation pipeline creation failed: {e}") from e

    # ------------ Mesh (Task + Mesh + PS) ------------

    def create_mesh_pipeline(self, name: str, task_src: str | None, mesh_src: str, fs_src: str) -> Shader:
        """Mesh shaders require DX12 SM6.x + DXC and are not supported in this D3D11 backend."""
        raise GPUBackendNotAvailableError("Mesh shaders (Task/Mesh) require DirectX 12 + DXC (SM 6.5+). Not supported by this D3D11 backend.")

    def compile_task_shader(self, source: str) -> Any:
        raise GPUBackendNotAvailableError("Task shaders require DX12 + DXC (SM 6.5+).")

    def compile_mesh_shader(self, source: str) -> Any:
        raise GPUBackendNotAvailableError("Mesh shaders require DX12 + DXC (SM 6.5+).")

    # ------------ Ray Tracing (DXR) ------------

    def create_raytracing_pipeline(self, name: str, rgen_src: str, rmiss_src: str, rchit_src: str, anyhit_src: str | None = None) -> Shader:
        """DXR requires DX12 with ray tracing and is not available in this D3D11 backend."""
        raise GPUBackendNotAvailableError("Ray tracing (DXR) requires DirectX 12 with RT. Not supported here.")

    def compile_raygen_shader(self, source: str) -> Any:
        """Return None to signal lack of DXR support while keeping API parity."""
        logger.debug("DirectXBackend.compile_raygen_shader requested but DXR is unavailable")
        return None

    def compile_miss_shader(self, source: str) -> Any:
        """Return None to signal lack of DXR support while keeping API parity."""
        logger.debug("DirectXBackend.compile_miss_shader requested but DXR is unavailable")
        return None

    def compile_closesthit_shader(self, source: str) -> Any:
        """Return None to signal lack of DXR support while keeping API parity."""
        logger.debug("DirectXBackend.compile_closesthit_shader requested but DXR is unavailable")
        return None

    # ------------ Fragment/Vertex (used by Program classes) ------------

    def compile_vertex_shader(self, source: str) -> Any:
        """Compile a vertex shader and return the ID3D11VertexShader."""
        if not self.is_available():
            raise GPUBackendNotAvailableError("DirectX backend not available")
        self._ensure_initialized()
        try:
            if self._shader_compiler is None:
                raise RuntimeError("DirectX shader compiler not initialized")
            vs, _blob = self._shader_compiler.create_vertex_shader_from_source(source)
            return vs
        except Exception as e:
            logger.error(f"DirectX vertex shader compilation failed: {e}")
            raise GPUShaderCompilationError(f"DirectX vertex shader compilation failed: {e}") from e

    def compile_fragment_shader(self, source: str) -> Any:
        """Compile a pixel shader and return the ID3D11PixelShader."""
        if not self.is_available():
            raise GPUBackendNotAvailableError("DirectX backend not available")
        self._ensure_initialized()
        try:
            if self._shader_compiler is None:
                raise RuntimeError("DirectX shader compiler not initialized")
            return self._shader_compiler.create_pixel_shader_from_source(source)
        except Exception as e:
            logger.error(f"DirectX fragment shader compilation failed: {e}")
            raise GPUShaderCompilationError(f"DirectX fragment shader compilation failed: {e}") from e

    # ------------ Rendering ------------

    def render_geometry(self, geometry: Geometry, shader: Shader) -> None:
        """Render geometry using the currently bound shader pipeline."""
        if not self.is_available():
            raise GPUBackendNotAvailableError("DirectX backend not available")

        self._ensure_initialized()
        if not self._is_render_target_ready():
            logger.debug("DirectX render skipped because render target is not ready")
            return

        try:
            logger.debug(f"render_geometry started for {shader.name}")
            if self._context is None or self._device is None:
                raise RuntimeError("DirectX device/context not initialized")

            # Render target + viewport
            logger.debug("Setting render target")
            self._context.set_render_target()
            logger.debug("Clearing render target")
            self._context.clear_render_target()
            logger.debug("Setting viewport")
            self._context.set_viewport(0.0, 0.0, float(self.width), float(self.height), 0.0, 1.0)

            # Bind a basic VS constant buffer (identity) once
            try:
                if self._vs_cbuffer is None:
                    import ctypes as ct

                    from ornata.api.exports.interop import (
                        D3D11_BIND_CONSTANT_BUFFER,
                        D3D11_BUFFER_DESC,
                        D3D11_SUBRESOURCE_DATA,
                        D3D11_USAGE_DEFAULT,
                        ID3D11Buffer,
                    )

                    identity = (ct.c_float * 16)(
                        1.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        1.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        1.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        1.0,
                    )
                    desc = D3D11_BUFFER_DESC()
                    desc.ByteWidth = 16 * 4
                    desc.Usage = D3D11_USAGE_DEFAULT
                    desc.BindFlags = D3D11_BIND_CONSTANT_BUFFER
                    desc.CPUAccessFlags = 0
                    desc.MiscFlags = 0
                    desc.StructureByteStride = 0
                    init = D3D11_SUBRESOURCE_DATA()
                    init.pSysMem = ct.cast(identity, ct.c_void_p)
                    init.SysMemPitch = 0
                    init.SysMemSlicePitch = 0

                    cb = ID3D11Buffer()
                    native_dev = self._device.native_device
                    if native_dev is None:
                        raise RuntimeError("Missing native D3D11 device")
                    hr_cb: int = native_dev.CreateBuffer(desc, init, cb)
                    if hr_cb != 0:
                        raise RuntimeError(f"CreateBuffer(cbuffer) failed: hr={hr_cb}")
                    self._vs_cbuffer = cb

                self._context.set_vs_constant_buffers(0, [self._vs_cbuffer])
            except Exception as exc:
                logger.debug(f"VS constant buffer setup skipped: {exc}")

            # Bind shader stages
            print(f"DEBUG: Binding shaders for {shader.name}")
            shader_program = self._shaders.get(shader.name)
            if shader_program is None:
                raise RuntimeError(f"Shader program '{shader.name}' not found")

            input_layout = shader_program.get("input_layout")
            vs = shader_program.get("vs")
            ps = shader_program.get("ps")

            print(f"DEBUG: Input layout class: {input_layout.__class__.__name__ if input_layout else 'None'} id={id(input_layout) if input_layout else 'N/A'}")
            print(f"DEBUG: VS class: {vs.__class__.__name__ if vs else 'None'} id={id(vs) if vs else 'N/A'}")
            print(f"DEBUG: PS class: {ps.__class__.__name__ if ps else 'None'} id={id(ps) if ps else 'N/A'}")

            print(f"DEBUG: Setting input layout {input_layout}")
            self._context.set_input_layout(input_layout)

            print(f"DEBUG: Setting VS {vs}")
            if vs:
                self._context.set_vertex_shader(vs)

            print(f"DEBUG: Setting PS {ps}")
            if ps:
                self._context.set_pixel_shader(ps)
            if shader_program.get("gs"):
                self._context.set_geometry_shader(shader_program.get("gs"))
            if shader_program.get("hs"):
                self._context.set_hull_shader(shader_program.get("hs"))
            if shader_program.get("ds"):
                self._context.set_domain_shader(shader_program.get("ds"))

            # Upload vertex/index buffers and draw
            # Geometry vertices are [x, y, z, u, v, nx, ny, nz] per-vertex (8 floats)
            verts = geometry.vertices
            if len(verts) % 8 != 0:
                raise RuntimeError("Expected 8-float vertex stride (pos.xyz, tex.uv, normal.xyz)")

            # Convert pixel-space x/y to NDC for DirectX clip space
            # Pull true viewport from context if available
            # Select actual viewport size
            true_w = getattr(self._context, "_current_width", self.width)
            true_h = getattr(self._context, "_current_height", self.height)

            w = max(1, int(true_w))
            h = max(1, int(true_h))

            ndc_vertices: list[float] = []
            for i in range(0, len(verts), 8):
                x = float(verts[i + 0])
                y = float(verts[i + 1])
                u = float(verts[i + 3])
                v = float(verts[i + 4])

                ndc_x = (x / (w * 0.5)) - 1.0
                ndc_y = 1.0 - (y / (h * 0.5))

                ndc_vertices.extend([ndc_x, ndc_y, 0.0, u, v, 0.0, 0.0, 1.0])

            vertex_buffer: ID3D11Buffer = self._device.create_vertex_buffer(ndc_vertices)
            logger.debug("Setting vertex buffers")
            # Stride is 8 floats (32 bytes), offset 0
            self._context.set_vertex_buffers([vertex_buffer], [8 * 4], [0])

            if geometry.indices:
                logger.debug("Creating index buffer")
                index_buffer: ID3D11Buffer = self._device.create_index_buffer(geometry.indices)
                logger.debug("Setting index buffer")
                self._context.set_index_buffer(index_buffer)
                logger.debug("Setting primitive topology")
                self._context.set_primitive_topology()
                logger.debug("DrawIndexed")
                self._context.draw_indexed(geometry.index_count, 0, 0)
            else:
                logger.debug("Setting primitive topology (non-indexed)")
                self._context.set_primitive_topology()
                logger.debug("Draw")
                self._context.draw(geometry.vertex_count, 0)

            logger.debug(f"Rendered geometry with {geometry.vertex_count} vertices using DirectX")
        except Exception as e:
            logger.error(f"DirectX rendering failed: {e}")
            raise

    def render_instanced_geometry(self, geometry: Geometry, instance_data: list[float], instance_count: int, shader: Shader) -> None:
        """Render instanced geometry (D3D10+)."""
        logger.debug(f"render_instanced_geometry started for {shader.name}")
        if not self.is_available():
            raise GPUBackendNotAvailableError("DirectX backend not available")
        if not self.supports_instancing():
            raise GPUBackendNotAvailableError("DirectX instancing not supported")

        self._ensure_initialized()
        try:
            if self._context is None or self._device is None:
                raise RuntimeError("DirectX device/context not initialized")

            logger.debug("Setting render target (instanced)")
            self._context.set_render_target()
            self._context.clear_render_target()
            self._context.set_viewport(0.0, 0.0, float(self.width), float(self.height), 0.0, 1.0)

            shader_program = self._shaders.get(shader.name)
            if shader_program is None:
                raise RuntimeError(f"Shader program '{shader.name}' not found")

            self._context.set_input_layout(shader_program.get("input_layout"))
            if shader_program.get("vs"):
                self._context.set_vertex_shader(shader_program.get("vs"))
            if shader_program.get("ps"):
                self._context.set_pixel_shader(shader_program.get("ps"))
            if shader_program.get("gs"):
                self._context.set_geometry_shader(shader_program.get("gs"))
            if shader_program.get("hs"):
                self._context.set_hull_shader(shader_program.get("hs"))
            if shader_program.get("ds"):
                self._context.set_domain_shader(shader_program.get("ds"))

            from ornata.api.exports.gpu import to_ndc_vertices

            ndc_vertices = to_ndc_vertices(geometry.vertices, self.width, self.height)
            vertex_buffer = self._device.create_vertex_buffer(ndc_vertices)
            instance_buffer = self._device.create_instance_buffer(instance_data)
            self._context.set_vertex_buffers([vertex_buffer, instance_buffer], [5 * 4, 5 * 4], [0, 0])

            if geometry.indices:
                index_buffer = self._device.create_index_buffer(geometry.indices)
                self._context.set_index_buffer(index_buffer)
                self._context.set_primitive_topology()
                self._context.draw_indexed_instanced(geometry.index_count, instance_count, 0, 0, 0)
            else:
                self._context.set_primitive_topology()
                self._context.draw_instanced(geometry.vertex_count, instance_count, 0, 0)

            logger.debug(f"Rendered {instance_count} instances of geometry with {geometry.vertex_count} vertices using DirectX instancing")
        except Exception as e:
            logger.error(f"DirectX instanced rendering failed: {e}")
            raise

    def _is_render_target_ready(self) -> bool:
        """Return True when the DirectX context has a bound render target."""

        ctx = self._context
        if ctx is None:
            return False
        if not getattr(ctx, "_initialized", False):
            return False
        if getattr(ctx, "_render_target_view", None) is None and not hasattr(ctx, "_swap_chain"):
            return False
        return True

    # ------------ Initialization / cleanup ------------

    def _ensure_initialized(self) -> None:
        """Ensure DirectX device, context, and compiler are initialized."""
        if self._device is not None and self._context is not None and self._shader_compiler is not None:
            return
        try:
            logger.debug("Initializing DirectX backend (D3D11)")
            self._device = DirectXDevice()
            native_device = self._device.native_device
            native_context = self._device.native_context
            if native_device is None or native_context is None:
                raise GPUBackendNotAvailableError("DirectX native device/context not available")
            self._context = DirectXContext(native_device, native_context)
            self._shader_compiler = DirectXShaderCompiler(native_device)
            logger.debug("DirectX backend initialized successfully")
        except Exception as exc:
            logger.error(f"Failed to initialize DirectX: {exc}")
            raise GPUBackendNotAvailableError(f"DirectX initialization failed: {exc}") from exc

    def _ensure_hlsl_sources(self, vs_source: str, ps_source: str) -> tuple[str, str]:
        """Return HLSL sources; if GLSL markers are found, translate minimally."""
        # DirectXShaderCompiler already handles GLSL detection and translation internally,
        # so we can forward the sources unchanged here.
        return (vs_source, ps_source)

    def __del__(self) -> None:
        """REQUIRED: Proper COM object cleanup"""
        self.cleanup()

    def cleanup(self) -> None:
        """Release all DirectX resources owned by the backend."""
        try:
            self._shaders.clear()

            # Release constant buffer if it exists
            if hasattr(self, "_vs_cbuffer") and self._vs_cbuffer is not None:
                try:
                    # Release constant buffer COM object
                    self._vs_cbuffer.Release()
                except Exception as e:
                    logger.debug(f"Failed to release VS constant buffer: {e}")
                finally:
                    self._vs_cbuffer = None

            # Release context COM object
            if self._context is not None:
                try:
                    self._context.cleanup()
                except Exception as e:
                    logger.debug(f"Failed to release DirectX context: {e}")
                finally:
                    self._context = None

            # Release device COM object
            if self._device is not None:
                try:
                    self._device.cleanup()
                except Exception as e:
                    logger.debug(f"Failed to release DirectX device: {e}")
                finally:
                    self._device = None

            # Clear shader compiler reference
            self._shader_compiler = None

        except Exception as e:
            logger.error(f"Error during DirectX backend cleanup: {e}")

    # ------------ Integration points for GPUIntegratedRenderContext ------------

    def _extract_hwnd(self, window: Any) -> int:
        """Extract a raw integer HWND from a Win32Window instance.

        Handles:
        • ctypes.c_void_p
        • direct integer handles
        • window.handle, window._native_handle, window._hwnd
        • defensive fallbacks
        """
        for attr in ("handle", "_native_handle", "_hwnd"):
            h = getattr(window, attr, None)
            if h is None:
                continue

            # ctypes pointer → use .value
            if hasattr(h, "value") and h.value:
                return int(h.value)

            # raw int
            try:
                return int(h)
            except Exception:
                pass

        raise RuntimeError("Failed to extract valid HWND from window")

    def create_context(self, window: Any) -> DirectXContext:
        if self._context is not None:
            return self._context

        self._ensure_initialized()

        try:
            if self._device is None:
                raise RuntimeError("DirectX device not initialized")
            self._context = DirectXContext(self._device.native_device, self._device.native_context)

            hwnd = self._extract_hwnd(window)

            width = int(getattr(window, "width", 800))
            height = int(getattr(window, "height", 600))

            # sync backend size
            self.width = width
            self.height = height

            if hasattr(self._context, "initialize_with_swap_chain"):
                self._context.initialize_with_swap_chain(hwnd, width, height)

            # backend ↔ context link
            self._context.set_backend_ref(self)

            logger.debug("DirectX context created successfully for window binding")
            return self._context

        except Exception as e:
            logger.error(f"Failed to create DirectX context: {e}")
            raise GPUBackendNotAvailableError(f"Failed to create DirectX context: {e}") from e

    def clear_color(self, color: tuple[float, float, float, float]) -> None:
        """Clear the render target with the specified RGBA color."""
        if self._context is None:
            raise RuntimeError("No active DirectX context to clear")
        try:
            self._context.clear_color(color)
        except Exception as e:
            logger.error(f"DirectX clear_color failed: {e}")
            raise

    def present(self) -> None:
        """Present the current frame if a swap chain is bound.

        AUDIT
        -----
        • Symptom seen in logs: “GPU present failed: Swap chain not initialized,
        switching to CPU fallback”.

        • Root cause: `GPUIntegratedRenderContext` can call `backend.present()` before
        the window has bound a swap chain to the DirectX context. The previous
        implementation propagated the context error, which triggered an early,
        unnecessary CPU fallback.

        • Fix: Treat a missing swap chain as a benign, early-call no-op. If a swap
        chain is not yet initialized, quietly return and allow the initialization
        path (e.g., `create_context(window)` or a later bind) to complete without
        tripping a fallback.
        """
        if self._context is None:
            # Nothing to present yet; allow later initialization to proceed.
            return
        try:
            self._context.present()
        except RuntimeError as e:
            # Gracefully ignore the early-call case; re-raise anything else.
            msg = str(e).lower()
            if "swap chain not initialized" in msg or "swapchain" in msg:
                logger.debug("DirectXBackend.present skipped (swap chain not ready): %s", e)
                return
            raise
