"""Debug stylesheet loading in application context."""
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

# Check if stylesheet was loaded
engine = app._runtime._styling.get_engine()
print("=== StyleEngine Sheets ===")
print(f"Number of sheets: {len(engine._sheets)}")
for sheet in engine._sheets:
    print(f"Sheet: {getattr(sheet, 'source', 'unknown')}")
    for rule in getattr(sheet, 'rules', []):
        comp = getattr(rule, 'component', 'unknown')
        print(f"  Component: {comp}")
        # Try to access properties at rule level or block level
        if hasattr(rule, 'properties'):
            for prop in rule.properties:
                name = getattr(prop, 'name', 'unknown')
                val = getattr(prop, 'value', 'unknown')
                print(f"    {name}: {val}")
        if hasattr(rule, 'blocks'):
            for block in rule.blocks:
                if hasattr(block, 'properties'):
                    for prop in block.properties:
                        name = getattr(prop, 'name', 'unknown')
                        val = getattr(prop, 'value', 'unknown')
                        print(f"    [block] {name}: {val}")
