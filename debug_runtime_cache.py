"""Debug runtime cache issue."""
import sys
sys.path.insert(0, "src")

from ornata.styling.runtime import get_styling_runtime
from ornata.definitions.enums import BackendTarget

runtime = get_styling_runtime()

# Check cache before loading stylesheet
print("=== Before loading stylesheet ===")
print(f"Cache size: {len(runtime._cache)}")

# Load stylesheet
runtime.load_stylesheet("examples/styles/base.osts")

print("\n=== After loading stylesheet ===")
print(f"Cache size: {len(runtime._cache)}")

# Now resolve
from ornata.api.exports.definitions import StylingContext
context = StylingContext(
    component_name="mission-control-root",
    state={},
    theme_overrides=None,
    caps=None,
    backend=BackendTarget.CLI,
)

resolved = runtime.resolve_style(context)
print(f"\n=== Resolved via runtime ===")
print(f"flex_direction: {resolved.flex_direction}")
print(f"display: {resolved.display}")
