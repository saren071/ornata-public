"""Debug action bar rendering."""
import sys
sys.path.insert(0, "src")

from datetime import datetime
from ornata.application import AppConfig, Application, BackendTarget, ButtonComponent, ContainerComponent, InputComponent, InteractionType, TextComponent

class TestUI:
    def build(self):
        header = TextComponent(
            component_name="mission-header",
            title="HEADER",
            order=0,
        )
        input_field = InputComponent(
            component_name="command-entry",
            placeholder="Type...",
            order=1,
        )
        button = ButtonComponent(
            component_name="launch-button",
            text="LAUNCH",
            order=2,
        )
        action_bar = ContainerComponent(
            component_name="action-bar",
            children=[input_field, button],
            order=3,
        )
        return ContainerComponent(
            component_name="root",
            children=[header, action_bar],
        )

config = AppConfig(
    title="Test",
    backend=BackendTarget.CLI,
    stylesheets=["examples/styles/base.osts"],
)
app = Application(config)
app.mount(TestUI().build)

frame = app._runtime.run(TestUI().build())
gui_tree = frame.gui_tree

# Check layout positions
print("=== Layout Positions ===")
def check_layout(node, depth=0):
    x = getattr(node, "x", 0)
    y = getattr(node, "y", 0)
    w = getattr(node, "width", 0)
    h = getattr(node, "height", 0)
    children = getattr(node, "children", []) or []
    print(f"{'  '*depth}{node.component_name}: ({x},{y}) {w}x{h}")
    for child in children:
        check_layout(child, depth + 1)

check_layout(gui_tree)

# Get canvas dimensions
from ornata.rendering.backends.cli.terminal import TerminalRenderer
renderer = TerminalRenderer(BackendTarget.CLI)

layout_width = getattr(frame.layout, "width", 100)
layout_height = getattr(frame.layout, "height", 40)
print(f"\nLayout size: {layout_width}x{layout_height}")

canvas_width = min(200, max(60, layout_width))
canvas_height = min(80, max(20, layout_height))
print(f"Canvas size: {canvas_width}x{canvas_height}")

scale_x = canvas_width / layout_width if layout_width > canvas_width else 1.0
scale_y = canvas_height / layout_height if layout_height > canvas_height else 1.0
print(f"Scale: {scale_x:.2f}, {scale_y:.2f}")

# Check scaled positions for action-bar
for node in [gui_tree] + gui_tree.children:
    if hasattr(node, "children"):
        for child in node.children:
            if "action" in child.component_name or "launch" in child.component_name or "command" in child.component_name:
                rect = renderer._scale_rect(child, scale_x, scale_y, canvas_width, canvas_height)
                print(f"{child.component_name}: raw=({child.x},{child.y}) scaled={rect}")
