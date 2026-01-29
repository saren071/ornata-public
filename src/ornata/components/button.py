"""Button component implementation."""

from __future__ import annotations

from typing import Any

from ornata.definitions.dataclasses.components import Component, InteractionDescriptor
from ornata.definitions.enums import ComponentKind, InteractionType


class ButtonComponent(Component):
    """Interactive button built on the base component."""

    def __init__(self, *, kind: ComponentKind = ComponentKind.BUTTON, focusable: bool = True, **kwargs: Any) -> None:
        """Create a button component.

        Args:
            kind (ComponentKind): Component kind override.
            focusable (bool): Whether the button participates in focus.
            **kwargs (Any): Additional component arguments.

        Returns:
            None
        """

        interactions = kwargs.pop(
            "interactions",
            InteractionDescriptor(
                types=frozenset({InteractionType.CLICK, InteractionType.PRESS}),
                cursor="pointer",
                is_toggle=False,
            ),
        )
        super().__init__(kind=kind, focusable=focusable, interactions=interactions, **kwargs)


__all__ = ["ButtonComponent"]
