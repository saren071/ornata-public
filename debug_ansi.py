"""Debug - check actual ANSI output."""
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
renderer = TerminalRenderer(BackendTarget.CLI)
result = renderer.render_tree(gui_tree, frame.layout)

output = result.content
print("=== FIRST 200 BYTES OF OUTPUT ===")
print(repr(output[:200]))
print("\n=== AS PLAIN TEXT (should show colors in terminal) ===")
print(output[:500])
