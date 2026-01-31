"""Debug Application's styling runtime."""
import sys
sys.path.insert(0, "src")

from datetime import datetime
from ornata.application import AppConfig, Application, BackendTarget, ButtonComponent, ContainerComponent, TextComponent

class TestUI:
    def build(self):
        header = TextComponent(
            component_name="mission-header",
            title="HEADER",
            order=0,
        )
        button = ButtonComponent(
            component_name="launch-button",
            text="LAUNCH",
            order=1,
        )
        return ContainerComponent(
            component_name="mission-control-root",
            children=[header, button],
        )

config = AppConfig(
    title="Test",
    backend=BackendTarget.CLI,
    stylesheets=["examples/styles/base.osts"],
)
app = Application(config)

# Check the app's styling runtime
styling = app._runtime._styling
engine = styling.get_engine()

print("=== App's StylingRuntime ===")
print(f"Number of sheets: {len(engine._sheets)}")
print(f"Stylesheets loaded: {app._runtime._stylesheets_loaded}")

# Try resolving through the app's runtime
from ornata.definitions.dataclasses.styling import StylingContext
from ornata.definitions.enums import BackendTarget

context = StylingContext(
    component_name="mission-control-root",
    state={},
    theme_overrides=None,
    caps=None,
    backend=BackendTarget.CLI,
)

payload = styling.resolve_backend_style(context)
print(f"\n=== Resolved via app's runtime ===")
print(f"flex_direction: {payload.style.flex_direction}")
print(f"display: {payload.style.display}")
