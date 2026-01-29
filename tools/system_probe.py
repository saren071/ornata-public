"""
Ornata System Probe

Runs each subsystem in isolation, captures ALL output (stdout, logs,
print statements, trace messages, errors), and returns a structured
contract of what each subsystem produced.

Run with:
    python -m tools.system_probe
"""

from __future__ import annotations

import contextlib
import io
import traceback
from collections import Counter
from typing import TYPE_CHECKING, Any, Callable

from ornata.api.exports.definitions import BackendTarget

if TYPE_CHECKING:
    from ornata.api.exports.definitions import Component, VDOMTree

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

def create_feature_complete_component() -> "Component":
    """Return a component that exercises every exposed capability."""
    from ornata.api.exports.definitions import (
        Alignment,
        Component,
        ComponentAccessibility,
        ComponentContent,
        ComponentDataBinding,
        ComponentKind,
        ComponentPlacement,
        ComponentRenderHints,
        InteractionDescriptor,
        InteractionType,
    )

    component = Component(
        component_name="ProbeComponent",
        component_id="probe-root",
        key="probe-root",
        name="ProbeComponent",
        kind=ComponentKind.BUTTON,
        variant="probe",
        intent="primary",
        role="button",
        content=ComponentContent(
            title="Subsystem Probe",
            subtitle="Exercises every component capability",
            heading="Probe Heading",
            subheading="Detailed subheading",
            text="A text body that should be measured and rendered.",
            body="The system probe relies on this rich body text.",
            paragraphs=["Paragraph 1", "Paragraph 2"],
            caption="Caption text",
            tooltip="Probe tooltip",
            status_text="Ready",
            placeholder="Enter probe data",
            prefix=">>",
            suffix="<<",
            icon="probe-icon",
            icon_alt="Probe icon description",
            media_source="media.png",
            media_alt="Media alternative",
            thumbnail_source="thumb.png",
            actions=["confirm", "dismiss"],
        ),
        placement=ComponentPlacement(
            x=5.0,
            y=10.0,
            z_index=3,
            layer="probe-layer",
            row=1,
            column=2,
            order=0,
            anchor=Alignment.CENTER,
            rotation=0.15,
            scale_x=1.1,
            scale_y=0.9,
        ),
        accessibility=ComponentAccessibility(
            label="Probe component",
            description="Captures every component feature",
            role="probe",
            hint="Activate to inspect subsystems",
            language="en-US",
            live_region="polite",
            tab_index=0,
            shortcut="Ctrl+P",
            announces=True,
            is_modal=False,
        ),
        interactions=InteractionDescriptor(
            types=frozenset({InteractionType.CLICK, InteractionType.HOVER}),
            debounce_ms=120,
            repeat_interval_ms=250,
            cursor="pointer",
            is_toggle=True,
            accelerator="Ctrl+Shift+P",
        ),
        render_hints=ComponentRenderHints(
            layer="probe-layer",
            priority=5,
            cacheable=True,
            prefers_gpu=True,
            prefers_text_engine=False,
            offscreen=False,
            rtl=False,
            hydration_key="probe-root",
        ),
        bindings=[
            ComponentDataBinding(
                source="probe_source",
                path="value",
                formatter="json.dumps",
                parser="json.loads",
                locale="en-US",
                is_two_way=True,
            )
        ],
    )

    component.states["default"] = True
    component.states["expanded"] = False
    component.data = {"probe_flag": True, "status": "initialized"}
    component.meta = {"probe": True, "variant": "initial"}
    component.dataset = [{"id": 1, "value": "one"}, {"id": 2, "value": "two"}]
    component.items = ["item-one", "item-two"]
    component.columns = ["id", "value"]
    component.rows = [[1, "one"], [2, "two"]]
    component.selection = [0, 1]
    component.selection_mode = "multiple"
    component.sorting = "asc"
    component.grouping = "category"
    component.filter_expression = "value != ''"
    component.page_index = 0
    component.page_size = 20
    component.total_count = 2
    component.value = 42
    component.secondary_value = {"detail": "secondary"}
    component.min_value = 0
    component.max_value = 100
    component.step_value = 5
    component.placeholder_value = "Probe placeholder"
    component.status = "ready"
    component.icon_slot = "leading"
    component.badge_text = "Probe"
    component.tooltip = "Detailed probe component"
    component.shortcuts = ["Ctrl+P", "Alt+P"]
    component.locale = "en-US"
    component.timestamp = 1.0
    component.animations = ["pulse"]
    component.transitions = ["slide"]
    component.visible = True
    component.enabled = True
    component.focusable = True
    return component


def build_child_component(name: str, key: str, text: str) -> "Component":
    """Create a child component used for diff coverage."""
    from ornata.api.exports.definitions import Component, ComponentContent

    child = Component(
        component_name=name,
        component_id=f"{key}-id",
        key=key,
        content=ComponentContent(text=text),
    )
    child.visible = True
    child.enabled = True
    return child


def build_vdom_pair() -> tuple["VDOMTree", "VDOMTree"]:
    """Return old/new VDOM trees that capture adds, removes, updates, and moves."""
    from ornata.api.exports.definitions import BackendTarget
    from ornata.api.exports.vdom import create_vdom_tree

    root_old = create_feature_complete_component()
    root_old.component_id = "probe-root"
    root_old.key = "probe-root"

    for child in [
        build_child_component("BaseChildA", "child-a", "Base Child A"),
        build_child_component("BaseChildB", "child-b", "Base Child B"),
        build_child_component("BaseChildD", "child-d", "Obsolete child"),
    ]:
        root_old.add_child(child)

    root_new = create_feature_complete_component()
    root_new.component_id = "probe-root"
    root_new.key = "probe-root"
    root_new.content.title = "Updated Probe Root"
    root_new.states["expanded"] = True
    root_new.data["probe_flag"] = False
    root_new.meta["probe"] = "variant"
    root_new.meta["phase"] = "updated"

    for child in [
        build_child_component("VariantChildB", "child-b", "Updated child B"),
        build_child_component("VariantChildA", "child-a", "Updated child A"),
        build_child_component("VariantChildE", "child-e", "New child E"),
    ]:
        root_new.add_child(child)

    old_tree = create_vdom_tree(root_old, BackendTarget.GUI)
    new_tree = create_vdom_tree(root_new, BackendTarget.GUI)
    return old_tree, new_tree

# -------------------------------
# Subsystem Runners
# Each runner should *not* modify Ornata state globally.
# They only instantiate or minimally exercise each system.
# -------------------------------


def run_components() -> Any:
    from ornata.api.exports.definitions import (
        Component,
        ComponentContent,
        ComponentPlacement,
        InteractionType,
    )

    parent = Component(
        component_name="ParentComponent",
        content=ComponentContent(title="Parent", text="Parent text"),
        placement=ComponentPlacement(x=0, y=0),
    )
    child = Component(
        component_name="ChildComponent",
        content=ComponentContent(title="Child", text="Child text"),
        placement=ComponentPlacement(x=5, y=1),
    )
    parent.add_child(child)
    sibling = Component(
        component_name="SiblingComponent",
        content=ComponentContent(text="Sib"),
        placement=ComponentPlacement(x=2, y=3),
    )
    parent.add_child(sibling)

    measured = parent.measure()
    layout_style = parent.get_layout_style()
    parent.emit(InteractionType.HOVER, payload={"hover": True})
    parent.emit(InteractionType.CLICK, payload={"click": True})
    render_res = parent.render()
    describe_res = parent.describe()
    return {
        "measured": measured,
        "layout_style": layout_style,
        "render": render_res,
        "describe": describe_res,
        "children": [child.describe(), sibling.describe()],
    }


def run_effects() -> Any:
    from ornata.api.exports.effects import Timeline
    from ornata.effects.timeline import FrameCache

    timeline = Timeline()
    cache = FrameCache(max_history=5)
    rendered_frames: list[str] = []
    diffs: list[tuple[int, str]] = []
    for step in range(6):
        timeline.update(0.04)
        frame = f"frame-{step}-{timeline}"  # placeholder representation
        cache.update(frame)
        diffs = cache.diff()
        rendered_frames.append(frame)
    # ensure diffs safe when unmatched lengths
    sanitized: list[tuple[int, str]] = [(idx, line) for idx, line in diffs]
    return {
        "steps": 6,
        "history": cache.history(),
        "diffs": sanitized,
        "exports": rendered_frames,
        "cache_size": len(cache.history()),
    }


def run_events() -> Any:
    from ornata.api.exports.definitions import Event, EventType
    from ornata.api.exports.events import EventBus

    bus = EventBus()
    handled: list[str] = []

    def handler(event: Event) -> None:
        handled.append(f"{event.type.value}:{event.data}")

    bus.set_coalescing_enabled(True)
    unsub = bus.subscribe(EventType.COMPONENT_UPDATE.value, handler)
    events_published = 0
    for i in range(8):
        event = Event(
            type=EventType.COMPONENT_UPDATE,
            data={"index": i, "timestamp": i * 0.1},
        )
        bus.publish(event)
        events_published += 1
    unsub()
    return {"events_published": events_published, "handlers": handled}


def run_layout() -> Any:
    from ornata.api.exports.definitions import Bounds, Component, ComponentContent, ComponentPlacement
    from ornata.api.exports.layout import LayoutEngine

    components = [
        Component(component_name="CompA", content=ComponentContent(text="A"), placement=ComponentPlacement(x=0, y=0)),
        Component(component_name="CompB", content=ComponentContent(text="B"), placement=ComponentPlacement(x=5, y=1)),
        Component(component_name="CompC", content=ComponentContent(text="C"), placement=ComponentPlacement(x=10, y=2)),
    ]
    engine = LayoutEngine()
    bounds = Bounds(x=0, y=0, width=200, height=80)
    layout = engine.calculate_layout(components[0], bounds, BackendTarget.CLI)
    cascade = [engine.calculate_layout(c, bounds, BackendTarget.CLI) for c in components[1:]]
    stats = engine.get_layout_stats()
    return {"layout": layout, "cascade": cascade, "stats": stats}


def run_rendering() -> Any:
    from ornata.api.exports.definitions import Component, ComponentContent, ComponentPlacement
    from ornata.api.exports.rendering import ANSIRenderer

    tree_root = Component(
        component_name="RenderRoot",
        content=ComponentContent(title="Tree", text="Multi child"),
        placement=ComponentPlacement(x=0, y=0),
    )
    for idx in range(3):
        child = Component(
            component_name=f"RenderChild{idx}",
            content=ComponentContent(text=f"child-{idx}"),
            placement=ComponentPlacement(x=idx * 2, y=idx),
        )
        tree_root.add_child(child)
    renderer = ANSIRenderer(BackendTarget.CLI)
    layout = tree_root.get_layout_style()
    output = renderer.render_tree(tree_root, layout)
    return {
        "output": output,
        "layout_style": repr(layout),
        "rendered_children": [repr(child.content) for child in tree_root.iter_children()],
    }


def run_gpu() -> Any:
    from ornata.api.exports.gpu import DeviceManager, load_fragment_program_source, load_vertex_program_source
    from ornata.gpu.device.geometry import component_to_gpu_geometry

    dm = DeviceManager()
    available = dm.is_available()
    result: dict[str, Any] = {"available": available}
    if not available:
        return result
    device = dm.device
    shader_name = "probe-shader"
    vertex_src = load_vertex_program_source()
    fragment_src = load_fragment_program_source()
    shader = dm.create_shader(shader_name, vertex_src, fragment_src)
    component = create_feature_complete_component()
    geometry = component_to_gpu_geometry(component)
    dm.render_geometry(geometry, shader)
    return {
        "available": True,
        "device": device,
        "shader": shader_name,
        "vertex_count": geometry.vertex_count,
        "index_count": geometry.index_count,
    }


def run_styling() -> Any:
    from ornata.api.exports.definitions import StylingContext
    from ornata.api.exports.styling import StylingRuntime

    rt = StylingRuntime()
    contexts = [
        StylingContext(component_name="button", state={"default": True}),
        StylingContext(component_name="text", state={"emphasis": True}),
        StylingContext(component_name="container", state={"focused": True}),
    ]
    resolved = [rt.resolve_style(ctx) for ctx in contexts]
    stats = rt.get_style_stats()
    return {
        "resolved": [str(style) for style in resolved],
        "stats": stats,
        "style_version": stats.get("style_version"),
        "theme_version": stats.get("theme_version"),
    }


def run_vdom() -> Any:
    from ornata.api.exports.vdom import DiffingEngine

    old_tree, new_tree = build_vdom_pair()
    engine = DiffingEngine()
    patches = engine.diff_trees(old_tree, new_tree)
    summary = Counter(patch.patch_type for patch in patches)
    patch_summary = {patch_type.value: count for patch_type, count in summary.items()}
    sample_patch = patches[0] if patches else None
    return {
        "patches_count": len(patches),
        "patches_by_type": patch_summary,
        "old_tree_nodes": getattr(old_tree, "node_count", None),
        "new_tree_nodes": getattr(new_tree, "node_count", None),
        "sample_patch": {
            "type": sample_patch.patch_type.value if sample_patch else None,
            "key": sample_patch.key if sample_patch else None,
            "data": str(sample_patch.data) if sample_patch else None,
        },
        "diff_completed": True,
    }


SYSTEMS: dict[str, Callable[[], dict[str, Any]]] = {
    "components": run_components,
    "effects": run_effects,
    "events": run_events,
    "layout": run_layout,
    "rendering": run_rendering,
    "gpu": run_gpu,
    "styling": run_styling,
    "vdom": run_vdom,
}


# -------------------------------
# Main entry
# -------------------------------


def run_probe() -> dict[str, dict[str, Any]]:
    final: dict[str, dict[str, Any]] = {}
    for name, fn in SYSTEMS.items():
        final[name] = capture(fn)
    return final


if __name__ == "__main__":
    import json

    output = run_probe()
    print(json.dumps(output, indent=4))
