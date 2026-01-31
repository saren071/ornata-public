"""Debug stylesheet loading."""
import sys
sys.path.insert(0, "src")

from ornata.styling.runtime import get_styling_runtime
from ornata.definitions.enums import BackendTarget

runtime = get_styling_runtime()

# Check if stylesheet was loaded
print("=== Stylesheets ===")
print(f"Sheets count: {len(runtime._sheets)}")
for i, sheet in enumerate(runtime._sheets):
    print(f"Sheet {i}: {getattr(sheet, 'source', 'unknown')}")
    print(f"  Rules: {len(getattr(sheet, 'rules', []))}")
    for rule in getattr(sheet, 'rules', []):
        comp = getattr(rule, 'component', 'unknown')
        print(f"    Rule: {comp}")
