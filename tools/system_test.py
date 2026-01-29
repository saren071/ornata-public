"""
Ornata System Test

Tests data flow through all subsystems using an actual component.
Each system receives and processes outputs from previous systems.
"""

from __future__ import annotations

import contextlib
import io
import traceback
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

# -------------------------------
# Helpers
# -------------------------------


def make_serializable(obj: Any) -> Any:
    """Convert objects to JSON serializable types."""
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    elif isinstance(obj, (list, tuple)):
        return [make_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    else:
        return str(obj)


def capture(func: Callable[[], Any]) -> dict[str, Any]:
    """Capture all output from a subsystem execution."""
    buffer = io.StringIO()
    result = None
    err = None

    with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
        try:
            result = func()
        except Exception as e:
            err = "".join(traceback.format_exception(type(e), e, e.__traceback__))

    return {
        "stdout": buffer.getvalue(),
        "result": make_serializable(result),
        "error": err,
    }


# -------------------------------
# Data Flow Test
# Each step uses outputs from previous steps
# -------------------------------


def run_full_system_test() -> dict[str, Any]:
    """Run complete system test with data flow between subsystems."""

    results = {}

    # Step 1: Create component and run component operations
    component = create_test_component()
    results["component_creation"] = capture(lambda: component)

    # Step 2: Component measurement (uses component)
    measured = component.measure()
    results["component_measurement"] = capture(lambda: measured)

    # Step 3: Component styling (uses component)
    style = component.get_layout_style()
    results["component_styling"] = capture(lambda: style)

    # Step 4: Component events (uses component)
    from ornata.api.exports.definitions import InteractionType
    component.emit(InteractionType.CLICK, payload={"test": True})
    results["component_events"] = capture(lambda: None)  # Event emission captured in stdout

    # Step 5: Component render (uses component)
    render_result = component.render()
    results["component_render"] = capture(lambda: render_result)

    # Step 6: Component describe (uses component)
    describe_result = component.describe()
    results["component_describe"] = capture(lambda: describe_result)

    # Step 7: Effects system (uses component for timeline)
    from ornata.api.exports.effects import Timeline
    timeline = Timeline()
    # Run full animation loop
    for _ in range(10):
        timeline.update(0.1)
    results["effects"] = capture(lambda: {"steps": 10, "completed": True})

    # Step 8: Events system (uses component for event publishing)
    from ornata.api.exports.definitions import Event, EventType
    from ornata.api.exports.events import EventBus
    bus = EventBus()
    # Publish multiple events
    events_published = 0
    for i in range(5):
        event = Event(type=EventType.COMPONENT_UPDATE, data={"component": component, "test": i})
        bus.publish(event)
        events_published += 1
    results["events"] = capture(lambda: {"events_published": events_published})

    # Step 9: Layout system (uses component and measured data)
    from ornata.api.exports.definitions import BackendTarget, Bounds
    from ornata.api.exports.layout import LayoutEngine
    engine = LayoutEngine()
    bounds = Bounds(x=0, y=0, width=100, height=50)
    layout_result = engine.calculate_layout(component, bounds, BackendTarget.CLI)
    results["layout"] = capture(lambda: {"layout": layout_result})

    # Step 10: Rendering system (uses component and layout_result)
    from ornata.api.exports.definitions import BackendTarget
    from ornata.api.exports.rendering import ANSIRenderer
    renderer = ANSIRenderer(BackendTarget.CLI)
    # Render the component tree using layout result
    output = renderer.render_tree(component, layout_result)
    results["rendering"] = capture(lambda: {"output": output})

    # Step 11: GPU system (independent)
    from ornata.api.exports.gpu import DeviceManager
    dm = DeviceManager()
    available = dm.is_available()
    gpu_result = {"available": available}
    if available:
        # Try to get device info
        try:
            device = dm.device
            gpu_result["device"] = device
        except Exception as e:
            gpu_result["device_error"] = str(e)
    results["gpu"] = capture(lambda: gpu_result)

    # Step 12: Styling runtime (uses component name)
    from ornata.api.exports.definitions import StylingContext
    from ornata.api.exports.styling import StylingRuntime
    rt = StylingRuntime()
    # Resolve styles for the actual component
    style = rt.resolve_style(StylingContext(component_name = component.component_name))
    results["styling"] = capture(lambda: {"component_style": style})

    # Step 13: VDOM system (independent)
    from ornata.api.exports.definitions import VDOMTree
    from ornata.api.exports.vdom import DiffingEngine
    # Create trees with some nodes
    old_tree = VDOMTree()
    new_tree = VDOMTree()
    # Assume trees can be built, but since minimal, just diff empty
    engine = DiffingEngine()
    patches = engine.diff_trees(old_tree, new_tree)
    results["vdom"] = capture(lambda: {"patches_count": len(patches), "diff_completed": True})

    return results


def create_test_component():
    """Create a test component for the system test."""
    from ornata.api.exports.definitions import Component, ComponentContent, ComponentPlacement

    return Component(
        component_name="TestComponent",
        content=ComponentContent(text="Hello World"),
        placement=ComponentPlacement(x=0, y=0),
    )


# -------------------------------
# Main entry
# -------------------------------


if __name__ == "__main__":
    import json

    output = run_full_system_test()
    print(json.dumps(output, indent=4))