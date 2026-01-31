"""Example application using the public Ornata core API."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from ornata.definitions.dataclasses.events import ComponentEvent


class MissionControlUI:
    """Developer-authored application logic using Ornata components."""

    def __init__(self, *, mission_name: str = "Mission Control") -> None:
        self.mission_name = mission_name

    def build(self) -> ContainerComponent:
        """Create the component tree representing the UI."""

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
        command_input.register_event_handler(InteractionType.SUBMIT, self._on_command_submit)

        launch_button = ButtonComponent(
            component_name="launch-button",
            text="Initiate Launch Sequence",
            priority=1,
            cacheable=False,
            interactions_types=frozenset({InteractionType.CLICK, InteractionType.ACTIVATE}),
            cursor="pointer",
            order=3,
        )
        launch_button.register_event_handler(InteractionType.CLICK, self._log_launch)

        action_bar = ContainerComponent(
            component_name="action-bar",
            children=[command_input, launch_button],
            order=4,
        )

        return ContainerComponent(
            component_name="mission-control-root",
            children=[header, telemetry_table, action_bar],
        )

    @staticmethod
    def _log_launch(event: ComponentEvent) -> None:
        print(f"[developer] Launch event fired from {event.component_id}")

    @staticmethod
    def _on_command_submit(event: ComponentEvent) -> None:
        print(f"[developer] Command submitted: {event}")


def main() -> None:
    """Developer entry point using the Ornata Application API."""

    config = AppConfig(
        title="Aquila Operations",
        backend=BackendTarget.CLI,
        stylesheets=[
            "examples/styles/base.osts",  # Example stylesheet shipped alongside the app
        ],
    )
    print("[demo] Resolved Backend:", config.backend)
    print("[demo] Initial viewport (will update dynamically):", config.viewport_width, "x", config.viewport_height)
    app = Application(config)
    ui = MissionControlUI(mission_name="Aquila Operations")
    app.mount(ui.build)
    try:
        app.run_loop(fps=30.0)
    except KeyboardInterrupt:
        print("\n[demo] Application interrupted; shutting down...")
    finally:
        app.stop()

if __name__ == "__main__":
    main()
