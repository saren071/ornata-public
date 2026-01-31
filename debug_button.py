"""Debug button rendering."""
import sys
sys.path.insert(0, "src")

from ornata.application import AppConfig, Application, BackendTarget, ButtonComponent, ContainerComponent, InputComponent, TextComponent

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

# Debug render
from ornata.rendering.backends.cli.terminal import TerminalRenderer
renderer = TerminalRenderer(BackendTarget.CLI)

# Get the button node
root = frame.gui_tree
action_bar = root.children[1]
button = action_bar.children[1]

print(f"Button node: x={button.x}, y={button.y}, w={button.width}, h={button.height}")
print(f"Button text: {getattr(button, 'text', None)}")

# Check if button rect would be clipped
canvas_width = 60
canvas_height = 20
layout_width = getattr(frame.layout, 'width', 60)
layout_height = getattr(frame.layout, 'height', 20)

scale_x = canvas_width / layout_width if layout_width > canvas_width else 1.0
scale_y = canvas_height / layout_height if layout_height > canvas_height else 1.0

print(f"Scale: {scale_x}, {scale_y}")
print(f"Layout size: {layout_width}x{layout_height}")
print(f"Canvas size: {canvas_width}x{canvas_height}")

# Calculate scaled rect
raw_x = int(round(button.x * scale_x))
raw_y = int(round(button.y * scale_y))
raw_w = max(2, int(round(button.width * scale_x)))
raw_h = max(2, int(round(button.height * scale_y)))

print(f"Raw scaled: ({raw_x},{raw_y}) {raw_w}x{raw_h}")

# Check if clipped
if raw_x >= canvas_width or raw_y >= canvas_height:
    print("Button clipped - outside canvas")
elif raw_w <= 0 or raw_h <= 0:
    print("Button has zero size")
else:
    scaled_w = min(raw_w, canvas_width - raw_x)
    scaled_h = min(raw_h, canvas_height - raw_y)
    print(f"Final rect: ({raw_x},{raw_y}) {scaled_w}x{scaled_h}")
