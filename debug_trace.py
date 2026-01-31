"""Debug rendering of button."""
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
            text="Launch",
            order=1,
        )
        return ContainerComponent(
            component_name="root",
            children=[header, button],
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

# Monkey-patch renderer to trace
from ornata.rendering.backends.cli.terminal import TerminalRenderer
from ornata.definitions.dataclasses.rendering import UnicodeCanvas

renderer = TerminalRenderer(BackendTarget.CLI)

original_draw_node = renderer._draw_gui_node
def traced_draw_node(canvas, node, *, depth, scale_x, scale_y):
    rect = renderer._scale_rect(node, scale_x, scale_y, canvas.width, canvas.height)
    raw_x = getattr(node, "x", 0)
    raw_y = getattr(node, "y", 0)
    print(f"{'  '*depth}Drawing {node.component_name}: raw=({raw_x},{raw_y}) scale={scale_x:.2f},{scale_y:.2f} rect={rect}")
    return original_draw_node(canvas, node, depth=depth, scale_x=scale_x, scale_y=scale_y)

renderer._draw_gui_node = lambda canvas, node, *, depth, scale_x, scale_y: traced_draw_node(canvas, node, depth=depth, scale_x=scale_x, scale_y=scale_y)

result = renderer.render_tree(gui_tree, frame.layout)
print("\n=== OUTPUT ===")
print(result.content.replace('\x1b', '<ESC>'))
