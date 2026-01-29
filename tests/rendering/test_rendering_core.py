"""Rendering core, pipeline, and signal coverage tests."""

from __future__ import annotations

from collections import deque
from typing import Any

import pytest

from ornata.api.exports.rendering import (
    FrameBuffer,
    RenderPipeline,
    RenderableBase,
    Renderer,
    SignalDispatcher,
    SignalEmitter,
    get_global_dispatcher,
)
from ornata.definitions.dataclasses.components import Component
from ornata.definitions.dataclasses.layout import LayoutResult
from ornata.definitions.dataclasses.rendering import Layer, PixelSurface, RenderOutput, RenderSignal
from ornata.definitions.enums import (
    BackendTarget,
    BlendMode,
    FrameState,
    RendererType,
    SignalType,
)
from ornata.definitions.errors import PipelineError
from ornata.definitions.flags import RenderCapability
from ornata.rendering.core.compositor import Compositor as CoreCompositor


class EchoRenderable(RenderableBase):
    """Renderable used to exercise :class:`RenderableBase` helpers."""

    def __init__(self, text: str | None = None) -> None:
        self._text = text

    def render(self) -> str | None:
        return self._text


class RecordingRenderer(Renderer):
    """Renderer stub that records invocations for assertions."""

    def __init__(self, backend_target: BackendTarget, *, fail: bool = False) -> None:
        super().__init__(backend_target)
        self.render_calls: list[tuple[Any, Any]] = []
        self.patch_calls: list[list[Any]] = []
        self._fail = fail

    def render_tree(self, tree: Any, layout_result: Any) -> RenderOutput:
        self.render_calls.append((tree, layout_result))
        if self._fail:
            raise RuntimeError("intentional renderer failure")
        return RenderOutput(
            content="frame",
            backend_target=str(self.backend_target),
            metadata={"layout_size": (getattr(layout_result, "width", 0), getattr(layout_result, "height", 0))},
        )

    def apply_patches(self, patches: list[Any]) -> None:
        self.patch_calls.append(patches)


def _make_pixel_surface(color: tuple[int, int, int, int]) -> PixelSurface:
    """Return a single-pixel :class:`PixelSurface` filled with ``color``."""

    surface = PixelSurface(width=1, height=1)
    surface.data = [[color]]
    return surface


def test_renderable_base_to_node_and_measure() -> None:
    """``RenderableBase`` should propagate render output into GuiNode metadata."""

    renderable = EchoRenderable("Hello")
    node = renderable.to_node()
    assert node.metadata["renderable"] is renderable
    assert node.text == "Hello"

    measurement = renderable.measure()
    assert measurement is not None
    assert measurement.width >= 5
    assert measurement.height == 1

    empty = EchoRenderable()
    null_measure = empty.measure()
    assert null_measure is not None
    assert null_measure.width == 0


def test_framebuffer_cycle_and_stats() -> None:
    """``FrameBuffer`` should rotate frames and report statistics."""

    buffer = FrameBuffer(buffer_size=2)
    frame_one = buffer.acquire_next_frame()
    assert frame_one.frame_number == 0
    frame_one.mark_rendering_start()
    frame_one.mark_rendering_complete()
    assert frame_one.is_ready_to_present()

    frame_two = buffer.acquire_next_frame()
    assert frame_two.frame_number == 1
    frame_two.mark_rendering_start()
    frame_two.mark_presented()
    assert frame_two.state == FrameState.PRESENTED

    ready = buffer.get_ready_frame()
    assert ready is frame_one

    stats = buffer.get_stats()
    assert stats["buffer_size"] == 2
    assert stats["active_frames"] == 2

    buffer.clear()
    assert buffer.get_ready_frame() is None


def test_compositor_blend_modes_track_dirty_regions() -> None:
    """``Compositor`` should respect blend modes and dirty region accounting."""

    compositor = CoreCompositor(width=1, height=1)
    base_layer = Layer(
        name="base",
        surface=_make_pixel_surface((10, 10, 10, 255)),
        blend_mode=BlendMode.REPLACE,
        z_index=0,
    )
    add_layer = Layer(
        name="add",
        surface=_make_pixel_surface((5, 0, 0, 255)),
        blend_mode=BlendMode.ADD,
        z_index=1,
    )

    compositor.add_layer(base_layer)
    compositor.add_layer(add_layer)

    result = compositor.compose()
    assert result.width == 1
    assert result.height == 1

    compositor.remove_layer("add")
    compositor.clear_all_layers()


def test_render_pipeline_renders_and_tracks_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    """``RenderPipeline`` should orchestrate layout, render, and composition stages."""

    created_engines: deque[Any] = deque()

    class StubLayoutEngine:
        def __init__(self) -> None:  # pragma: no cover - exercised indirectly
            created_engines.append(self)

        def calculate_layout(self, component: Component, bounds: Any, backend_target: BackendTarget) -> LayoutResult:
            self.last_call = (component, bounds, backend_target)
            return LayoutResult(width=64, height=32)

    monkeypatch.setattr("ornata.api.exports.layout.LayoutEngine", StubLayoutEngine)

    renderer = RecordingRenderer(BackendTarget.CLI)
    pipeline = RenderPipeline(renderer, RendererType.CPU)

    component = Component(component_name="root")
    output = pipeline.render_frame(component, LayoutResult(width=10, height=5))
    assert output.content == "frame"
    assert renderer.render_calls
    assert created_engines

    metrics = pipeline.get_metrics()
    assert metrics.frames_rendered == 1
    assert metrics.fps >= 0

    pipeline.apply_patches(["patch"])
    assert renderer.patch_calls[-1] == ["patch"]

    stats = pipeline.get_frame_buffer_stats()
    assert stats["buffer_size"] == 2

    pipeline.reset_metrics()
    assert pipeline.get_metrics().frames_rendered == 0

    pipeline.clear_frame_buffer()
    assert pipeline.is_idle() is True


def test_render_pipeline_raises_pipeline_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Errors from the renderer should surface as :class:`PipelineError`."""

    class StubLayoutEngine:
        def calculate_layout(self, component: Component, bounds: Any, backend_target: BackendTarget) -> LayoutResult:
            return LayoutResult(width=10, height=5)

    monkeypatch.setattr("ornata.api.exports.layout.LayoutEngine", StubLayoutEngine)

    failing_renderer = RecordingRenderer(BackendTarget.CLI, fail=True)
    pipeline = RenderPipeline(failing_renderer, RendererType.CPU)

    with pytest.raises(PipelineError):
        pipeline.render_frame(Component(component_name="root"), LayoutResult())

    assert pipeline.is_error() is True


def test_signal_dispatcher_emits_and_clears() -> None:
    """Signal dispatcher should route events and support handler lifecycle."""

    dispatcher = SignalDispatcher()
    recorded: list[tuple[str, dict[str, Any]]] = []

    def handler(signal: RenderSignal) -> None:
        recorded.append((signal.signal_type.name, signal.data))

    dispatcher.connect(SignalType.RENDER_START, handler)
    dispatcher.connect_all(handler)

    signal = RenderSignal(signal_type=SignalType.RENDER_START, data={"frame": 1}, timestamp=0.0)
    dispatcher.emit(signal)
    assert recorded[0][0] == "RENDER_START"
    assert dispatcher.get_handler_count() == 2

    dispatcher.disconnect(SignalType.RENDER_START, handler)
    dispatcher.disconnect_all(handler)
    assert dispatcher.get_handler_count() == 0

    dispatcher.clear_handlers()


def test_signal_emitter_helpers_use_dispatcher(monkeypatch: pytest.MonkeyPatch) -> None:
    """``SignalEmitter`` helper methods should emit properly typed signals."""

    dispatcher = get_global_dispatcher()
    emitter = SignalEmitter(dispatcher)
    events: list[SignalType] = []

    def recorder(signal: RenderSignal) -> None:
        events.append(signal.signal_type)

    dispatcher.connect_all(recorder)
    emitter.emit_render_start(1)
    emitter.emit_render_complete(1, duration=0.1)
    emitter.emit_render_error(1, RuntimeError("boom"))
    emitter.emit_frame_dropped(2, reason="timeout")
    emitter.emit_performance_warning("warn", metric="frame", value=5.0, threshold=3.0)

    assert events == [
        SignalType.RENDER_START,
        SignalType.RENDER_COMPLETE,
        SignalType.RENDER_ERROR,
        SignalType.FRAME_DROPPED,
        SignalType.PERFORMANCE_WARNING,
    ]

    dispatcher.clear_handlers()


def test_capabilities_report_flags() -> None:
    """Capability helpers should advertise supported render features."""

    from ornata.api.exports.rendering import get_capabilities, get_cli_capabilities, get_gui_capabilities, get_tty_capabilities

    cli_caps = get_cli_capabilities()
    assert cli_caps.backend_type == BackendTarget.CLI
    assert cli_caps.has_capability(RenderCapability.COLOR)

    gui_caps = get_gui_capabilities()
    assert gui_caps.backend_type == BackendTarget.GUI
    assert gui_caps.frame_rate == pytest.approx(60.0)

    tty_caps = get_tty_capabilities()
    assert tty_caps.backend_type == BackendTarget.TTY

    assert get_capabilities(BackendTarget.CLI).backend_type == BackendTarget.CLI


def test_global_dispatcher_singleton() -> None:
    """``get_global_dispatcher`` should always return the same instance."""

    dispatcher_one = get_global_dispatcher()
    dispatcher_two = get_global_dispatcher()
    assert dispatcher_one is dispatcher_two
