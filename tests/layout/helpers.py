"""Shared helpers for layout subsystem tests."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from ornata.api.exports.definitions import Bounds, ComponentMeasurement
from ornata.api.exports.layout import LayoutNode, LayoutStyle


class DummyComponent:
    """Simple component-like object used to exercise layout algorithms."""

    def __init__(
        self,
        name: str,
        style: LayoutStyle | None = None,
        *,
        measurement: ComponentMeasurement | None = None,
        children: Iterable["DummyComponent"] | None = None,
    ) -> None:
        self.component_name = name
        self._style = style or LayoutStyle()
        self._measurement = measurement or ComponentMeasurement(
            width=self._style.width or 0,
            height=self._style.height or 0,
        )
        self._children = tuple(children or ())

    def iter_children(self) -> tuple["DummyComponent", ...]:
        """Return the immutable children tuple expected by layout APIs."""

        return tuple(self._children)

    def get_layout_style(self) -> LayoutStyle:
        """Return the prepared layout style."""

        return self._style

    def measure(self) -> ComponentMeasurement:
        """Return deterministic measurement results."""

        return self._measurement


def make_layout_node(style: LayoutStyle | None = None, *, children: Sequence[LayoutNode] | None = None) -> LayoutNode:
    """Create a :class:`LayoutNode` with optional children for tests."""

    node = LayoutNode(style=style or LayoutStyle())
    for child in children or ():
        node.add(child)
    return node


def make_bounds(x: int = 0, y: int = 0, width: int = 100, height: int = 50) -> Bounds:
    """Return a bounds instance with sensible defaults for layout tests."""

    return Bounds(x=x, y=y, width=width, height=height)
