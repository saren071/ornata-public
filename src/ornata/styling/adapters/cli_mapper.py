from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ornata.definitions.dataclasses.styling import ResolvedStyle


class CLIMapper:
    """Maps ResolvedStyle to CLI/terminal-compatible format with ANSI codes."""

    def __init__(self, resolved: ResolvedStyle):
        """Initialize mapper with resolved style.

        Args:
            resolved: The resolved style to map.
        """
        self.resolved = resolved

    def map(self) -> dict[str, Any]:
        """Map normalized style for basic stdout-only rendering.

        Converts color specifications to ANSI escape sequences.

        Returns:
            Dictionary with ANSI-formatted style properties.
        """
        from ornata.styling.colorkit.resolver import ColorResolver

        data: dict[str, Any] = {}
        resolver = ColorResolver()

        if self.resolved.color:
            data["fg"] = resolver.resolve_ansi(self.resolved.color)
        if self.resolved.background:
            data["bg"] = resolver.resolve_background(str(self.resolved.background))
        if self.resolved.border_color:
            data["border_fg"] = resolver.resolve_ansi(self.resolved.border_color)
        if self.resolved.outline:
            data["outline_fg"] = resolver.resolve_ansi(self.resolved.outline)
        if self.resolved.text_decoration_color:
            data["decoration_fg"] = resolver.resolve_ansi(self.resolved.text_decoration_color)

        return data
