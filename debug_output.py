"""Debug script to see ANSI output from rendered frame."""

import sys
sys.path.insert(0, "src")

from datetime import datetime
from ornata.application import (
    AppConfig,
    Application,
    BackendTarget,
    ButtonComponent,
    ContainerComponent,
    InputComponent,
    InteractionType,
    TableComponent,
    TextComponent,
)

class MissionControlUI:
    def __init__(self, *, mission_name: str = "Mission Control") -> None:
        self.mission_name = mission_name

    def build(self) -> ContainerComponent:
        header = TextComponent(
            component_name="mission-header",
            title=self.mission_name,
            subtitle=datetime.now().strftime("%B %d, %Y - %H:%M"),
            order=0,
            label="Mission control header",
        )

        telemetry_table = TableComponent(
            component_name="telemetry-table",
            columns=["Subsystem", "State", "Last Update"],
            rows=[
                ["Nav", "Nominal", "00:03"],
                ["Power", "Charging", "00:15"],
                ["Thermal", "Stable", "00:01"],
            ],
            selection_mode="single",
            selection=[0],
            order=1,
        )

        command_input = InputComponent(
            component_name="command-entry",
            placeholder="Type command...",
            label="Command entry input",
            interactions_types=frozenset({InteractionType.CHANGE, InteractionType.SUBMIT}),
            cursor="text",
            order=2,
        )

        launch_button = ButtonComponent(
            component_name="launch-button",
            text="Initiate Launch Sequence",
            priority=1,
            cacheable=False,
            interactions_types=frozenset({InteractionType.CLICK, InteractionType.ACTIVATE}),
            cursor="pointer",
            order=3,
        )

        action_bar = ContainerComponent(
            component_name="action-bar",
            children=[command_input, launch_button],
            order=4,
        )

        return ContainerComponent(
            component_name="mission-control-root",
            children=[header, telemetry_table, action_bar],
        )

# Create app and render one frame
config = AppConfig(
    title="Aquila Operations",
    backend=BackendTarget.CLI,
    stylesheets=["examples/styles/base.osts"],
)
app = Application(config)
ui = MissionControlUI(mission_name="Aquila Operations")
app.mount(ui.build)

# Get the rendered output directly
frame = app._runtime.run(ui.build())
gui_tree = frame.gui_tree

# Render using the renderer directly
from ornata.rendering.backends.cli.terminal import TerminalRenderer
renderer = TerminalRenderer(BackendTarget.CLI)

# Get layout result
result = renderer.render_tree(gui_tree, frame.layout)

# Print the output with visible escape sequences
output = result.content if hasattr(result, 'content') else str(result)
print("=== RENDERED OUTPUT (first 20 lines) ===")
lines = output.split('\n')
for i, line in enumerate(lines[:20]):
    visible = line.replace('\x1b[0m', '[RESET]').replace('\x1b[48;2;', '[BG:').replace('\x1b[38;2;', '[FG:')
    # Show the raw bytes for lines with escape codes
    if '\x1b' in line:
        visible += f"  (raw: {repr(line[:80])})"
    print(f"{i:2}: {visible[:120]}")

print(f"\n=== Total lines: {len(lines)} ===")
