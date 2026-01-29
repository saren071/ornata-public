"""Input component implementations."""

from __future__ import annotations

from typing import Any

from ornata.definitions.dataclasses.components import Component, InteractionDescriptor
from ornata.definitions.enums import ComponentKind, InteractionType


class InputComponent(Component):
    """Collects user input such as text, toggles, and sliders."""

    def __init__(
        self,
        *,
        kind: ComponentKind = ComponentKind.INPUT,
        interactions: InteractionDescriptor | None = None,
        **kwargs: Any,
    ) -> None:
        """Create an input component.

        Args:
            kind (ComponentKind): Component kind override.
            interactions (InteractionDescriptor | None): Interaction descriptor override.
            **kwargs (Any): Additional component arguments.

        Returns:
            None
        """

        interactions = interactions or InteractionDescriptor(
            types=frozenset({InteractionType.CHANGE, InteractionType.FOCUS, InteractionType.BLUR}),
            cursor="text",
            is_toggle=False,
        )
        super().__init__(kind=kind, focusable=True, interactions=interactions, **kwargs)


__all__ = ["InputComponent"]
