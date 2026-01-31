"""Debug color application."""
import sys
sys.path.insert(0, "src")

from datetime import datetime
from ornata.application import AppConfig, Application, BackendTarget, TextComponent, ContainerComponent

class TestUI:
    def build(self):
        header = TextComponent(
            component_name="mission-header",
            title="TEST",
            subtitle="sub",
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

# Trace the rendering
from ornata.rendering.backends.cli.terminal import TerminalRenderer
from ornata.definitions.dataclasses.rendering import UnicodeCanvas

renderer = TerminalRenderer(BackendTarget.CLI)

# Check what fg_seq is for mission-header
def trace_node(node, depth=0):
    metadata = getattr(node, "metadata", {})
    backend = metadata.get("backend_style")
    fg_seq = ""
    if backend and backend.style:
        fg_seq = backend.style.color if isinstance(getattr(backend.style, "color", None), str) else ""
    
    children = getattr(node, "children", []) or []
    is_leaf = not children
    
    print(f"{'  '*depth}{node.component_name}: leaf={is_leaf}, fg={repr(fg_seq)[:30] if fg_seq else 'None'}")
    
    for child in children:
        trace_node(child, depth + 1)

print("=== GuiNode color trace ===")
trace_node(gui_tree)
