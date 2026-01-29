"""Coverage for the Ornata plugin manager and registry systems."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from collections.abc import Generator
from typing import Any

import pytest

from ornata.api.exports.definitions import (
    BackendTarget,
    Component,
    Event,
    LayoutResult,
    RenderOutput,
    ResolvedStyle,
)
from ornata.api.exports.plugins import (
    ComponentPlugin,
    EventPlugin,
    ExportPlugin,
    LayoutPlugin,
    PluginManager,
    PluginRegistry,
    RendererPlugin,
    StylePlugin,
)
from ornata.api.exports.rendering import Renderer


@pytest.fixture(autouse=True)
def reset_plugin_registry() -> Generator[None, None, None]:
    """Isolate registry state across tests."""

    previous = dict(PluginRegistry._registry)
    PluginRegistry._registry.clear()
    yield
    PluginRegistry._registry.clear()
    PluginRegistry._registry.update(previous)


class _RendererStub(Renderer):
    """Minimal renderer used by plugin stubs."""

    def __init__(self) -> None:
        super().__init__(BackendTarget.CLI)
        self.patches: list[Any] = []

    def render_tree(self, tree: Any, layout_result: Any) -> RenderOutput:
        return RenderOutput(
            content=f"render:{tree}",
            backend_target=self.backend_target,
            metadata={"layout_width": getattr(layout_result, "width", 0)},
        )

    def apply_patches(self, patches: list[Any]) -> None:
        self.patches.extend(patches)


class _ComprehensivePlugin(
    ComponentPlugin,
    RendererPlugin,
    LayoutPlugin,
    StylePlugin,
    EventPlugin,
    ExportPlugin,
):
    """Plugin exercising every capability hook for coverage."""

    def __init__(self) -> None:
        self.initialized = False
        self.cleaned = False
        self.events_handled: list[str] = []

    @property
    def name(self) -> str:
        return "comprehensive"

    @property
    def version(self) -> str:
        return "1.0.0"

    def initialize(self) -> None:
        self.initialized = True

    def cleanup(self) -> None:
        self.cleaned = True

    def get_component_types(self) -> list[str]:
        return ["card"]

    def create_component(self, component_type: str, *args: Any, **kwargs: Any) -> Component:
        component = Component(component_name=component_type)
        component.data = {"args": args, "kwargs": kwargs}
        return component

    def get_renderer_types(self) -> list[str]:
        return ["stub"]

    def create_renderer(self, renderer_type: str, *args: Any, **kwargs: Any) -> Renderer:
        _ = (renderer_type, args, kwargs)
        return _RendererStub()

    def get_layout_types(self) -> list[str]:
        return ["stack"]

    def calculate_layout(
        self,
        layout_type: str,
        component: Component,
        container_bounds: Any,
        renderer_type: Any,
    ) -> LayoutResult:
        _ = (layout_type, component, container_bounds, renderer_type)
        return LayoutResult(width=2, height=3)

    def get_style_properties(self) -> list[str]:
        return ["--plugin-color"]

    def resolve_custom_style(
        self,
        component_name: str,
        property_name: str,
        property_value: Any,
        context: Any,
    ) -> ResolvedStyle:
        _ = (component_name, property_name, property_value, context)
        return ResolvedStyle(color="#00f")

    def get_event_types(self) -> list[str]:
        return ["plugin_event"]

    def handle_event(self, event: Event) -> bool:
        self.events_handled.append(event.type.value)
        return True

    def get_export_formats(self) -> list[str]:
        return ["text"]

    def export_component(self, component: Component, format_name: str, **options: Any) -> str:
        _ = options
        return f"{component.component_name}:{format_name}"


class _CountingPlugin(ComponentPlugin):
    """Plugin that records initialize/cleanup counts for duplicate-load tests."""

    load_count = 0
    cleanup_count = 0

    @property
    def name(self) -> str:
        return "counter"

    @property
    def version(self) -> str:
        return "0.0.1"

    def initialize(self) -> None:
        type(self).load_count += 1

    def cleanup(self) -> None:
        type(self).cleanup_count += 1

    def get_component_types(self) -> list[str]:
        return ["counter"]

    def create_component(self, component_type: str, *args: Any, **kwargs: Any) -> Component:
        _ = (component_type, args, kwargs)
        return Component(component_name="counter-component")


class _DummyEntryPoint:
    """Test helper replicating ``importlib.metadata.EntryPoint`` behavior."""

    def __init__(self, name: str, obj: Any) -> None:
        self.name = name
        self._obj = obj

    def load(self) -> Any:
        return self._obj


def test_plugin_manager_loads_and_unloads_all_capabilities() -> None:
    """PluginManager should register every capability and support unload."""

    manager = PluginManager()
    manager.load_plugin(_ComprehensivePlugin, name="demo")

    plugin = manager.get_plugin("demo")
    assert isinstance(plugin, _ComprehensivePlugin)
    assert plugin.initialized is True
    assert manager.list_loaded_plugins() == ["demo"]

    assert manager.get_component_plugins() == [plugin]
    assert manager.get_renderer_plugins() == [plugin]
    assert manager.get_layout_plugins() == [plugin]
    assert manager.get_style_plugins() == [plugin]
    assert manager.get_event_plugins() == [plugin]
    assert manager.get_export_plugins() == [plugin]

    registered_names = PluginRegistry.list()
    assert "demo.card" in registered_names
    assert "demo.stub" in registered_names
    assert "demo.stack" in registered_names

    manager.unload_plugin("demo")
    assert plugin.cleaned is True
    assert manager.get_plugin("demo") is None
    assert manager.list_loaded_plugins() == []


def test_plugin_manager_avoids_duplicate_loads() -> None:
    """Loading the same plugin twice should keep a single instance."""

    _CountingPlugin.load_count = 0
    _CountingPlugin.cleanup_count = 0

    manager = PluginManager()
    manager.load_plugin(_CountingPlugin, name="counter")
    manager.load_plugin(_CountingPlugin, name="counter")

    assert _CountingPlugin.load_count == 1

    manager.unload_plugin("counter")
    assert _CountingPlugin.cleanup_count == 1


def test_plugin_manager_discovers_files_and_entry_points(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Discovery should load filesystem plugins and entry-point provided ones."""

    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    plugin_file = plugin_dir / "file_plugin.py"
    plugin_file.write_text(
        dedent(
            """
            from __future__ import annotations

            from ornata.api.exports.definitions import Component
            from ornata.api.exports.plugins import ComponentPlugin

            class FilePlugin(ComponentPlugin):
                @property
                def name(self) -> str:
                    return "file-plugin"

                @property
                def version(self) -> str:
                    return "0.2.0"

                def initialize(self) -> None:
                    self.initialized = True

                def cleanup(self) -> None:
                    self.initialized = False

                def get_component_types(self) -> list[str]:
                    return ["file"]

                def create_component(self, component_type: str, *args, **kwargs):
                    return Component(component_name=component_type)
            """
        ).strip()
    )

    def _fake_load_entry_points(cls) -> int:
        cls.register("entry.plugin", lambda: "ok")
        return 1

    monkeypatch.setattr(PluginRegistry, "load_entry_points", classmethod(_fake_load_entry_points))

    manager = PluginManager()
    manager.add_plugin_directory(plugin_dir)
    manager.add_plugin_directory(str(plugin_dir))

    loaded = manager.discover_and_load_plugins()
    assert loaded == 2
    assert len(manager._plugin_dirs) == 1  # noqa: SLF001 - test ensures deduplication
    assert "FilePlugin" in manager.list_loaded_plugins()
    assert PluginRegistry.get("entry.plugin") is not None


def test_plugin_registry_load_entry_points_uses_select(monkeypatch: pytest.MonkeyPatch) -> None:
    """Entry point providers with select() should register callables and tuples."""

    class RegisteringPlugin:
        def register(self) -> tuple[str, Any]:
            return ("registered.plugin", lambda: "ok")

    class EntryPointSet(list):
        def select(self, group: str) -> list[_DummyEntryPoint]:
            assert group == "ornata.plugins"
            return self

    def fake_entry_points(*args: Any, **kwargs: Any) -> EntryPointSet:
        _ = (args, kwargs)
        return EntryPointSet(
            [
                _DummyEntryPoint("callable.plugin", lambda: "callable"),
                _DummyEntryPoint("ignored", RegisteringPlugin()),
            ]
        )

    monkeypatch.setattr("ornata.plugins.registry.entry_points", fake_entry_points)

    count = PluginRegistry.load_entry_points()
    assert count == 2
    assert "callable.plugin" in PluginRegistry.list()
    assert "registered.plugin" in PluginRegistry.list()


def test_plugin_registry_load_entry_points_falls_back_without_select(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The registry should retry entry_points(group=...) when select() fails."""

    class NoSelect:
        pass

    def fake_entry_points(*args: Any, **kwargs: Any) -> Any:
        if kwargs:
            return [_DummyEntryPoint("fallback.plugin", lambda: "fallback")]
        return NoSelect()

    monkeypatch.setattr("ornata.plugins.registry.entry_points", fake_entry_points)

    count = PluginRegistry.load_entry_points()
    assert count == 1
    assert "fallback.plugin" in PluginRegistry.list()


def test_plugin_registry_load_entry_points_handles_missing_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    """When importlib metadata is unavailable, discovery should be a no-op."""

    monkeypatch.setattr("ornata.plugins.registry.entry_points", None)
    assert PluginRegistry.load_entry_points() == 0
