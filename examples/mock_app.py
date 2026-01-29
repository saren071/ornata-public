"""Example application using the public Ornata core API."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from ornata.api.exports.definitions import ComponentAccessibility, ComponentContent, ComponentPlacement, ComponentRenderHints, InteractionDescriptor, InteractionType
from ornata.application import AppConfig, Application, BackendTarget
from ornata.components import (
    ButtonComponent,
    ContainerComponent,
    InputComponent,
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
            content=ComponentContent(
                title=self.mission_name,
                subtitle=datetime.now().strftime("%B %d, %Y - %H:%M"),
            ),
            placement=ComponentPlacement(order=0),
            accessibility=ComponentAccessibility(label="Mission control header"),
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
            placement=ComponentPlacement(order=1),
        )

        command_input = InputComponent(
            component_name="command-entry",
            content=ComponentContent(placeholder="Type command..."),
            accessibility=ComponentAccessibility(label="Command entry input"),
            interactions=InteractionDescriptor(
                types=frozenset({InteractionType.CHANGE, InteractionType.SUBMIT}),
                cursor="text",
            ),
            placement=ComponentPlacement(order=2),
        )

        launch_button = ButtonComponent(
            component_name="launch-button",
            content=ComponentContent(text="Initiate Launch Sequence"),
            render_hints=ComponentRenderHints(priority=1, cacheable=False),
            interactions=InteractionDescriptor(
                types=frozenset({InteractionType.CLICK, InteractionType.ACTIVATE}),
                cursor="pointer",
            ),
            placement=ComponentPlacement(order=3),
        )
        launch_button.register_event_handler(InteractionType.CLICK, self._log_launch)

        action_bar = ContainerComponent(
            component_name="action-bar",
            children=[command_input, launch_button],
            placement=ComponentPlacement(order=4),
        )

        return ContainerComponent(
            component_name="mission-control-root",
            children=[header, telemetry_table, action_bar],
        )

    @staticmethod
    def _log_launch(event: ComponentEvent) -> None:
        print(f"[developer] Launch event fired from {event.component_id}")


def main() -> None:
    """Developer entry point using the Ornata Application API."""

    config = AppConfig(
        title="Aquila Operations",
        backend=BackendTarget.CLI,
        viewport_width=1280,
        viewport_height=720,
        stylesheets=[
            "examples/styles/base.osts",  # Example stylesheet shipped alongside the app
        ],
    )
    print("[demo] Resolved Backend:", config.backend)
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
