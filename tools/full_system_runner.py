"""
Full System Runner

Runs the entire Ornata system end-to-end using the Application API,
capturing and displaying the results from each major system component.
Each system's output is passed as input to the subsequent system.
"""

from __future__ import annotations

import contextlib
import io
import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

from ornata.api.exports.definitions import (
    Alignment,
    BackendTarget,
    ComponentAccessibility,
    ComponentContent,
    ComponentPlacement,
    ComponentRenderHints,
    Event,
    EventType,
    InteractionDescriptor,
    InteractionType,
    VDOMTree,
)
from ornata.api.exports.effects import Timeline
from ornata.api.exports.events import EventBus
from ornata.api.exports.gpu import DeviceManager
from ornata.api.exports.rendering import ANSIRenderer, TTYRenderer
from ornata.api.exports.vdom import DiffingEngine
from ornata.application import AppConfig, Application
from ornata.components import (
    ButtonComponent,
    ContainerComponent,
    InputComponent,
    TableComponent,
    TextComponent,
)

# -------------------------------
# Helpers (same as system_test.py)
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
# Full System Test
# -------------------------------


def run_full_system() -> dict[str, Any]:
    """Run the complete Ornata system end-to-end."""

    results = {}

    # Step 1: Component Building System
    # Build the component tree
    component = create_test_app_component()
    # Extract references for later use
    # header = component.children[0]  # Not used after effects simplification
    button = component.children[1]
    input_field = component.children[2]
    # table = component.children[3]  # Not used
    results["component_build"] = capture(lambda: component)

    # Step 2: Application Configuration and Setup
    config = AppConfig(
        title="Full System Test",
        backend=BackendTarget.CLI,
        viewport_width=120,
        viewport_height=40,
        stylesheets=["examples/styles/base.osts"],
    )
    app = Application(config)
    app.mount(lambda: component)  # Mount the component factory
    results["app_setup"] = capture(lambda: {"config": config, "app": app})

    # Step 3: Runtime System (Styling, Layout, VDOM)
    # Run the full application cycle
    frame = app.run()
    results["runtime_orchestration"] = capture(lambda: {
        "root_component": frame.root,
        "layout_result": frame.layout,
        "resolved_styles": dict(frame.styles),
        "gui_tree": frame.gui_tree,
    })

    # Step 4: Rendering System
    # Render the GUI tree using the layout
    renderer = ANSIRenderer(BackendTarget.CLI)
    render_output = renderer.render_tree(frame.gui_tree, frame.layout)
    results["rendering_cli"] = capture(lambda: {
        "output_content": render_output.content,
        "output_type": type(render_output.content).__name__,
    })

    # Test TTY backend
    app.set_backend(BackendTarget.TTY)
    frame_tty = app.run()
    renderer_tty = TTYRenderer(BackendTarget.TTY)
    render_output_tty = renderer_tty.render_tree(frame_tty.gui_tree, frame_tty.layout)
    results["rendering_tty"] = capture(lambda: {
        "output_content": render_output_tty.content,
        "output_type": type(render_output_tty.content).__name__,
    })

    # Switch back to CLI for consistency
    app.set_backend(BackendTarget.CLI)

    # Step 5: GPU System (Check availability)
    dm = DeviceManager()
    available = dm.is_available()
    gpu_result: dict[str, Any] = {"available": available}
    if available:
        try:
            device = dm.device
            gpu_result["device"] = device
        except Exception as e:
            gpu_result["device_error"] = str(e)
    results["gpu"] = capture(lambda: gpu_result)

    # Step 6: Event System (Test event publishing and handling)
    bus = EventBus()
    events_published = 0
    # Publish component-specific events
    for i in range(3):
        # Emit click on button
        button.emit(InteractionType.CLICK, payload={"test": i, "component": button})
        # Emit change on input
        input_field.emit(InteractionType.CHANGE, payload={"value": f"changed_{i}"})
        events_published += 2
    # Also publish generic events
    for i in range(2):
        event = Event(type=EventType.COMPONENT_UPDATE, data={"test": i})
        bus.publish(event)
        events_published += 1
    results["events"] = capture(lambda: {"events_published": events_published, "handlers_registered": True})

    # Step 7: Effects System (Run timeline)
    timeline = Timeline()
    steps = 10
    for _ in range(steps):
        timeline.update(0.1)
    results["effects"] = capture(lambda: {"steps": steps, "completed": True})

    # Step 8: VDOM System (Diff test)
    old_tree = VDOMTree()
    new_tree = VDOMTree()
    engine = DiffingEngine()
    patches = engine.diff_trees(old_tree, new_tree)
    results["vdom"] = capture(lambda: {"patches_count": len(patches), "diff_completed": True})

    return results


def create_test_app_component():
    """Create a comprehensive test component tree with all features exercised."""

    # Create a text component with full content
    header = TextComponent(
        component_name="comprehensive-header",
        component_id="header-001",
        key="header-key",
        name="Header Name",
        variant="header-variant",
        intent="informative",
        role="banner",
        content=ComponentContent(
            title="Ornata Full System Test",
            subtitle="Testing Every Aspect",
            heading="H1",
            subheading="Sub",
            text="Welcome to the comprehensive test",
            body="This tests all components and features",
            paragraphs=["Paragraph 1", "Paragraph 2"],
            caption="Test Caption",
            tooltip="Tooltip text",
            status_text="Status: OK",
            placeholder="Enter text",
            prefix="Prefix",
            suffix="Suffix",
            icon="icon-test",
            icon_alt="Alt icon",
            media_source="media.mp4",
            media_alt="Alt media",
            thumbnail_source="thumb.jpg",
            actions=["Do Something"],
        ),
        placement=ComponentPlacement(
            x=10, y=5, z_index=1, layer="main", row=0, column=0, order=0,
            anchor=Alignment.START, rotation=0, scale_x=1.0, scale_y=1.0
        ),
        accessibility=ComponentAccessibility(
            label="Header", description="Main header", role="heading", hint="Important", language="en",
            live_region="polite", tab_index=0, shortcut="Ctrl+H", announces=True, is_modal=False
        ),
        interactions=InteractionDescriptor(
            types=frozenset({InteractionType.CLICK, InteractionType.FOCUS}),
            debounce_ms=100, repeat_interval_ms=200, cursor="pointer", is_toggle=True, accelerator="Ctrl+H"
        ),
        render_hints=ComponentRenderHints(
            layer="foreground", priority=1, cacheable=True, prefers_gpu=True, prefers_text_engine=False,
            offscreen=False, rtl=False, hydration_key="header-render"
        ),
    )

    # Create a button with full configuration
    button = ButtonComponent(
        component_name="test-button",
        component_id="button-001",
        key="button-key",
        name="Button Name",
        variant="primary",
        intent="action",
        role="button",
        content=ComponentContent(
            text="Click Me",
            tooltip="A test button",
            status_text="Button status",
            icon="btn-icon",
            actions=["btn action"]
        ),
        placement=ComponentPlacement(
            order=1, x=5, y=12, z_index=2, layer="ui", row=0, column=1,
            anchor=Alignment.CENTER, rotation=15, scale_x=1.0, scale_y=1.0
        ),
        accessibility=ComponentAccessibility(
            label="Test Button", description="Primary action trigger", role="button",
            hint="Click to test", language="en-US", shortcut="Ctrl+B", announces=True
        ),
        interactions=InteractionDescriptor(
            types=frozenset({InteractionType.CLICK, InteractionType.PRESS}),
            debounce_ms=40,
            cursor="pointer",
            is_toggle=False,
            accelerator="Ctrl+B",
        ),
        render_hints=ComponentRenderHints(
            layer="foreground", priority=2, cacheable=True, prefers_gpu=False, prefers_text_engine=True,
            offscreen=False, rtl=False, hydration_key="button-hydration"
        ),
    )
    button.register_event_handler(InteractionType.CLICK, lambda e: print("Button clicked"))

    # Create an input field with full configuration
    input_field = InputComponent(
        component_name="test-input",
        component_id="input-001",
        key="input-key",
        name="Input Name",
        variant="outlined",
        intent="input",
        role="textbox",
        content=ComponentContent(
            placeholder="Type here",
            tooltip="Input field tooltip",
            status_text="Input status"
        ),
        value="initial text",
        secondary_value="secondary",
        min_value=0,
        max_value=100,
        step_value=1,
        placeholder_value="Start typing",
        status="ready",
        placement=ComponentPlacement(
            order=2, layer="input", x=15, y=8, z_index=3, anchor=Alignment.END,
            rotation=0, scale_x=1.0, scale_y=1.0, row=0, column=2
        ),
        accessibility=ComponentAccessibility(
            label="Test Input", description="Accepts test text", role="textbox",
            hint="Type something", language="en-US", shortcut="Ctrl+I", announces=False
        ),
        interactions=InteractionDescriptor(
            types=frozenset({InteractionType.CHANGE, InteractionType.SUBMIT, InteractionType.FOCUS}),
            debounce_ms=150,
            repeat_interval_ms=250,
            cursor="text",
            accelerator="Ctrl+I",
        ),
        render_hints=ComponentRenderHints(
            layer="input", priority=3, cacheable=False, prefers_gpu=False, prefers_text_engine=True,
            offscreen=False, rtl=False, hydration_key="input-hydration"
        ),
        icon_slot="input-icon",
        badge_text="Live",
        shortcuts=["Enter"],
        locale="en-US",
        timestamp=1.0,
        animations=["pulse"],
        transitions=["fade"],
    )

    # Create a table with full configuration
    table = TableComponent(
        component_name="test-table",
        component_id="table-001",
        key="table-key",
        name="Table Name",
        variant="striped",
        intent="data",
        role="table",
        content=ComponentContent(
            tooltip="Table tooltip",
            status_text="Table status"
        ),
        columns=["ID", "Name", "Status"],
        rows=[
            ["1", "Component A", "Active"],
            ["2", "Component B", "Inactive"],
            ["3", "Component C", "Pending"],
        ],
        selection_mode="single",
        selection=[0],
        sorting={"column": "ID", "direction": "asc"},
        grouping={"column": "Status"},
        filter_expression="Status == 'Active'",
        page_index=0,
        page_size=10,
        total_count=3,
        placement=ComponentPlacement(
            order=3, layer="table", x=5, y=20, z_index=4, anchor=Alignment.START,
            rotation=0, scale_x=1.0, scale_y=1.0, row=1, column=0
        ),
        accessibility=ComponentAccessibility(
            label="Test Table", description="Displays component data", role="table",
            hint="Table of components", language="en-US", announces=False
        ),
        interactions=InteractionDescriptor(types=frozenset({InteractionType.SELECT})),
        render_hints=ComponentRenderHints(
            layer="background", priority=1, cacheable=True, prefers_gpu=False, prefers_text_engine=False,
            offscreen=False, rtl=False, hydration_key="table-hydration"
        ),
    )

    # Create a container with all children, fully configured
    return ContainerComponent(
        component_name="comprehensive-root",
        component_id="root-001",
        key="root-key",
        name="Root Name",
        variant="container-variant",
        intent="layout",
        role="main",
        content=ComponentContent(
            title="Root Container",
            subtitle="Holds all test components",
            text="Root text",
            body="Root body",
            paragraphs=["Root para"],
            caption="Root caption",
            tooltip="Root tooltip",
            status_text="Root status",
            placeholder="Root placeholder",
            prefix="Root prefix",
            suffix="Root suffix",
            icon="root-icon",
            icon_alt="Root icon alt",
            media_source="root.mp4",
            media_alt="Root media alt",
            thumbnail_source="root.jpg",
            actions=["root action"]
        ),
        placement=ComponentPlacement(
            x=0, y=0, z_index=0, layer="root", row=0, column=0, order=0,
            anchor=Alignment.CENTER, rotation=0, scale_x=1.0, scale_y=1.0
        ),
        accessibility=ComponentAccessibility(
            label="Root Container", description="Root description", role="group", hint="Root hint",
            language="en", live_region="polite", tab_index=0, shortcut="Ctrl+R", announces=True, is_modal=False
        ),
        interactions=InteractionDescriptor(
            types=frozenset({InteractionType.CLICK}),
            debounce_ms=50, repeat_interval_ms=100, cursor="default", is_toggle=False, accelerator="Ctrl+R"
        ),
        render_hints=ComponentRenderHints(
            layer="background", priority=0, cacheable=True, prefers_gpu=False, prefers_text_engine=True,
            offscreen=False, rtl=False, hydration_key="root-key"
        ),
        children=[header, button, input_field, table],
    )


# -------------------------------
# Main entry
# -------------------------------


if __name__ == "__main__":
    import traceback  # Import here for capture function

    try:
        output = run_full_system()
        print(json.dumps(output, indent=2))
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
