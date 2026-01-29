"""Integration-level coverage for the Ornata layout engine."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import pytest

from ornata.definitions.dataclasses.components import Component, ComponentMeasurement
from ornata.definitions.dataclasses.layout import Bounds, LayoutStyle
from ornata.definitions.enums import BackendTarget
from ornata.layout.engine.engine import LayoutEngine, LayoutNode, compute_layout

if TYPE_CHECKING:
    from pathlib import Path


def _build_layout_node(definition: dict[str, Any]) -> LayoutNode:
    """Construct a :class:`LayoutNode` from a JSON definition."""

    style = LayoutStyle(**definition["style"])
    node = LayoutNode(style=style)
    for child in definition.get("children", []):
        node.add(_build_layout_node(child))
    return node


@pytest.fixture(scope="module")
def layout_scenarios(data_dir: "Path") -> dict[str, Any]:
    """Load canonical layout scenarios defined under ``tests/data``."""

    scenario_path = data_dir / "layout_scenarios.json"
    with scenario_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _edge_value(style: LayoutStyle, attr: str) -> int:
    """Return the resolved padding or margin value for ``attr``."""

    value = getattr(style, attr)
    if value is not None:
        return value
    return style.padding if "padding" in attr else style.margin


def test_compute_layout_wraps_row(layout_scenarios: dict[str, Any]) -> None:
    """Row-based containers wrap overflowing children onto new lines."""

    scenario = layout_scenarios["wrap_row"]
    root = _build_layout_node(scenario)
    result = compute_layout(root, scenario["available_width"], scenario["available_height"])

    first_child = root.children[0]
    last_child = root.children[2]

    assert last_child.layout.y > first_child.layout.y, "overflowing child should drop to next row"

    padding_top = _edge_value(root.style, "padding_top")
    padding_bottom = _edge_value(root.style, "padding_bottom")
    expected_height = (
        first_child.layout.height
        + root.style.gap
        + last_child.layout.height
        + padding_top
        + padding_bottom
    )
    assert result.height == expected_height

    padding_left = _edge_value(root.style, "padding_left")
    padding_right = _edge_value(root.style, "padding_right")
    assert result.width == scenario["available_width"] + padding_left + padding_right


def test_compute_layout_wraps_column(layout_scenarios: dict[str, Any]) -> None:
    """Column containers should start a new column when height is exhausted."""

    scenario = layout_scenarios["wrap_column"]
    root = _build_layout_node(scenario)
    compute_layout(root, scenario["available_width"], scenario["available_height"])

    first_child = root.children[0]
    last_child = root.children[2]

    assert last_child.layout.x > first_child.layout.x

    padding_left = _edge_value(root.style, "padding_left")
    padding_right = _edge_value(root.style, "padding_right")
    assert root.layout.width == last_child.layout.x + last_child.layout.width + padding_left + padding_right


def test_compute_layout_handles_positioning(layout_scenarios: dict[str, Any]) -> None:
    """Absolute and relative nodes must respect their offsets."""

    absolute_input = layout_scenarios["positioning"]["absolute"]
    absolute = _build_layout_node(absolute_input)
    absolute_result = compute_layout(
        absolute,
        absolute_input["available_width"],
        absolute_input["available_height"],
    )
    assert absolute_result.x == absolute_input["style"]["left"]
    assert absolute_result.y == absolute_input["style"]["top"]

    relative_input = layout_scenarios["positioning"]["relative"]
    relative = _build_layout_node(relative_input)
    relative_result = compute_layout(
        relative,
        relative_input["available_width"],
        relative_input["available_height"],
    )
    assert relative_result.x == relative_input["style"]["left"]
    assert relative_result.y == relative_input["style"]["top"]


class SyntheticComponent(Component):
    """Concrete component used to exercise :class:`LayoutEngine`."""

    def __init__(
        self,
        name: str,
        style: LayoutStyle,
        *,
        measurement: ComponentMeasurement | None = None,
        children: list["SyntheticComponent"] | None = None,
    ) -> None:
        super().__init__(component_name=name)
        self._layout_style = style
        self._measurement = measurement or ComponentMeasurement(width=style.width or 0, height=style.height or 0)
        self.children = list(children or [])

    def iter_children(self) -> tuple[Component, ...]:
        """Return the children tuple expected by the engine."""

        return tuple(self.children)

    def get_layout_style(self) -> LayoutStyle:
        """Return the injected layout style."""

        return self._layout_style

    def measure(self) -> ComponentMeasurement:
        """Return deterministic measurement results for the node."""

        return self._measurement


class TrackingConstraint:
    """Test double used to ensure constraints apply adjustments."""

    def __init__(self, *, delta_width: int = 0, delta_height: int = 0) -> None:
        self.delta_width = delta_width
        self.delta_height = delta_height
        self.validate_calls = 0
        self.apply_calls = 0

    def validate(self, component: Component, bounds: Bounds) -> bool:
        """Always fail validation so ``apply`` executes."""

        self.validate_calls += 1
        return False

    def apply(self, component: Component, bounds: Bounds) -> Bounds:
        """Return mutated bounds and track executions."""

        self.apply_calls += 1
        return Bounds(
            x=bounds.x,
            y=bounds.y,
            width=bounds.width + self.delta_width,
            height=bounds.height + self.delta_height,
        )


def test_layout_engine_caches_results() -> None:
    """The engine should return the same cached object for repeated inputs."""

    style = LayoutStyle(width=12, height=4)
    component = SyntheticComponent("Cacheable", style)
    engine = LayoutEngine()
    bounds = Bounds(0, 0, 120, 60)

    first = engine.calculate_layout(component, bounds, BackendTarget.CLI)
    stats_after_first = engine.get_layout_stats()
    second = engine.calculate_layout(component, bounds, BackendTarget.CLI)
    stats_after_second = engine.get_layout_stats()

    assert first is second
    assert stats_after_first["cache_size"] == 1
    assert stats_after_second["cache_size"] == 1


def test_layout_engine_applies_constraints() -> None:
    """Registered constraints must mutate the final layout result."""

    engine = LayoutEngine()
    constraint = TrackingConstraint(delta_width=5, delta_height=3)
    engine.add_constraint(constraint)

    style = LayoutStyle(width=20, height=10)
    component = SyntheticComponent("Constrained", style)
    result = engine.calculate_layout(component, Bounds(0, 0, 100, 100), BackendTarget.GUI)

    assert constraint.validate_calls == 1
    assert constraint.apply_calls == 1
    assert result.width == (style.width or 0) + constraint.delta_width
    assert result.height == (style.height or 0) + constraint.delta_height
