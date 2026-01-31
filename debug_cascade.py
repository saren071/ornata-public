"""Debug cascade application."""
import sys
sys.path.insert(0, "src")

from ornata.styling.language.cascade import _property_handlers, resolve_stylesheet
from ornata.styling.language.engine import StyleEngine

# Load stylesheet
engine = StyleEngine()
engine.load_stylesheet("examples/styles/base.osts")

# Get the sheet
sheet = engine._sheets[0]
print("=== Checking handlers ===")
print(f"flex-direction handler: {_property_handlers.get('flex-direction')}")
print(f"display handler: {_property_handlers.get('display')}")

print("\n=== Resolving mission-control-root ===")
resolved = resolve_stylesheet(
    sheet=sheet,
    component="mission-control-root",
    states=frozenset(),
    colors={},
    fonts={},
)

print(f"flex_direction: {resolved.flex_direction}")
print(f"display: {resolved.display}")

# Check raw properties
for rule in sheet.rules:
    if rule.component == "mission-control-root":
        print(f"\n=== Raw properties for {rule.component} ===")
        for block in rule.blocks:
            print(f"  Block states: {block.states}")
            print(f"  Block raw_props: {block.raw_props}")
            for prop in block.properties:
                print(f"    Property: {prop.name} = {prop.value}")
