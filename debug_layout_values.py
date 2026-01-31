"""Debug layout values to verify cell conversion."""
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

print("=== Resolved Styles ===")
from ornata.styling.runtime import get_styling_runtime
runtime = get_styling_runtime()

for comp_name in ["mission-control-root", "mission-header", "action-bar", "command-entry", "launch-button"]:
    context = type('Context', (), {
        'component_name': comp_name,
        'state': {},
        'theme_overrides': None,
        'caps': None,
        'backend': BackendTarget.CLI,
        'active_states': lambda self: frozenset(),
    })()
    resolved = runtime.resolve_backend_style(context)
    style = resolved.style if resolved else None
    if style:
        w = getattr(style.width, 'value', style.width) if style.width else None
        h = getattr(style.height, 'value', style.height) if style.height else None
        w_unit = getattr(style.width, 'unit', 'none') if hasattr(style.width, 'unit') else 'raw'
        h_unit = getattr(style.height, 'unit', 'none') if hasattr(style.height, 'unit') else 'raw'
        print(f"{comp_name}: width={w} ({w_unit}), height={h} ({h_unit})")
    else:
        print(f"{comp_name}: no style")

print("\n=== Layout Tree Positions ===")
def debug_layout(node, depth=0):
    layout = getattr(node, 'layout', None)
    if layout:
        print(f"{'  '*depth}{node.component_name}: ({layout.x},{layout.y}) {layout.width}x{layout.height}")
    else:
        print(f"{'  '*depth}{node.component_name}: no layout")
    for child in node.children:
        debug_layout(child, depth + 1)

root = app._runtime._layout_tree
debug_layout(root)
