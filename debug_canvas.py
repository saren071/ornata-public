"""Debug UnicodeCanvas behavior with ANSI codes."""
import sys
sys.path.insert(0, "src")

from ornata.definitions.dataclasses.rendering import UnicodeCanvas

# Test 1: Write ANSI directly
print("=== Test 1: Direct ANSI write ===")
canvas = UnicodeCanvas(20, 5)
bg_seq = "\x1b[48;2;26;15;31m"
canvas._write(0, 0, f"{bg_seq}Hello")
result = canvas.render()
print(repr(result[:100]))

# Test 2: Check what's in the grid
print("\n=== Test 2: Grid contents ===")
canvas2 = UnicodeCanvas(10, 3)
canvas2._write(0, 0, "\x1b[48;2;255;0;0m")
print(f"Row 0: {repr(''.join(canvas2._grid[0]))}")
print(f"Repr:  {repr(canvas2._grid[0])}")

# Check each cell
print("\nCell by cell:")
for i, ch in enumerate(canvas2._grid[0][:10]):
    print(f"  [{i}]: {repr(ch)} (ord={ord(ch) if ch else 'empty'})")

# Test 3: Check if render preserves escapes
print("\n=== Test 3: Render output ===")
output = canvas2.render()
print(f"Has escape: {'\\x1b' in repr(output)}")
print(f"Output: {repr(output)}")
