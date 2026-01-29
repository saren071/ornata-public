"""Text component definitions."""

from __future__ import annotations

from typing import Any

from ornata.definitions.dataclasses.components import Component
from ornata.definitions.enums import ComponentKind


class TextComponent(Component):
    """Read-only text container supporting titles and body copy."""

    def __init__(
        self,
        *,
        kind: ComponentKind = ComponentKind.TEXT,
        **kwargs: Any,
    ) -> None:
        """Create a text component.

        Args:
            kind (ComponentKind): Component kind override.
            **kwargs (Any): Additional component arguments.

        Returns:
            None
        """

        super().__init__(kind=kind, focusable=False, **kwargs)


__all__ = ["TextComponent"]
