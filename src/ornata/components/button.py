"""Button component implementation."""

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


class ButtonComponent(Component):
    """Interactive button built on the base component."""

    def __init__(
        self,
        *,
        text: str | None = None,
        title: str | None = None,
        subtitle: str | None = None,
        order: int | None = None,
        label: str | None = None,
        priority: int | None = None,
        cacheable: bool | None = None,
        interactions_types: frozenset[InteractionType] | None = None,
        cursor: str = "pointer",
        kind: ComponentKind = ComponentKind.BUTTON,
        focusable: bool = True,
        content: ComponentContent | None = None,
        placement: ComponentPlacement | None = None,
        accessibility: ComponentAccessibility | None = None,
        render_hints: ComponentRenderHints | None = None,
        interactions: InteractionDescriptor | None = None,
        **kwargs: Any,
    ) -> None:
        """Create a button component with ergonomic arguments.

        Parameters
        ----------
        text : str | None
            Visible button label.
        title : str | None
            Optional title channel.
        subtitle : str | None
            Optional subtitle channel.
        order : int | None
            Layout order for the button within its parent.
        label : str | None
            Accessibility label.
        priority : int | None
            Render priority hint.
        cacheable : bool | None
            Whether renderer may cache this node.
        interactions_types : frozenset[InteractionType] | None
            Interaction types to register; defaults to click/press.
        cursor : str
            Cursor hint when hovering.
        kind : ComponentKind
            Component kind override.
        focusable : bool
            Whether the button can receive focus.
        content : ComponentContent | None
            Pre-built content payload.
        placement : ComponentPlacement | None
            Pre-built placement payload.
        accessibility : ComponentAccessibility | None
            Pre-built accessibility payload.
        render_hints : ComponentRenderHints | None
            Pre-built render hints.
        interactions : InteractionDescriptor | None
            Pre-built interactions payload.
        **kwargs : Any
            Additional component arguments forwarded to the base component.
        """

        content_payload = content or ComponentContent(text=text, title=title, subtitle=subtitle)
        placement_payload = placement or ComponentPlacement(order=order)
        accessibility_payload = accessibility or ComponentAccessibility(label=label)
        render_hints_payload = render_hints or ComponentRenderHints(
            priority=priority,
            cacheable=False if cacheable is None else cacheable,
        )

        interactions_payload = interactions or InteractionDescriptor(
            types=interactions_types or frozenset({InteractionType.CLICK, InteractionType.PRESS}),
            cursor=cursor,
            is_toggle=False,
        )

        super().__init__(
            kind=kind,
            focusable=focusable,
            content=content_payload,
            placement=placement_payload,
            accessibility=accessibility_payload,
            render_hints=render_hints_payload,
            interactions=interactions_payload,
            **kwargs,
        )


__all__ = ["ButtonComponent"]
