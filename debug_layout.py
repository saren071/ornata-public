"""Debug component layout."""
import sys
sys.path.insert(0, "src")

from datetime import datetime
from ornata.application import (
    AppConfig, Application, BackendTarget,
    ButtonComponent, ContainerComponent, InputComponent,
    InteractionType, TableComponent, TextComponent,
)

class MissionControlUI:
    def build(self):
        header = TextComponent(
            component_name="mission-header",
            title="TEST",
            subtitle="sub",
            order=0,
            label="Header",
        )
        
        button = ButtonComponent(
            component_name="launch-button",
            text="Launch",
            priority=1,
            cacheable=False,
            interactions_types=frozenset({InteractionType.CLICK}),
            order=1,
        )
        
        action_bar = ContainerComponent(
            component_name="action-bar",
            children=[button],
            order=2,
        )
        
        return ContainerComponent(
            component_name="mission-control-root",
            children=[header, action_bar],
        )

config = AppConfig(
    title="Test",
    backend=BackendTarget.CLI,
    stylesheets=["examples/styles/base.osts"],
)
app = Application(config)
ui = MissionControlUI()
app.mount(ui.build)

frame = app._runtime.run(ui.build())
gui_tree = frame.gui_tree

# Print component layout with text content
print("=== Component Layout ===")
def print_node(node, depth=0):
    indent = "  " * depth
    x = getattr(node, "x", 0)
    y = getattr(node, "y", 0)
    w = getattr(node, "width", 0)
    h = getattr(node, "height", 0)
    children = getattr(node, "children", []) or []
    text = getattr(node, "text", None)
    content = getattr(node, "content", None)
    content_text = getattr(content, "text", None) if content else None
    print(f"{indent}{node.component_name}: ({x},{y}) {w}x{h} text={repr(text)} content.text={repr(content_text)}")
    for child in children:
        print_node(child, depth + 1)

print_node(gui_tree)

# Render and check output
from ornata.rendering.backends.cli.terminal import TerminalRenderer
renderer = TerminalRenderer(BackendTarget.CLI)
result = renderer.render_tree(gui_tree, frame.layout)

output = result.content
print("\n=== RENDERED ===")
visible = output.replace('\x1b', '<ESC>')
print(visible)
