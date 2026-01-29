"""Tests for :mod:`ornata.core.application`."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import ornata.events.runtime as events_runtime
from ornata.api.exports.events import EventSubsystem
from ornata.core import application as application_module
from ornata.core.application import Application, BackendTarget
from ornata.definitions.dataclasses.components import Component, ComponentContent
from ornata.definitions.dataclasses.core import AppConfig, RuntimeFrame
from ornata.definitions.dataclasses.layout import LayoutResult
from ornata.definitions.dataclasses.rendering import GuiNode, RenderOutput
from ornata.definitions.dataclasses.vdom import VDOMTree
from ornata.rendering.backends.cli.input import CLIInputPipeline
from ornata.rendering.core.base_renderer import Renderer


def _component(name: str) -> Component:
    component = Component(component_name=name)
    component.content = ComponentContent(text=name)
    return component


def _frame(component_name: str = "Root") -> RuntimeFrame:
    component = _component(component_name)
    return RuntimeFrame(
        root=component,
        layout=LayoutResult(width=1, height=1),
        styles={},
        gui_tree=GuiNode(component_name=component.component_name or "node"),
    )


class DummyRenderer(Renderer):
    def __init__(self, backend_target: BackendTarget) -> None:
        super().__init__(backend_target)

    def render_tree(self, tree: object, layout_result: LayoutResult | None) -> RenderOutput:
        return RenderOutput(content=f"{self.backend_target.value}:{tree}", backend_target=self.backend_target.value)

    def apply_patches(self, patches: list[object]) -> None:
        return None


def test_register_backend_with_bridge_routes_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[BackendTarget, object]] = []

    class FakeBridge:
        def register_renderer(self, backend_target: BackendTarget, renderer: object) -> str:
            calls.append((backend_target, renderer))
            return "ctx"

    monkeypatch.setattr("ornata.rendering.vdom_bridge.get_vdom_renderer_bridge", lambda: FakeBridge())
    renderer = DummyRenderer(BackendTarget.CLI)
    context = application_module.register_backend_with_bridge(BackendTarget.CLI, renderer)
    assert context == "ctx"
    assert calls == [(BackendTarget.CLI, renderer)]


def test_render_vdom_tree_bridge_routes_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[object, BackendTarget]] = []

    class FakeBridge:
        def render_vdom_tree(self, tree: object, backend_target: BackendTarget) -> str:
            calls.append((tree, backend_target))
            return "rendered"

    monkeypatch.setattr("ornata.rendering.vdom_bridge.get_vdom_renderer_bridge", lambda: FakeBridge())
    tree = VDOMTree(backend_target=BackendTarget.CLI)
    result = application_module.render_vdom_tree_bridge(tree, BackendTarget.CLI)
    assert result == "rendered"
    assert calls == [(tree, BackendTarget.CLI)]


def test_print_wrapper_delegates_to_builtins(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[tuple[tuple[object, ...], dict[str, object]]] = []
    monkeypatch.setattr(application_module.builtins, "print", lambda *args, **kwargs: captured.append((args, kwargs)))
    application_module.print("value", 1, end="!", flush=True)
    assert captured == [(("value", 1), {"end": "!", "flush": True})]


@pytest.fixture
def runtime_spy(monkeypatch: pytest.MonkeyPatch) -> list[object]:
    instances: list[object] = []

    class DummyRuntime:
        def __init__(self, config: AppConfig) -> None:
            self.config = config
            self.vdom_tree = SimpleNamespace(mark="tree")
            self.stylesheets: list[str] = []
            self.run_components: list[Component] = []
            instances.append(self)

        def load_stylesheet(self, path: str) -> None:
            self.stylesheets.append(path)

        def run(self, component: Component) -> RuntimeFrame:
            self.run_components.append(component)
            return RuntimeFrame(
                root=component,
                layout=LayoutResult(width=10, height=5),
                styles={id(component): object()},
                gui_tree=GuiNode(component_name=component.component_name or "node"),
            )

    monkeypatch.setattr(application_module, "OrnataRuntime", DummyRuntime)
    return instances


def test_application_run_without_mount_raises(runtime_spy: list[object]) -> None:
    app = Application()
    with pytest.raises(RuntimeError, match="Call mount\\(\\) first"):
        app.run()


def test_application_run_invokes_runtime_and_render(monkeypatch: pytest.MonkeyPatch, runtime_spy: list[object]) -> None:
    app = Application()
    component = _component("Hello")
    app.mount(lambda: component)
    captured: dict[str, object] = {}

    def fake_render(frame: RuntimeFrame, *, loop_mode: bool) -> None:
        captured["frame"] = frame
        captured["loop_mode"] = loop_mode

    monkeypatch.setattr(app, "_render_frame", fake_render)
    frame = app.run()
    assert frame.root is component
    assert captured["frame"] is frame
    assert captured["loop_mode"] is False


def test_application_set_backend_recreates_runtime(runtime_spy: list[object]) -> None:
    config = AppConfig(stylesheets=["tests/data/styles/testing.osts"])
    app = Application(config)
    assert len(runtime_spy) == 1
    app.set_backend(BackendTarget.GUI)
    assert config.backend is BackendTarget.GUI
    assert len(runtime_spy) == 2
    assert runtime_spy[-1].stylesheets == ["tests/data/styles/testing.osts"]


def test_application_add_stylesheet_prevents_duplicates(runtime_spy: list[object]) -> None:
    app = Application()
    app.add_stylesheet("sheet.osts")
    app.add_stylesheet("sheet.osts")
    assert runtime_spy[-1].stylesheets == ["sheet.osts"]


def test_application_mount_accepts_component_instance(runtime_spy: list[object]) -> None:
    app = Application()
    component = _component("Mounted")
    app.mount(component)
    assert app._builder is not None  # noqa: SLF001
    assert app._builder() is component


def test_application_run_loop_cli_stops_after_single_iteration(monkeypatch: pytest.MonkeyPatch, runtime_spy: list[object]) -> None:
    app = Application()
    component = _component("LoopRoot")
    app.mount(lambda: component)

    class FakeSubsystem(EventSubsystem):
        def __init__(self) -> None:
            self.started = 0
            self.pumped = 0
            self.stopped = 0

        def start_platform_event_loop(self) -> None:
            self.started += 1

        def pump_platform_events(self) -> None:
            self.pumped += 1

        def stop_platform_event_loop(self) -> None:
            self.stopped += 1

    subsystem = FakeSubsystem()

    def fake_ensure_event_subsystem() -> EventSubsystem:
        app._event_subsystem = subsystem  # noqa: SLF001
        return subsystem

    monkeypatch.setattr(app, "_ensure_event_subsystem", fake_ensure_event_subsystem)

    pipeline_calls: list[str] = []

    class Pipeline(CLIInputPipeline):
        def __init__(self) -> None:
            self.started = False

        def start(self) -> None:
            self.started = True
            pipeline_calls.append("start")

        def stop(self) -> None:
            pipeline_calls.append("stop")

    def fake_start_cli_input_pipeline(ignored: object) -> None:
        pipeline = Pipeline()
        pipeline.start()
        app._cli_input_pipeline = pipeline  # noqa: SLF001

    monkeypatch.setattr(app, "_start_cli_input_pipeline", fake_start_cli_input_pipeline)

    render_calls: list[bool] = []

    def fake_render_frame(frame: RuntimeFrame, *, loop_mode: bool) -> None:
        render_calls.append(loop_mode)
        app.stop()

    monkeypatch.setattr(app, "_render_frame", fake_render_frame)

    def fake_run(root_component: Component) -> RuntimeFrame:
        return _frame(root_component.component_name or "LoopRoot")

    app._runtime.run = fake_run
    monkeypatch.setattr(application_module.time, "sleep", lambda _: None)

    app.run_loop(fps=15)

    assert subsystem.started == 1
    assert subsystem.pumped >= 1
    assert subsystem.stopped == 1
    assert pipeline_calls == ["start", "stop"]
    assert render_calls == [True]


def test_application_run_loop_gui_invokes_driver(monkeypatch: pytest.MonkeyPatch, runtime_spy: list[object]) -> None:
    config = AppConfig(backend=BackendTarget.GUI)
    app = Application(config)
    app.mount(lambda: _component("GuiLoop"))

    class FakeSubsystem(EventSubsystem):
        def start_platform_event_loop(self) -> None:
            return None

        def pump_platform_events(self) -> None:
            app.stop()

        def stop_platform_event_loop(self) -> None:
            return None

    subsystem = FakeSubsystem()

    def fake_gui_subsystem() -> EventSubsystem:
        app._event_subsystem = subsystem  # noqa: SLF001
        return subsystem

    monkeypatch.setattr(app, "_ensure_event_subsystem", fake_gui_subsystem)

    gui_calls: list[tuple[str, bool]] = []
    monkeypatch.setattr(app, "_ensure_gui_driver", lambda backend_name, *, loop_mode: gui_calls.append((backend_name, loop_mode)))

    def fake_run(component: Component) -> RuntimeFrame:
        return _frame(component.component_name or "GuiLoop")

    app._runtime.run = fake_run
    monkeypatch.setattr(app, "_render_frame", lambda frame, *, loop_mode: app.stop())
    monkeypatch.setattr(application_module.time, "sleep", lambda _: None)

    app.run_loop(fps=30)

    assert gui_calls == [("auto", True)]


def test_application_run_loop_rejects_nonpositive_fps(runtime_spy: list[object]) -> None:
    app = Application()
    app.mount(lambda: _component("Root"))
    with pytest.raises(ValueError):
        app.run_loop(fps=0)


def test_application_run_loop_handles_keyboard_interrupt(monkeypatch: pytest.MonkeyPatch, runtime_spy: list[object]) -> None:
    app = Application()
    app.mount(lambda: _component("Root"))

    class FakeSubsystem(EventSubsystem):
        def start_platform_event_loop(self) -> None:
            return None

        def pump_platform_events(self) -> None:
            return None

        def stop_platform_event_loop(self) -> None:
            return None

    subsystem = FakeSubsystem()
    app._event_subsystem = subsystem  # noqa: SLF001
    monkeypatch.setattr(app, "_ensure_event_subsystem", lambda: subsystem)

    class Pipeline(CLIInputPipeline):
        def __init__(self, event_subsystem: EventSubsystem) -> None:
            super().__init__(event_subsystem)

        def start(self) -> None:
            return None

        def stop(self) -> None:
            pipeline_calls.append("stop")

    pipeline_calls: list[str] = []

    def fake_start_cli_input_pipeline(ignored: object) -> None:
        app._cli_input_pipeline = Pipeline(subsystem)  # noqa: SLF001

    monkeypatch.setattr(app, "_start_cli_input_pipeline", fake_start_cli_input_pipeline)
    monkeypatch.setattr(application_module.time, "sleep", lambda _: None)
    monkeypatch.setattr(app._runtime, "run", lambda component: (_ for _ in ()).throw(KeyboardInterrupt()))

    app.run_loop(fps=10)

    assert pipeline_calls == ["stop"]


def test_render_frame_dispatches_to_each_backend(monkeypatch: pytest.MonkeyPatch, runtime_spy: list[object]) -> None:
    app = Application()
    frame = _frame()

    called: list[tuple[str, BackendTarget]] = []
    monkeypatch.setattr(app, "_run_terminal_session", lambda frame, backend, factory, *, loop_mode: called.append(("terminal", backend)))
    monkeypatch.setattr(app, "_run_gui_session", lambda frame, backend_name, *, loop_mode: called.append(("gui", backend_name)))

    app.config.backend = BackendTarget.CLI
    app._render_frame(frame, loop_mode=False)
    app.config.backend = BackendTarget.TTY
    app._render_frame(frame, loop_mode=True)
    app.config.backend = BackendTarget.GUI
    app._render_frame(frame, loop_mode=False)

    assert called == [
        ("terminal", BackendTarget.CLI),
        ("terminal", BackendTarget.TTY),
        ("gui", "auto"),
    ]


def test_render_frame_unknown_backend_logs_warning(monkeypatch: pytest.MonkeyPatch, runtime_spy: list[object]) -> None:
    app = Application()
    warnings: list[str] = []
    app.config.backend = SimpleNamespace(value="mystery")
    monkeypatch.setattr(app._logger, "warning", lambda msg, *args: warnings.append(msg))
    app._render_frame(_frame(), loop_mode=False)
    assert warnings and "not implemented" in warnings[0]


def test_run_terminal_session_updates_last_output(monkeypatch: pytest.MonkeyPatch, runtime_spy: list[object]) -> None:
    app = Application()
    frame = _frame()
    backend_output = RenderOutput(content="new", backend_target="cli")

    class BackendStub:
        def render_tree(self, tree: object, layout: LayoutResult) -> RenderOutput:
            return backend_output

    displayed: list[RenderOutput] = []
    monkeypatch.setattr(app, "_display_terminal_output", lambda output, *, loop_mode, previous_content: displayed.append(output))
    app._ensure_backend = lambda backend_target, factory: BackendStub()
    app._last_output = RenderOutput(content="old", backend_target="cli")

    app._run_terminal_session(frame, BackendTarget.CLI, lambda backend_target: BackendStub(), loop_mode=False)
    assert displayed == [backend_output]
    assert app._last_output is backend_output


def test_run_terminal_session_uses_prepared_tree(monkeypatch: pytest.MonkeyPatch, runtime_spy: list[object]) -> None:
    app = Application()
    frame = _frame()
    frame.gui_tree = None
    backend_output = RenderOutput(content="prepared", backend_target="cli")

    class BackendStub:
        def __init__(self) -> None:
            self.trees: list[object] = []

        def render_tree(self, tree: object, layout: LayoutResult) -> RenderOutput:
            self.trees.append(tree)
            return backend_output

    backend = BackendStub()
    app._ensure_backend = lambda backend_target, factory: backend
    app._prepare_render_tree = lambda backend_target: "render-tree"
    monkeypatch.setattr(app, "_display_terminal_output", lambda *args, **kwargs: None)

    app._run_terminal_session(frame, BackendTarget.TTY, lambda backend_target: backend, loop_mode=True)
    assert backend.trees == ["render-tree"]


def test_run_gui_session_resets_last_output(monkeypatch: pytest.MonkeyPatch, runtime_spy: list[object]) -> None:
    app = Application()
    frame = _frame()
    driver_calls: list[tuple[GuiNode, bool]] = []

    class DriverStub:
        def present(self, gui_node: GuiNode, *, blocking: bool) -> None:
            driver_calls.append((gui_node, blocking))

    app._ensure_gui_driver = lambda backend_name, *, loop_mode: DriverStub()
    app._last_output = RenderOutput(content="old", backend_target="cli")
    app._run_gui_session(frame, "auto", loop_mode=False)
    assert driver_calls[0][1] is True
    assert app._last_output is None


def test_run_gui_session_handles_driver_error(monkeypatch: pytest.MonkeyPatch, runtime_spy: list[object]) -> None:
    app = Application()
    frame = _frame()
    errors: list[str] = []
    app._logger = SimpleNamespace(error=lambda msg, *args: errors.append(msg))

    def boom(*args, **kwargs):  # noqa: ANN001
        raise RuntimeError("boom")

    app._ensure_gui_driver = boom
    app._run_gui_session(frame, "auto", loop_mode=False)
    assert errors and "Failed to initialize" in errors[0]


def test_display_terminal_output_handles_bytes(monkeypatch: pytest.MonkeyPatch, runtime_spy: list[object]) -> None:
    app = Application()
    prints: list[str] = []
    monkeypatch.setattr(application_module, "print", lambda value, *args, **kwargs: prints.append(value))
    clears: list[str] = []
    app._clear_terminal = lambda: clears.append("cleared")

    app._display_terminal_output(RenderOutput(content=b"hi", backend_target="cli"), loop_mode=True, previous_content="hi")
    assert prints == []

    app._display_terminal_output(RenderOutput(content=b"hi", backend_target="cli"), loop_mode=True, previous_content=None)
    assert clears == ["cleared"]
    assert prints == ["hi"]

    app._display_terminal_output(RenderOutput(content="bye", backend_target="cli"), loop_mode=False, previous_content=None)
    assert prints[-1] == "bye"


def test_display_terminal_output_skips_duplicate_loop_content(monkeypatch: pytest.MonkeyPatch, runtime_spy: list[object]) -> None:
    app = Application()
    outputs: list[str] = []
    monkeypatch.setattr(application_module, "print", lambda value="", *args, **kwargs: outputs.append(value))
    app._display_terminal_output(RenderOutput(content="same", backend_target="cli"), loop_mode=True, previous_content="same")
    assert outputs == []


def test_ensure_backend_uses_factory_once(runtime_spy: list[object]) -> None:
    app = Application()
    created: list[object] = []

    def factory() -> object:
        value = SimpleNamespace()
        created.append(value)
        return value

    contexts: list[BackendTarget] = []
    app._ensure_backend_context = lambda backend_target, factory=None: contexts.append(backend_target)

    backend = app._ensure_backend(BackendTarget.CLI, factory)
    backend_again = app._ensure_backend(BackendTarget.CLI, factory)
    assert backend_again is backend
    assert len(created) == 1
    assert contexts == [BackendTarget.CLI, BackendTarget.CLI]


def test_ensure_backend_context_registration(monkeypatch: pytest.MonkeyPatch, runtime_spy: list[object]) -> None:
    app = Application()
    renderer = object()
    app._backend_instances[BackendTarget.CLI] = renderer
    context = SimpleNamespace()
    monkeypatch.setattr(application_module, "register_backend_with_bridge", lambda backend_target, backend: context)

    app._ensure_backend_context(BackendTarget.CLI)
    assert app._backend_contexts[BackendTarget.CLI] is context

    with pytest.raises(ValueError, match="No backend factory"):
        app._ensure_backend_context(BackendTarget.TTY)


def test_ensure_backend_context_requires_factory(runtime_spy: list[object]) -> None:
    app = Application()
    with pytest.raises(ValueError, match="No backend factory"):
        app._ensure_backend_context(BackendTarget.GUI)


def test_prepare_render_tree_renders(monkeypatch: pytest.MonkeyPatch, runtime_spy: list[object]) -> None:
    app = Application()
    rendered: list[tuple[object, BackendTarget]] = []
    app._runtime = SimpleNamespace(vdom_tree="tree")
    monkeypatch.setattr(app, "_ensure_backend_context", lambda backend_target: None)
    monkeypatch.setattr(application_module, "render_vdom_tree_bridge", lambda tree, backend_target: rendered.append((tree, backend_target)) or "converted")

    result = app._prepare_render_tree(BackendTarget.CLI)
    assert result == "converted"
    assert rendered == [("tree", BackendTarget.CLI)]


def test_create_renderers_call_factories(monkeypatch: pytest.MonkeyPatch, runtime_spy: list[object]) -> None:
    app = Application()
    created_cli: list[BackendTarget] = []
    created_tty: list[BackendTarget] = []
    monkeypatch.setattr(application_module, "ANSIRenderer", lambda backend_target: created_cli.append(backend_target) or SimpleNamespace())
    monkeypatch.setattr(application_module, "TTYRenderer", lambda backend_target: created_tty.append(backend_target) or SimpleNamespace())

    app._create_cli_renderer(BackendTarget.CLI)
    app._create_tty_renderer(BackendTarget.TTY)
    assert created_cli == [BackendTarget.CLI]
    assert created_tty == [BackendTarget.TTY]


def test_resolve_gui_backend_name(runtime_spy: list[object]) -> None:
    app = Application()
    assert app._resolve_gui_backend_name(BackendTarget.GUI) == "auto"
    app.config.capabilities["gui_backend"] = "dx"
    assert app._resolve_gui_backend_name(BackendTarget.GUI) == "dx"


def test_ensure_event_subsystem_caches(monkeypatch: pytest.MonkeyPatch, runtime_spy: list[object]) -> None:
    subsystem = SimpleNamespace()
    monkeypatch.setattr(events_runtime, "get_event_subsystem", lambda: subsystem)
    app = Application()
    first = app._ensure_event_subsystem()
    second = app._ensure_event_subsystem()
    assert first is second is subsystem


def test_start_cli_input_pipeline_singleton(monkeypatch: pytest.MonkeyPatch, runtime_spy: list[object]) -> None:
    app = Application()
    starts: list[str] = []

    class Pipeline:
        def __init__(self) -> None:
            self.started = False

        def start(self) -> None:
            self.started = True
            starts.append("start")

        def stop(self) -> None:
            starts.append("stop")

    monkeypatch.setattr(application_module, "create_cli_input_pipeline", lambda subsystem: Pipeline())
    subsystem = SimpleNamespace()
    app._start_cli_input_pipeline(subsystem)
    app._start_cli_input_pipeline(subsystem)
    assert starts == ["start"]
    app.stop()
    assert "stop" in starts


def test_ensure_gui_driver_reuse(monkeypatch: pytest.MonkeyPatch, runtime_spy: list[object]) -> None:
    app = Application()
    created: list[str] = []

    class DriverStub:
        def __init__(self, config: AppConfig, logger: object, *, backend_name: str) -> None:
            self.backend_name = backend_name
            self.ensure_running_calls = 0
            created.append(backend_name)

        def ensure_running(self) -> None:
            self.ensure_running_calls += 1

    monkeypatch.setattr(application_module, "_GUIRenderDriver", DriverStub)
    driver = app._ensure_gui_driver("auto", loop_mode=False)
    assert driver.backend_name == "auto"
    assert app._gui_driver is None

    driver_loop = app._ensure_gui_driver("loop", loop_mode=True)
    assert app._gui_driver is driver_loop
    driver_again = app._ensure_gui_driver("loop", loop_mode=True)
    assert driver_again is driver_loop
    assert driver_loop.ensure_running_calls == 1


def test_clear_terminal_outputs_escape(monkeypatch: pytest.MonkeyPatch, runtime_spy: list[object]) -> None:
    app = Application()
    writes: list[str] = []
    monkeypatch.setattr(application_module, "print", lambda value="", *args, **kwargs: writes.append(value))
    app._clear_terminal()
    assert writes[-1] == "\x1b[2J\x1b[H"


@pytest.fixture
def gui_environment(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    rendered: list[tuple[GuiNode, object]] = []

    class FakeThread:
        def __init__(self) -> None:
            self._alive = True

        def is_alive(self) -> bool:
            return self._alive

        def join(self, timeout: float | None = None) -> None:
            self._alive = False

    class FakeGuiApplication:
        def __init__(self, backend: str) -> None:
            self.backend = backend
            self._running = False
            self.windows: list[object] = []
            self.stop_calls = 0

        @property
        def is_running(self) -> bool:
            return self._running

        def create_window(self, title: str, width: int, height: int) -> object:
            window = SimpleNamespace(title=title, width=width, height=height)
            self.windows.append(window)
            return window

        def run(self) -> None:
            self._running = True

        def run_async(self) -> FakeThread:
            self._running = True
            return FakeThread()

        def stop(self) -> None:
            self.stop_calls += 1
            self._running = False

    runtime = SimpleNamespace(rendered=[])

    def fake_render_gui_node(gui_node: GuiNode, window: object) -> None:
        rendered.append((gui_node, window))

    runtime.render_gui_node = fake_render_gui_node
    monkeypatch.setattr(application_module, "GuiApplication", FakeGuiApplication)
    monkeypatch.setattr(application_module, "get_gui_runtime", lambda: runtime)
    return SimpleNamespace(runtime=runtime, rendered=rendered)


def test_gui_render_driver_present_and_shutdown(gui_environment: SimpleNamespace) -> None:
    logger = SimpleNamespace(info=lambda *args, **kwargs: None, error=lambda *args, **kwargs: None)
    driver = application_module._GUIRenderDriver(AppConfig(), logger, backend_name="mock")
    gui_node = GuiNode(component_name="node")
    driver.present(gui_node, blocking=True)
    assert gui_environment.rendered[-1][0] is gui_node
    driver.present(gui_node, blocking=False)
    assert driver._loop_active is True  # noqa: SLF001
    driver.ensure_running()
    driver.shutdown()
    assert driver._loop_active is False  # noqa: SLF001


def test_gui_render_driver_requires_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    logger = SimpleNamespace(info=lambda *args, **kwargs: None, error=lambda *args, **kwargs: None)

    class FakeApp:
        def __init__(self) -> None:
            self.is_running = False

        def create_window(self, *args: object) -> object:
            return object()

        def run(self) -> None:
            return None

        def run_async(self) -> SimpleNamespace:
            return SimpleNamespace(is_alive=lambda: False, join=lambda timeout=None: None)

        def stop(self) -> None:
            return None

    monkeypatch.setattr(application_module, "GuiApplication", lambda backend: FakeApp())
    monkeypatch.setattr(application_module, "get_gui_runtime", lambda: None)

    with pytest.raises(RuntimeError, match="GUI runtime unavailable"):
        application_module._GUIRenderDriver(AppConfig(), logger, backend_name="mock")


def test_gui_render_driver_present_requires_runtime(gui_environment: SimpleNamespace) -> None:
    logger = SimpleNamespace(info=lambda *args, **kwargs: None, error=lambda *args, **kwargs: None)
    driver = application_module._GUIRenderDriver(AppConfig(), logger, backend_name="mock")
    driver._runtime = None
    with pytest.raises(RuntimeError, match="GUI runtime/window not initialized"):
        driver.present(GuiNode(component_name="node"))


def test_gui_render_driver_ensure_running_handles_existing_loop(gui_environment: SimpleNamespace) -> None:
    logger = SimpleNamespace(info=lambda *args, **kwargs: None, error=lambda *args, **kwargs: None)
    driver = application_module._GUIRenderDriver(AppConfig(), logger, backend_name="mock")
    driver._app._running = True  # noqa: SLF001
    driver.ensure_running()
    assert driver._loop_active is True  # noqa: SLF001


def test_application_stop_cleans_resources(runtime_spy: list[object]) -> None:
    app = Application()
    calls: list[str] = []
    app._cli_input_pipeline = SimpleNamespace(stop=lambda: calls.append("pipeline"))  # noqa: SLF001
    app._event_subsystem = SimpleNamespace(stop_platform_event_loop=lambda: calls.append("events"))  # noqa: SLF001
    app._gui_driver = SimpleNamespace(shutdown=lambda: calls.append("gui"))  # noqa: SLF001
    app._event_loop_started = True  # noqa: SLF001
    app.stop()
    assert calls == ["pipeline", "events", "gui"]
    assert app._gui_driver is None


def test_run_gui_session_sets_last_output_to_none(runtime_spy: list[object]) -> None:
    app = Application()
    frame = _frame()
    app._last_output = RenderOutput(content="old", backend_target="cli")
    driver_calls: list[bool] = []

    class DriverStub:
        def present(self, gui_node: GuiNode, *, blocking: bool) -> None:
            driver_calls.append(blocking)

    app._ensure_gui_driver = lambda backend_name, *, loop_mode: DriverStub()
    app._run_gui_session(frame, "auto", loop_mode=True)
    assert driver_calls == [False]
    assert app._last_output is None
