"""Debug resolved styles for flex-direction."""
import sys
sys.path.insert(0, "src")

from ornata.styling.runtime import get_styling_runtime
from ornata.definitions.enums import BackendTarget

runtime = get_styling_runtime()

# Check what styles are resolved for mission-control-root
payload = runtime.resolve_backend_style(
    type('Context', (), {
        'component_name': "mission-control-root",
        'state': {},
        'theme_overrides': None,
        'caps': None,
        'backend': BackendTarget.CLI,
        'active_states': lambda self: frozenset(),
    })()
)

print("=== mission-control-root resolved style ===")
style = payload.style if payload else None
if style:
    for attr in dir(style):
        if not attr.startswith('_'):
            val = getattr(style, attr)
            if val is not None and not callable(val):
                print(f"  {attr}: {repr(val)}")
else:
    print("No style resolved")
