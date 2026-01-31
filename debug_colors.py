"""Debug script to check ANSI sequence handling."""

import sys
sys.path.insert(0, "src")

# First, test what the color resolver returns
from ornata.styling.runtime import get_styling_runtime
from ornata.definitions.enums import BackendTarget

runtime = get_styling_runtime()

# Check what styles are resolved for each component
components = [
    "mission-control-root",
    "mission-header",
    "telemetry-table",
    "action-bar",
    "command-entry",
    "launch-button",
]

print("=== Resolved Styles ===")
for name in components:
    payload = runtime.resolve_backend_style(
        type('Context', (), {
            'component_name': name,
            'state': {},
            'theme_overrides': None,
            'caps': None,
            'backend': BackendTarget.CLI,
            'active_states': lambda self: frozenset(),
        })()
    )
    style = payload.style if payload else None
    if style:
        bg = getattr(style, 'background', None)
        fg = getattr(style, 'color', None)
        print(f"{name}:")
        print(f"  bg: {repr(bg) if bg else 'None'}")
        print(f"  fg: {repr(fg) if fg else 'None'}")
    else:
        print(f"{name}: no style")

# Now test actual rendering
print("\n=== Rendering Test ===")
from datetime import datetime
from ornata.application import (
    AppConfig,
    Application,
    BackendTarget,
    ButtonComponent,
    ContainerComponent,
    InputComponent,
    InteractionType,
    TableComponent,
    TextComponent,
)

class TestUI:
    def build(self):
        header = TextComponent(
            component_name="mission-header",
            title="Test",
            subtitle="Subtitle",
            order=0,
            label="Header",
        )
        return ContainerComponent(
            component_name="mission-control-root",
            children=[header],
        )

config = AppConfig(
    title="Test",
    backend=BackendTarget.CLI,
    stylesheets=["examples/styles/base.osts"],
)
app = Application(config)
ui = TestUI()
app.mount(ui.build)

frame = app._runtime.run(ui.build())
gui_tree = frame.gui_tree

# Check what backend_style looks like in the gui_tree
print("\n=== GuiNode backend_style ===")
def check_node(node, depth=0):
    metadata = getattr(node, "metadata", {})
    backend = metadata.get("backend_style")
    indent = "  " * depth
    print(f"{indent}{node.component_name}:")
    if backend and backend.style:
        bg = getattr(backend.style, 'background', None)
        fg = getattr(backend.style, 'color', None)
        print(f"{indent}  bg: {repr(bg)[:60] if bg else 'None'}")
        print(f"{indent}  fg: {repr(fg)[:60] if fg else 'None'}")
    else:
        print(f"{indent}  no backend_style")
    for child in getattr(node, "children", []):
        check_node(child, depth + 1)

check_node(gui_tree)
