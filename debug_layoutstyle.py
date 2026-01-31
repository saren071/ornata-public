"""Debug LayoutStyle conversion."""
import sys
sys.path.insert(0, "src")

from datetime import datetime
from ornata.application import AppConfig, Application, BackendTarget, ButtonComponent, ContainerComponent, TextComponent
from ornata.layout.adapters.osts_converter import osts_to_layout_style

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

# Check resolved style and layout style for mission-control-root
from ornata.styling.runtime import get_styling_runtime
runtime = get_styling_runtime()

context = type('Context', (), {
    'component_name': "mission-control-root",
    'state': {},
    'theme_overrides': None,
    'caps': None,
    'backend': BackendTarget.CLI,
    'active_states': lambda self: frozenset(),
})()

resolved = runtime.resolve_style(context)
print("=== ResolvedStyle ===")
for attr in ['flex_direction', 'display', 'width', 'height', 'direction']:
    val = getattr(resolved, attr, None)
    print(f"  {attr}: {val}")

print("\n=== LayoutStyle ===")
layout = osts_to_layout_style(resolved, BackendTarget.CLI)
for attr in ['flex_direction', 'display', 'width', 'height', 'direction']:
    val = getattr(layout, attr, None)
    print(f"  {attr}: {val}")
