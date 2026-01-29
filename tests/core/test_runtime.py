"""Tests for :mod:`ornata.core.runtime`."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ornata.core import runtime as runtime_module
from ornata.core.runtime import OrnataRuntime
from ornata.definitions.dataclasses.components import (
    Component,
    ComponentContent,
    ComponentMeasurement,
)
from ornata.definitions.dataclasses.core import AppConfig
from ornata.definitions.dataclasses.layout import LayoutResult, LayoutStyle
from ornata.definitions.dataclasses.styling import Insets, Length, ResolvedStyle, StylingContext
from ornata.layout.engine.engine import LayoutEngine, LayoutNode
from ornata.styling.runtime.runtime import StylingRuntime

if TYPE_CHECKING:
    from collections.abc import Sequence

    import pytest


def _component(name: str, text: str | None = None) -> Component:
    component = Component(component_name=name)
    if text is not None:
        component.content = ComponentContent(text=text)
    return component


def test_runtime_load_stylesheet_deduplicates() -> None:
    """Repeated stylesheet loads should invoke the styling runtime only once."""

    runtime = OrnataRuntime(AppConfig())

    class TrackingStylingRuntime(StylingRuntime):
        def __init__(self) -> None:
            self.loaded: list[str] = []

        def load_stylesheet(self, path: str) -> None:
            self.loaded.append(path)

        def resolve_styles_parallel(self, contexts: Sequence[StylingContext]) -> list[ResolvedStyle]:  # pragma: no cover - not needed here
            return [ResolvedStyle() for _ in contexts]

    dummy = TrackingStylingRuntime()
    runtime._styling = dummy  # noqa: SLF001 - test instrumentation

    runtime.load_stylesheet("tests/data/styles/testing.osts")
    runtime.load_stylesheet("tests/data/styles/testing.osts")

    assert dummy.loaded == ["tests/data/styles/testing.osts"]


def test_runtime_resolve_styles_builds_contexts() -> None:
    """``_resolve_styles`` should build a context per component depth-first."""

    runtime = OrnataRuntime(AppConfig())
    contexts_seen: list[list[str]] = []

    class ContextCapturingStylingRuntime(StylingRuntime):
        def resolve_styles_parallel(self, contexts: Sequence[StylingContext]) -> list[ResolvedStyle]:
            contexts_seen.append([ctx.component_name for ctx in contexts])
            return [ResolvedStyle(font="root"), ResolvedStyle(font="child")]

        def load_stylesheet(self, path: str) -> None:  # pragma: no cover - defensive
            raise AssertionError("Unexpected stylesheet load")

    runtime._styling = ContextCapturingStylingRuntime()  # noqa: SLF001

    root = _component("Root", text="root")
    child = _component("Child", text="child")
    root.children.append(child)

    styles = runtime._resolve_styles(root)

    assert contexts_seen == [["Root", "Child"]]
    assert styles[id(root)].font == "root"
    assert styles[id(child)].font == "child"


def test_runtime_build_layout_tree_applies_styles() -> None:
    """Resolved styles should mutate layout nodes as expected."""

    runtime = OrnataRuntime(AppConfig())
    root = _component("Root")
    child = _component("Child")
    root.children.append(child)

    root_style = ResolvedStyle(
        width=Length(20),
        height=Length(10),
        min_width=Length(5),
        min_height=Length(6),
        max_width=Length(40),
        max_height=Length(30),
        display="flex",
        position="relative",
        flex_direction="row",
        flex_wrap="wrap",
        justify_content="center",
        align_items="stretch",
        flex_grow=2.0,
        flex_shrink=1.0,
        flex_basis=Length(15),
        margin=Insets(Length(1), Length(1), Length(1), Length(1)),
    )
    child_style = ResolvedStyle(flex_wrap="nowrap", flex_grow=1.0, flex_shrink=0.5)

    layout_tree, bindings = runtime._build_layout_tree(
        root,
        {
            id(root): root_style,
            id(child): child_style,
        },
    )

    assert isinstance(layout_tree, LayoutNode)
    assert layout_tree.style.width == 20
    assert layout_tree.style.height == 10
    assert layout_tree.style.min_width == 5
    assert layout_tree.style.wrap is True

    child_node = bindings[id(child)]
    assert child_node.style.wrap is False
    assert child_node.style.flex_grow == 1.0

    assert child_node.measure is not None
    measure_width, measure_height = child_node.measure(None, None)
    assert measure_width >= 0
    assert measure_height >= 0


def test_runtime_measure_callback_clamps_negative_values() -> None:
    """Measurement callbacks should never yield negative values."""

    runtime = OrnataRuntime(AppConfig())

    class MeasuringComponent(Component):
        def measure(self) -> ComponentMeasurement:  # type: ignore[override]
            return ComponentMeasurement(width=-10, height=-5)

    callback = runtime._make_measure_callback(MeasuringComponent(component_name="Measure"))
    width, height = callback(None, None)
    assert width == 0
    assert height == 0


def test_runtime_run_executes_pipeline_and_handles_compute_error(monkeypatch: "pytest.MonkeyPatch") -> None:
    """``run`` should proceed even if ``compute_layout`` raises."""

    runtime = OrnataRuntime(AppConfig())

    class StaticStylingRuntime(StylingRuntime):
        def resolve_styles_parallel(self, contexts: Sequence[StylingContext]) -> list[ResolvedStyle]:
            return [ResolvedStyle(width=Length(8)), ResolvedStyle(width=Length(4))]

        def load_stylesheet(self, path: str) -> None:
            return None

    runtime._styling = StaticStylingRuntime()  # noqa: SLF001

    class StubLayoutEngine(LayoutEngine):
        def __init__(self) -> None:
            self.calls = 0

        def calculate_layout(self, component: Component, bounds: object, backend_target: object) -> LayoutResult:  # type: ignore[override]
            self.calls += 1
            return LayoutResult(width=64, height=32)

    dummy_engine = StubLayoutEngine()
    runtime._layout_engine = dummy_engine  # noqa: SLF001

    def failing_compute_layout(*args: object, **kwargs: object) -> None:
        raise RuntimeError("legacy layout failure")

    monkeypatch.setattr(runtime_module, "compute_layout", failing_compute_layout)

    root = _component("Root", text="root")
    child = _component("Child", text="child")
    root.children.append(child)

    frame = runtime.run(root)

    assert frame.root is root
    assert frame.layout.width == 64
    assert frame.styles
    assert runtime.last_gui_tree is not None
    assert dummy_engine.calls == 1


def test_runtime_build_gui_tree_extracts_text() -> None:
    """``_build_gui_tree`` should populate layout, style, and textual metadata."""

    runtime = OrnataRuntime(AppConfig())

    root = _component("Root", text=" Hello World ")
    child = _component("Child")
    child.content = ComponentContent(paragraphs=["  Nested body  "])
    root.children.append(child)

    root_node = LayoutNode(style=LayoutStyle())
    root_node.layout = LayoutResult(x=1, y=2, width=3, height=4)
    child_node = LayoutNode(style=LayoutStyle())
    child_node.layout = LayoutResult(x=5, y=6, width=7, height=8)

    bindings = {
        id(root): root_node,
        id(child): child_node,
    }
    styles = {
        id(root): ResolvedStyle(font="root-font"),
        id(child): ResolvedStyle(font="child-font"),
    }

    gui_root = runtime._build_gui_tree(root, bindings, styles)

    assert gui_root.text == "Hello World"
    assert gui_root.x == 1
    assert gui_root.layout_style is root_node.style
    assert gui_root.children[0].text == "Nested body"
    assert gui_root.children[0].width == 7


def test_runtime_iter_components_depth_first() -> None:
    """``_iter_components`` should yield nodes depth-first."""

    runtime = OrnataRuntime(AppConfig())
    root = _component("root")
    child = _component("child")
    grandchild = _component("grandchild")
    root.children.append(child)
    child.children.append(grandchild)

    sequence = [component.component_name for component in runtime._iter_components(root)]
    assert sequence == ["root", "child", "grandchild"]
