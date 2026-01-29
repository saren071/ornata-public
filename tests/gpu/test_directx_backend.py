"""Coverage for DirectX GPU backend behavior."""

from __future__ import annotations

from collections.abc import Sequence
from types import SimpleNamespace

import pytest

from ornata.api.exports.definitions import Geometry, GPUBackendNotAvailableError, GPUShaderCompilationError
from ornata.api.exports.gpu import DirectXBackend, DirectXContext, DirectXDevice
from ornata.api.exports.interop import ID3D11Buffer, ID3D11Device, ID3D11DeviceContext, ID3D11RenderTargetView


class StubDirectXDevice(DirectXDevice):
    """Deterministic DirectXDevice stand-in for backend tests."""

    instances: list[StubDirectXDevice] = []

    def __init__(self) -> None:
        # Intentionally bypass real device initialization
        self._device = ID3D11Device()
        self._context = ID3D11DeviceContext()
        self._feature_level = None
        self._buffer_manager = None
        self._initialized = True
        self.vertex_calls: list[list[float]] = []
        self.index_calls: list[list[int]] = []
        self.instance_calls: list[list[float]] = []
        self.cleaned_up = False
        StubDirectXDevice.instances.append(self)

    def create_vertex_buffer(self, vertices: list[float]) -> ID3D11Buffer:
        self.vertex_calls.append(list(vertices))
        return ID3D11Buffer()

    def create_index_buffer(self, indices: list[int]) -> ID3D11Buffer:
        self.index_calls.append(list(indices))
        return ID3D11Buffer()

    def create_instance_buffer(self, instance_data: list[float]) -> ID3D11Buffer:
        self.instance_calls.append(list(instance_data))
        return ID3D11Buffer()

    def cleanup(self) -> None:
        self.cleaned_up = True


class StubDirectXContext(DirectXContext):
    """Simple context mock capturing high-level state changes."""

    instances: list[StubDirectXContext] = []

    def __init__(self, native_device: object, native_context: object) -> None:
        self._device = native_device
        self._context = native_context
        self._initialized = True
        self._render_target_view = ID3D11RenderTargetView()
        self._current_width = 800
        self._current_height = 600
        self.backend = None
        self.calls: list[tuple[str, object]] = []
        self._present_error: RuntimeError | None = None
        StubDirectXContext.instances.append(self)

    def set_backend_ref(self, backend: DirectXBackend) -> None:
        self.backend = backend

    def set_render_target(self) -> None:
        self.calls.append(("set_render_target", None))

    def clear_render_target(self) -> None:
        self.calls.append(("clear_render_target", None))

    def set_viewport(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        min_depth: float = 0.0,
        max_depth: float = 1.0,
    ) -> None:
        self.calls.append(("set_viewport", (x, y, width, height, min_depth, max_depth)))

    def set_input_layout(self, input_layout: object) -> None:
        self.calls.append(("input_layout", input_layout))

    def set_vertex_shader(self, shader: object) -> None:
        self.calls.append(("vs", shader))

    def set_pixel_shader(self, shader: object) -> None:
        self.calls.append(("ps", shader))

    def set_geometry_shader(self, shader: object) -> None:
        self.calls.append(("gs", shader))

    def set_hull_shader(self, shader: object) -> None:
        self.calls.append(("hs", shader))

    def set_domain_shader(self, shader: object) -> None:
        self.calls.append(("ds", shader))

    def set_vertex_buffers(
        self,
        buffers: Sequence[ID3D11Buffer],
        strides: Sequence[int],
        offsets: Sequence[int],
    ) -> None:
        self.calls.append(("vertex_buffers", (list(buffers), list(strides), list(offsets))))

    def set_vs_constant_buffers(self, start_slot: int, buffers: Sequence[ID3D11Buffer]) -> None:
        self.calls.append(("vs_cbuffers", (start_slot, list(buffers))))

    def set_index_buffer(self, buffer: object) -> None:
        self.calls.append(("index_buffer", buffer))

    def set_primitive_topology(self) -> None:
        self.calls.append(("primitive_topology", None))

    def draw_indexed(self, index_count: int, start_index: int, base_vertex: int) -> None:
        self.calls.append(("draw_indexed", (index_count, start_index, base_vertex)))

    def draw(self, vertex_count: int, start_vertex: int) -> None:
        self.calls.append(("draw", (vertex_count, start_vertex)))

    def draw_indexed_instanced(
        self,
        index_count: int,
        instance_count: int,
        start_index: int,
        base_vertex: int,
        start_instance: int,
    ) -> None:
        self.calls.append(
            (
                "draw_indexed_instanced",
                (index_count, instance_count, start_index, base_vertex, start_instance),
            )
        )

    def draw_instanced(self, vertex_count: int, instance_count: int, start_vertex: int, start_instance: int) -> None:
        self.calls.append(("draw_instanced", (vertex_count, instance_count, start_vertex, start_instance)))

    def cleanup(self) -> None:
        self.calls.append(("cleanup", None))

    def present(self) -> None:
        self.calls.append(("present", None))
        if self._present_error is not None:
            raise self._present_error


class StubShaderCompiler:
    """Shader compiler stub recording invocations."""

    def __init__(self, device: object) -> None:
        self.device = device
        self.compiled_pairs: list[tuple[str, str, str]] = []

    def compile_and_create_shaders(self, name: str, vs_src: str, ps_src: str) -> dict[str, object]:
        self.compiled_pairs.append((name, vs_src, ps_src))
        return {
            "vs": f"{name}-vs",
            "ps": f"{name}-ps",
            "input_layout": f"{name}-layout",
        }

    def create_geometry_shader_from_source(self, _: str) -> None:
        raise RuntimeError("geometry failure")

    def create_compute_shader_from_source(self, source: str) -> str:
        return f"compute::{source}"

    def create_hull_shader_from_source(self, _: str) -> None:
        raise RuntimeError("hs failure")

    def create_domain_shader_from_source(self, _: str) -> None:
        raise RuntimeError("ds failure")


def setup_stubbed_backend(monkeypatch: pytest.MonkeyPatch) -> DirectXBackend:
    """Return a DirectXBackend wired to lightweight stub components."""

    backend = DirectXBackend()
    monkeypatch.setattr("ornata.gpu.backends.directx.backend.DirectXDevice", StubDirectXDevice)
    monkeypatch.setattr("ornata.gpu.backends.directx.backend.DirectXContext", StubDirectXContext)
    monkeypatch.setattr("ornata.gpu.backends.directx.backend.DirectXShaderCompiler", StubShaderCompiler)
    return backend


def test_directx_backend_unavailable_on_non_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    """`is_available` should return ``False`` whenever the host is not Windows."""

    backend = DirectXBackend()
    monkeypatch.setattr("ornata.gpu.backends.directx.backend.platform.system", lambda: "Linux")

    assert backend.is_available() is False
    assert backend.supports_instancing() is False


def test_directx_backend_is_available_when_dlls_load(monkeypatch: pytest.MonkeyPatch) -> None:
    """`is_available` should probe the expected D3D DLLs on Windows."""

    loaded: list[str] = []
    backend = DirectXBackend()

    def fake_load_library(name: str) -> None:
        loaded.append(name)

    monkeypatch.setattr("ornata.gpu.backends.directx.backend.platform.system", lambda: "Windows")
    monkeypatch.setattr("ornata.api.exports.interop.load_library", fake_load_library)

    assert backend.is_available() is True
    assert loaded == ["d3d11.dll", "d3dcompiler_47.dll"]


def test_directx_backend_create_shader_requires_available_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    """Shader creation must raise when the backend is not available."""

    backend = DirectXBackend()
    monkeypatch.setattr(backend, "is_available", lambda: False)

    with pytest.raises(GPUBackendNotAvailableError):
        backend.create_shader("demo", "void main() {}", "void main() {}")


def test_directx_device_fallbacks_to_warp(monkeypatch: pytest.MonkeyPatch) -> None:
    """DirectXDevice should retry with the WARP driver when hardware creation fails."""

    calls: list[str] = []
    driver_types = SimpleNamespace(HARDWARE="hardware", WARP="warp")
    feature_levels = SimpleNamespace(LEVEL_11_1=0xB100, LEVEL_11_0=0xB000, LEVEL_10_1=0xA100, LEVEL_10_0=0xA000)

    def fake_create_device(*args: object, **kwargs: object):
        driver = args[1]
        calls.append(str(driver))
        if driver == driver_types.HARDWARE:
            return 1, None, None, None
        return 0, "DEVICE", SimpleNamespace(value=feature_levels.LEVEL_11_1), "CONTEXT"

    class StubBufferManager:
        def __init__(self, device: str) -> None:
            self.device = device

        def create_vertex_buffer(self, data: list[float]) -> tuple[str, list[float]]:
            return ("vertex", data)

        def create_index_buffer(self, data: list[int]) -> tuple[str, list[int]]:
            return ("index", data)

        def create_instance_buffer(self, data: list[float]) -> tuple[str, list[float]]:
            return ("instance", data)

    monkeypatch.setattr("ornata.api.exports.interop.D3D_DRIVER_TYPE", driver_types)
    monkeypatch.setattr("ornata.api.exports.interop.D3D_FEATURE_LEVEL", feature_levels)
    monkeypatch.setattr("ornata.api.exports.interop.D3D11_SDK_VERSION", 123)
    monkeypatch.setattr("ornata.api.exports.interop.D3D11CreateDevice", fake_create_device)
    monkeypatch.setattr("ornata.api.exports.gpu.DirectXBufferManager", StubBufferManager, raising=False)

    device = DirectXDevice()

    assert calls == [driver_types.HARDWARE, driver_types.WARP]
    assert device.native_device == "DEVICE"
    assert device.native_context == "CONTEXT"
    feature_level = device.feature_level
    assert feature_level is not None
    assert feature_level.value == feature_levels.LEVEL_11_1


def test_directx_device_raises_when_all_driver_attempts_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    """Initialization should raise immediately if both hardware and WARP drivers fail."""

    driver_types = SimpleNamespace(HARDWARE="hardware", WARP="warp")
    feature_levels = SimpleNamespace(LEVEL_11_1=0xB100, LEVEL_11_0=0xB000, LEVEL_10_1=0xA100, LEVEL_10_0=0xA000)

    def always_fail(*args: object, **kwargs: object):
        return 1, None, None, None

    monkeypatch.setattr("ornata.api.exports.interop.D3D_DRIVER_TYPE", driver_types)
    monkeypatch.setattr("ornata.api.exports.interop.D3D_FEATURE_LEVEL", feature_levels)
    monkeypatch.setattr("ornata.api.exports.interop.D3D11_SDK_VERSION", 123)
    monkeypatch.setattr("ornata.api.exports.interop.D3D11CreateDevice", always_fail)

    with pytest.raises(RuntimeError):
        DirectXDevice()


def test_directx_backend_creates_and_disposes_shader(monkeypatch: pytest.MonkeyPatch) -> None:
    """Initialization path should wire device/context/compiler and manage shader cache."""

    backend = setup_stubbed_backend(monkeypatch)
    monkeypatch.setattr(backend, "is_available", lambda: True)

    shader = backend.create_shader("demo", "void main(){}", "void main(){}")

    assert shader.compiled is True
    assert shader.program is not None
    assert shader.program.get("vs") == "demo-vs"

    vertices = [0.0] * 8
    backend.create_vertex_buffer(vertices)
    assert isinstance(backend._device, StubDirectXDevice)
    assert backend._device.vertex_calls[0] == vertices

    backend.dispose_shader(shader)
    assert "demo" not in backend.shaders


def test_directx_backend_render_geometry_populates_buffers(monkeypatch: pytest.MonkeyPatch) -> None:
    """render_geometry should upload buffers and issue indexed draws when ready."""

    backend = setup_stubbed_backend(monkeypatch)
    monkeypatch.setattr(backend, "is_available", lambda: True)
    shader = backend.create_shader("pipeline", "vs", "ps")
    backend._vs_cbuffer = object()

    # 3 vertices, stride 8 (x, y, z, u, v, nx, ny, nz)
    vertices = [
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
        50.0,
        10.0,
        0.0,
        1.0,
        1.0,
        0.0,
        0.0,
        1.0,
        100.0,
        20.0,
        0.0,
        0.5,
        0.5,
        0.0,
        0.0,
        1.0,
    ]
    geometry = Geometry(vertices=vertices, indices=[0, 1, 2], vertex_count=3, index_count=3)

    backend.render_geometry(geometry, shader)

    assert isinstance(backend._device, StubDirectXDevice)
    assert len(backend._device.vertex_calls) == 1
    assert isinstance(backend._context, StubDirectXContext)
    assert any(call[0] == "draw_indexed" for call in backend._context.calls)


def test_directx_backend_render_geometry_rejects_invalid_stride(monkeypatch: pytest.MonkeyPatch) -> None:
    """Vertices not matching the required stride should raise immediately."""

    backend = setup_stubbed_backend(monkeypatch)
    monkeypatch.setattr(backend, "is_available", lambda: True)
    shader = backend.create_shader("bad", "vs", "ps")
    backend._vs_cbuffer = object()
    bad_vertices = [0.0, 0.0, 0.0]
    geometry = Geometry(vertices=bad_vertices, indices=[], vertex_count=1, index_count=0)

    with pytest.raises(RuntimeError, match="8-float vertex stride"):
        backend.render_geometry(geometry, shader)


def test_directx_backend_geometry_shader_errors_are_wrapped(monkeypatch: pytest.MonkeyPatch) -> None:
    """Shader compiler failures should surface as GPUShaderCompilationError."""

    backend = setup_stubbed_backend(monkeypatch)
    monkeypatch.setattr(backend, "is_available", lambda: True)
    backend._ensure_initialized()

    with pytest.raises(GPUShaderCompilationError):
        backend.compile_geometry_shader("void main(){}\n")


def test_directx_backend_render_instanced_geometry_requires_instancing(monkeypatch: pytest.MonkeyPatch) -> None:
    """render_instanced_geometry must raise when instancing support is absent."""

    backend = setup_stubbed_backend(monkeypatch)
    monkeypatch.setattr(backend, "is_available", lambda: True)
    monkeypatch.setattr(backend, "supports_instancing", lambda: False)
    shader = backend.create_shader("inst", "vs", "ps")
    backend._vs_cbuffer = object()
    geometry = Geometry(vertices=[0.0] * 8, indices=[], vertex_count=1, index_count=0)

    with pytest.raises(GPUBackendNotAvailableError):
        backend.render_instanced_geometry(geometry, [], 1, shader)


def test_directx_backend_present_gracefully_handles_swap_chain_states() -> None:
    """present should no-op when swap chains are unavailable and re-raise other errors."""

    backend = DirectXBackend()

    benign = StubDirectXContext(object(), object())
    benign._present_error = RuntimeError("swap chain not initialized")
    backend._context = benign
    backend.present()
    assert ("present", None) in benign.calls

    healthy = StubDirectXContext(object(), object())
    backend._context = healthy
    backend.present()
    assert ("present", None) in healthy.calls

    failing = StubDirectXContext(object(), object())
    failing._present_error = RuntimeError("unexpected failure")
    backend._context = failing
    with pytest.raises(RuntimeError):
        backend.present()


def test_directx_backend_extract_hwnd_prefers_pointer_value() -> None:
    """_extract_hwnd should unwrap pointer-like attributes before casting."""

    backend = DirectXBackend()

    class Window:
        def __init__(self) -> None:
            self.handle = SimpleNamespace(value=99)

    assert backend._extract_hwnd(Window()) == 99


def test_directx_backend_cleanup_releases_resources(monkeypatch: pytest.MonkeyPatch) -> None:
    """cleanup should release constant buffers and call child cleanups."""

    backend = setup_stubbed_backend(monkeypatch)
    monkeypatch.setattr(backend, "is_available", lambda: True)
    backend.create_shader("demo", "vs", "ps")

    class StubConstantBuffer:
        def __init__(self) -> None:
            self.released = False

        def Release(self) -> None:  # noqa: N802 - matching DirectX style
            self.released = True

    cb = StubConstantBuffer()
    backend._vs_cbuffer = cb
    backend.cleanup()

    assert cb.released is True
    assert backend._device is None
    assert backend._context is None

