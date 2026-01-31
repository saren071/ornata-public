"""Test text color rendering."""
import sys
sys.path.insert(0, "src")

from datetime import datetime
from ornata.application import AppConfig, Application, BackendTarget, TextComponent, ContainerComponent

class TestUI:
    def build(self):
        header = TextComponent(
            component_name="mission-header",
            title="TEST TITLE",
            subtitle="subtitle here",
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
renderer = TerminalRenderer(BackendTarget.CLI)
result = renderer.render_tree(gui_tree, frame.layout)

output = result.content
print("=== OUTPUT ===")
print(output)
print("=== CHECKING FOR ANSI CODES ===")
print(f"Contains escape: {'\\x1b' in output}")
if '\x1b' in output:
    # Find lines with escape codes
    for i, line in enumerate(output.split('\n')):
        if '\x1b' in line:
            print(f"Line {i}: {repr(line)}")
else:
    print("No ANSI escape codes found - text colors not being applied")
