"""Test script to verify ANSI color parsing."""
from ornata.rendering.backends.cli.rasterizer import RasterContext
from ornata.definitions.dataclasses.styling import ANSIColor

ctx = RasterContext()

# Test parsing truecolor ANSI
result = ctx._parse_ansi_color('\x1b[38;2;129;7;7m')
print(f"Parsed truecolor: {result}")

# Test parsing 256 color
result2 = ctx._parse_ansi_color('\x1b[38;5;196m')
print(f"Parsed 256 color: {result2}")

# Test parsing 16 color
result3 = ctx._parse_ansi_color('\x1b[31m')
print(f"Parsed 16 color: {result3}")
