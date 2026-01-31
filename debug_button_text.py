"""Debug button text rendering."""
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

# Get the button node
root = frame.gui_tree
action_bar = root.children[1]
button = action_bar.children[1]

print(f"Button component_name: {button.component_name}")
print(f"Button text: {getattr(button, 'text', None)}")
print(f"Button content: {getattr(button, 'content', None)}")
if button.content:
    print(f"  content.text: {getattr(button.content, 'text', None)}")
    print(f"  content.title: {getattr(button.content, 'title', None)}")
    print(f"  content.body: {getattr(button.content, 'body', None)}")

# Check backend_style
metadata = getattr(button, 'metadata', {})
backend_style = metadata.get('backend_style')
if backend_style:
    style = getattr(backend_style, 'style', None)
    if style:
        print(f"Backend style color: {getattr(style, 'color', None)}")
        print(f"Backend style background: {getattr(style, 'background', None)}")
