"""Debug layout tree building."""
import sys
sys.path.insert(0, "src")

from datetime import datetime
from ornata.application import AppConfig, Application, BackendTarget, ButtonComponent, ContainerComponent, TextComponent

class TestUI:
    def build(self):
        header = TextComponent(
            component_name="mission-header",
            title="HEADER",
            order=0,
        )
        button = ButtonComponent(
            component_name="launch-button",
            text="LAUNCH",
            order=1,
        )
        return ContainerComponent(
            component_name="mission-control-root",
            children=[header, button],
        )

config = AppConfig(
    title="Test",
    backend=BackendTarget.CLI,
    stylesheets=["examples/styles/base.osts"],
)
app = Application(config)
ui = TestUI()
app.mount(ui.build)

# Build and check layout tree
frame = app._runtime.run(ui.build())

print("=== Layout Tree ===")
def print_layout(node, depth=0):
    style = node.style
    layout = getattr(node, 'layout', None)
    print(f"{'  '*depth}Node:")
    print(f"{'  '*depth}  direction: {style.direction}")
    print(f"{'  '*depth}  display: {style.display}")
    if layout:
        print(f"{'  '*depth}  pos: ({layout.x}, {layout.y}) {layout.width}x{layout.height}")
    for child in node.children:
        print_layout(child, depth + 1)

# Get layout tree root
layout_root = app._runtime._layout_tree
print_layout(layout_root)
