"""Integration coverage for CLI, TTY, and GUI rendering backends."""

from __future__ import annotations

import io
from types import SimpleNamespace
from typing import Any

import pytest

from examples.mock_app import MissionControlUI
from ornata.api.exports.rendering import ANSIRenderer, TerminalRenderer, TTYRenderer
from ornata.api.exports.rendering import render_tree as gui_render_tree
from ornata.application import AppConfig, BackendTarget, RuntimeFrame
from ornata.core.runtime import OrnataRuntime
from ornata.definitions.dataclasses.layout import LayoutResult
from ornata.definitions.dataclasses.rendering import GuiNode


@pytest.fixture(scope="module")
def mission_frame() -> RuntimeFrame:
    """Build a runtime frame using the Mission Control sample UI."""

    config = AppConfig(
        title="Renderer Coverage",
        backend=BackendTarget.CLI,
        viewport_width=120,
        viewport_height=48,
        stylesheets=[],
    )
    runtime = OrnataRuntime(config)
    ui = MissionControlUI(mission_name="Test Mission")
    return runtime.run(ui.build())


def test_terminal_renderer_produces_unicode_snapshot(mission_frame: RuntimeFrame) -> None:
    """Terminal renderer should produce a UNICODE snapshot for Mission Control."""

    renderer = TerminalRenderer(BackendTarget.CLI)
    output = renderer.render_tree(mission_frame.gui_tree, mission_frame.layout)

    content = _as_text(output.content)
    assert "+ mission-header" in content
    assert "telemetry-table" in content
    assert output.metadata == {
        "canvas_size": (mission_frame.layout.width, mission_frame.layout.height)
    }


def test_ansi_renderer_appends_reset_code(mission_frame: RuntimeFrame) -> None:
    """ANSI renderer wraps the UNICODE snapshot with a reset code."""

    renderer = ANSIRenderer(BackendTarget.CLI)
    output = renderer.render_tree(mission_frame.gui_tree, mission_frame.layout)

    content = _as_text(output.content)
    assert content.endswith("\x1b[0m")
    assert "+ mission-header" in content


@pytest.fixture()
def tty_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace terminal dependencies with deterministic stubs for tests."""

    class StubTerminalController:
        def __init__(self, stream: io.StringIO) -> None:
            self.stream = stream
            self._size = (24, 80)

        def save_state(self) -> SimpleNamespace:
            return SimpleNamespace()

        def restore_state(self, _state: SimpleNamespace | None = None) -> None:  # pragma: no cover - noop
            return None

        def get_size(self) -> tuple[int, int]:
            return self._size

    class StubVT100:
        @staticmethod
        def alternate_screen_enable() -> str:
            return "<ALT>"

        @staticmethod
        def alternate_screen_disable() -> str:
            return "<ALT_OFF>"

        @staticmethod
        def cursor_hide() -> str:
            return "<HIDE>"

        @staticmethod
        def cursor_show() -> str:
            return "<SHOW>"

        @staticmethod
        def cursor_position(row: int, col: int) -> str:
            return f"<POS {row},{col}>"

        @staticmethod
        def erase_display(_mode: Any = None) -> str:
            return "<ERASE>"

        @staticmethod
        def reset() -> str:
            return "<RESET>"

    monkeypatch.setattr("ornata.rendering.backends.tty.termios.TerminalController", StubTerminalController)
    monkeypatch.setattr("ornata.rendering.backends.tty.vt100.VT100", StubVT100)


def test_tty_renderer_stream_output(tty_environment: None) -> None:
    """TTY renderer should write rendered content to the configured stream."""

    stream = io.StringIO()
    renderer = TTYRenderer(BackendTarget.TTY, stream=stream, use_alt_screen=False)

    leaf = SimpleNamespace(props={"content": "TTY Rendered"}, children=[])
    tree = SimpleNamespace(root=leaf)

    output = renderer.render_tree(tree, layout_result=LayoutResult(width=40, height=10))

    stream_value = stream.getvalue()
    assert "TTY Rendered" in stream_value

    content = _as_text(output.content)
    assert "TTY Rendered" in content
    assert output.metadata is not None
    assert output.metadata["terminal_size"] == (24, 80)


def _as_text(content: str | bytes) -> str:
    """Return ``content`` as a UTF-8 string for assertions."""

    if isinstance(content, bytes):
        return content.decode("utf-8", errors="replace")
    return content


class FakeCanvas:
    """Minimal canvas capturing drawing commands for GUI renderer tests."""

    viewport_w: int = 80
    viewport_h: int = 25

    def __init__(self) -> None:
        self.operations: list[tuple[str, tuple[Any, ...]]] = []

    def save(self) -> None:  # pragma: no cover - compatibility shim
        return None

    def restore(self) -> None:  # pragma: no cover - compatibility shim
        return None

    def fill_rect(self, x: int, y: int, w: int, h: int, color: tuple[int, int, int, int]) -> None:
        self.operations.append(("fill_rect", (x, y, w, h, color)))

    def stroke_rect(self, x: int, y: int, w: int, h: int, color: tuple[int, int, int, int], width: int) -> None:
        self.operations.append(("stroke_rect", (x, y, w, h, color, width)))

    def draw_text(
        self,
        x: int,
        y: int,
        text: str,
        color: tuple[int, int, int, int],
        font_face: str | None,
        px: int,
        weight: int | str | None,
    ) -> None:
        self.operations.append(("draw_text", (x, y, text, color, font_face, px, weight)))


def test_gui_renderer_draws_registered_nodes() -> None:
    """GUI renderer should dispatch to registered draw functions for nodes."""

    root = GuiNode(component_name="panel", width=40, height=10)
    text_node = GuiNode(component_name="text", text="Hello", x=2, y=2, width=10, height=1)
    root.children.append(text_node)

    canvas = FakeCanvas()
    gui_render_tree(canvas, root)

    operations = dict(canvas.operations)
    assert "fill_rect" in operations
    assert any(op[0] == "draw_text" for op in canvas.operations)
