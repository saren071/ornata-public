"""Test action bar rendering."""
import sys
sys.path.insert(0, "src")

from datetime import datetime
from ornata.application import AppConfig, Application, BackendTarget, ButtonComponent, ContainerComponent, InputComponent, TableComponent, TextComponent

class TestUI:
    def build(self):
        header = TextComponent(
            component_name="mission-header",
            title="HEADER",
            order=0,
        )
        input_field = InputComponent(
            component_name="command-entry",
            placeholder="Type command...",
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
            component_name="mission-control-root",
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

# Render and check output
from ornata.rendering.backends.cli.terminal import TerminalRenderer
renderer = TerminalRenderer(BackendTarget.CLI)
result = renderer.render_tree(frame.gui_tree, frame.layout)

output = result.content
print("=== RENDERED OUTPUT ===")
print(output.replace('\x1b', '<ESC>'))

# Debug GuiNode content
print("\n=== GuiNode tree ===")
def debug_node(node, depth=0):
    text = getattr(node, 'text', None)
    content = getattr(node, 'content', None)
    content_text = getattr(content, 'text', None) if content else None
    placeholder = getattr(content, 'placeholder', None) if content else None
    x = getattr(node, 'x', 0)
    y = getattr(node, 'y', 0)
    w = getattr(node, 'width', 0)
    h = getattr(node, 'height', 0)
    children = getattr(node, 'children', []) or []
    print(f"{'  '*depth}{node.component_name}:")
    print(f"{'  '*depth}  pos=({x},{y}) {w}x{h}")
    print(f"{'  '*depth}  text={repr(text)}")
    print(f"{'  '*depth}  content.text={repr(content_text)}")
    print(f"{'  '*depth}  content.placeholder={repr(placeholder)}")
    print(f"{'  '*depth}  children={len(children)}")
    for child in children:
        debug_node(child, depth + 1)

debug_node(frame.gui_tree)

# Check layout bounds
print("\n=== Layout bounds ===")
layout = frame.layout
print(f"Layout type: {type(layout)}")
print(f"Layout attrs: {dir(layout)}")
print(f"Layout: {getattr(layout, 'width', 'N/A')}x{getattr(layout, 'height', 'N/A')}")
for attr in ['width', 'height', 'x', 'y', 'bounds']:
    val = getattr(layout, attr, 'N/A')
    print(f"  layout.{attr} = {val}")

# Check if action bar components are present
if 'LAUNCH' in output:
    print("\n✓ Launch button found")
else:
    print("\n✗ Launch button NOT found")

if 'Type command' in output or 'command' in output.lower():
    print("✓ Input field found")
else:
    print("✗ Input field NOT found")
