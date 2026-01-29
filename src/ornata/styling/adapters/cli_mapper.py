from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ornata.definitions.dataclasses.styling import ResolvedStyle

class CLIMapper:
    def __init__(self, resolved: ResolvedStyle):
        self.resolved = resolved

    def map(self) -> dict[str, Any]:
        """Map normalized style for basic stdout-only rendering."""
        data: dict[str, Any] = {}
        if self.resolved.color:
            data["fg"] = self.resolved.color
        if self.resolved.background:
            data["bg"] = self.resolved.background
        return data
