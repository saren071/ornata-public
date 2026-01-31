"""Debug the canvas grid contents after render."""
import sys
sys.path.insert(0, "src")

from datetime import datetime
from ornata.application import AppConfig, Application, BackendTarget, TextComponent, ContainerComponent

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

from ornata.rendering.backends.cli.terminal import TerminalRenderer
from ornata.definitions.dataclasses.rendering import UnicodeCanvas

renderer = TerminalRenderer(BackendTarget.CLI)

# Monkey-patch to inspect canvas after render
original_render = renderer._render_gui_snapshot
def patched_render(canvas, root, depth, scale_x, scale_y):
    result = original_render(canvas, root, depth, scale_x, scale_y)
    
    # Inspect the grid
    print("=== CANVAS GRID (first 5 rows, first 30 cols) ===")
    for row_idx in range(min(5, canvas.height)):
        row = canvas._grid[row_idx][:30]
        visible = []
        for ch in row:
            if ord(ch) < 32:
                visible.append(f"\\x{ord(ch):02x}")
            else:
                visible.append(ch)
        print(f"Row {row_idx}: {''.join(visible)}")
    
    return result

renderer._render_gui_snapshot = lambda canvas, root, depth=0, scale_x=1.0, scale_y=1.0: patched_render(canvas, root, depth, scale_x, scale_y)

result = renderer.render_tree(gui_tree, frame.layout)
print("\n=== RENDERED ===")
print(repr(result.content[:200]))
