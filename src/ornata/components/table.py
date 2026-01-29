"""Table/grid component implementations."""

from __future__ import annotations

from typing import Any

from ornata.definitions.dataclasses.components import Component
from ornata.definitions.enums import ComponentKind


class TableComponent(Component):
    """Structured grid component for presenting tabular data."""

    def __init__(
        self,
        *,
        kind: ComponentKind = ComponentKind.TABLE,
        selection_mode: str | None = "single",
        **kwargs: Any,
    ) -> None:
        """Create a table component.

        Args:
            kind (ComponentKind): Component kind override.
            selection_mode (str | None): Selection strategy.
            **kwargs (Any): Additional component arguments.

        Returns:
            None
        """

        super().__init__(kind=kind, selection_mode=selection_mode, focusable=True, **kwargs)


__all__ = ["TableComponent"]
