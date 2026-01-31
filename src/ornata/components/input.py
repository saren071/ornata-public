"""Input component implementations."""

from __future__ import annotations

from typing import Any

from ornata.definitions.dataclasses.components import (
    Component,
    ComponentAccessibility,
    ComponentContent,
    ComponentPlacement,
    ComponentRenderHints,
    InteractionDescriptor,
)
from ornata.definitions.enums import ComponentKind, InteractionType


class InputComponent(Component):
    """Collects user input such as text, toggles, and sliders."""

    def __init__(
        self,
        *,
        placeholder: str | None = None,
        text: str | None = None,
        order: int | None = None,
        label: str | None = None,
        priority: int | None = None,
        cacheable: bool | None = None,
        kind: ComponentKind = ComponentKind.INPUT,
        interactions_types: frozenset[InteractionType] | None = None,
        cursor: str = "text",
        content: ComponentContent | None = None,
        placement: ComponentPlacement | None = None,
        accessibility: ComponentAccessibility | None = None,
        render_hints: ComponentRenderHints | None = None,
        interactions: InteractionDescriptor | None = None,
        **kwargs: Any,
    ) -> None:
        """Create an input component with ergonomic arguments."""

        content_payload = content or ComponentContent(placeholder=placeholder, text=text)
        placement_payload = placement or ComponentPlacement(order=order)
        accessibility_payload = accessibility or ComponentAccessibility(label=label)
        render_hints_payload = render_hints or ComponentRenderHints(
            priority=priority,
            cacheable=False if cacheable is None else cacheable,
        )

        interactions_payload = interactions or InteractionDescriptor(
            types=interactions_types
            or frozenset({InteractionType.CHANGE, InteractionType.FOCUS, InteractionType.BLUR}),
            cursor=cursor,
            is_toggle=False,
        )

        super().__init__(
            kind=kind,
            focusable=True,
            content=content_payload,
            placement=placement_payload,
            accessibility=accessibility_payload,
            render_hints=render_hints_payload,
            interactions=interactions_payload,
            **kwargs,
        )


__all__ = ["InputComponent"]
