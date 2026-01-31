"""Debug stylesheet parsing."""
import sys
sys.path.insert(0, "src")

from ornata.styling.language.engine import StyleEngine

engine = StyleEngine()
engine.load_stylesheet("examples/styles/base.osts")

print("=== Stylesheet Rules ===")
for sheet in engine._sheets:
    for rule in sheet.rules:
        print(f"\nComponent: {rule.component}")
        for block in rule.blocks:
            print(f"  States: {block.states}")
            for prop in block.properties:
                print(f"    {prop.name}: {prop.value}")
