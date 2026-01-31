"""Debug terminal size detection."""
import sys
sys.path.insert(0, "src")

from ornata.api.exports.rendering import get_terminal_size

rows, cols = get_terminal_size()
print(f"Terminal size: {rows} rows x {cols} columns")

# Also check shutil directly
import shutil
size = shutil.get_terminal_size(fallback=(24, 80))
print(f"shutil reports: {size.lines} lines x {size.columns} columns")
