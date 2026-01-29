"""Advanced typography utilities for text rendering."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ornata.api.exports.definitions import TextShadow


class TypographyEngine:
    """Advanced typography processing engine."""
    from ornata.api.exports.definitions import TextAlign, TextDecorationStyle, TextTransform

    @staticmethod
    def apply_text_transform(text: str, transform: TextTransform) -> str:
        """Apply text transformation to text."""
        if transform == "uppercase":
            return text.upper()
        elif transform == "lowercase":
            return text.lower()
        elif transform == "capitalize":
            return text.title()
        else:
            return text

    @staticmethod
    def apply_text_decoration(text: str, decoration: str, color: str | None = None, style: TextDecorationStyle = "solid") -> str:
        """Apply text decoration to text."""
        if not decoration or decoration == "none":
            return text

        # For terminal rendering, we can use ANSI codes to simulate decorations
        if decoration == "underline":
            return f"\033[4m{text}\033[24m"
        elif decoration == "overline":
            # ANSI doesn't have overline, fallback to underline
            return f"\033[4m{text}\033[24m"
        elif decoration == "line-through":
            return f"\033[9m{text}\033[29m"
        else:
            return text

    @staticmethod
    def apply_text_shadow(text: str, shadow: TextShadow) -> str:
        """Apply text shadow effect (simplified for terminal)."""
        # For terminal, shadows are difficult to implement
        # This would require advanced rendering with background colors
        # For now, just return the text
        return text

    @staticmethod
    def apply_letter_spacing(text: str, spacing_px: float) -> str:
        """Apply letter spacing by inserting spaces."""
        if spacing_px <= 0:
            return text

        # Convert px to character spacing (rough approximation)
        spaces_per_char = max(0, int(spacing_px / 2))
        if spaces_per_char == 0:
            return text

        result = ""
        for char in text:
            result += char + " " * spaces_per_char
        return result.rstrip()

    @staticmethod
    def apply_word_spacing(text: str, spacing_px: float) -> str:
        """Apply word spacing by inserting spaces between words."""
        if spacing_px <= 0:
            return text

        # Convert px to spaces
        extra_spaces = max(0, int(spacing_px / 4))
        if extra_spaces == 0:
            return text

        return re.sub(r"\s+", " " * (1 + extra_spaces), text)

    @staticmethod
    def calculate_line_height(base_height: int, line_height: float | int) -> int:
        """Calculate line height in pixels."""
        if isinstance(line_height, int):
            return line_height
        else:
            return int(base_height * line_height)

    @staticmethod
    def wrap_text_with_alignment(text: str, width: int, align: TextAlign = "left") -> list[str]:
        """Wrap text and apply alignment."""
        # Simple word wrapping
        words = text.split()
        lines: list[str] = []
        current_line = ""
        current_length = 0

        for word in words:
            word_length = len(word)
            if current_length + word_length + 1 <= width:
                if current_line:
                    current_line += " " + word
                    current_length += word_length + 1
                else:
                    current_line = word
                    current_length = word_length
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
                current_length = word_length

        if current_line:
            lines.append(current_line)

        # Apply alignment
        aligned_lines: list[str] = []
        for line in lines:
            if align == "left":
                aligned_lines.append(line.ljust(width))
            elif align == "right":
                aligned_lines.append(line.rjust(width))
            elif align == "center":
                aligned_lines.append(line.center(width))
            else:  # justify
                aligned_lines.append(line.ljust(width))

        return aligned_lines


__all__ = ["TypographyEngine"]
