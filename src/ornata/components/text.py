"""Text component definitions."""

from __future__ import annotations

from typing import Any

from ornata.definitions.dataclasses.components import (
    Component,
    ComponentAccessibility,
    ComponentContent,
    ComponentPlacement,
    ComponentRenderHints,
)
from ornata.definitions.enums import ComponentKind


class TextComponent(Component):
    """Read-only text container supporting titles and body copy."""

    def __init__(
        self,
        *,
        title: str | None = None,
        subtitle: str | None = None,
        text: str | None = None,
        body: str | None = None,
        order: int | None = None,
        label: str | None = None,
        priority: int | None = None,
        cacheable: bool | None = None,
        kind: ComponentKind = ComponentKind.TEXT,
        content: ComponentContent | None = None,
        placement: ComponentPlacement | None = None,
        accessibility: ComponentAccessibility | None = None,
        render_hints: ComponentRenderHints | None = None,
        **kwargs: Any,
    ) -> None:
        """Create a text component with ergonomic arguments.

        Parameters
        ----------
        title : str | None
            Title channel.
        subtitle : str | None
            Subtitle channel.
        text : str | None
            Primary text content.
        body : str | None
            Body text content.
        order : int | None
            Layout order in parent.
        label : str | None
            Accessibility label.
        priority : int | None
            Render priority hint.
        cacheable : bool | None
            Whether renderer may cache this node.
        kind : ComponentKind
            Component kind override.
        content : ComponentContent | None
            Pre-built content payload.
        placement : ComponentPlacement | None
            Pre-built placement payload.
        accessibility : ComponentAccessibility | None
            Pre-built accessibility payload.
        render_hints : ComponentRenderHints | None
            Pre-built render hints.
        **kwargs : Any
            Additional component arguments forwarded to the base component.
        """

        content_payload = content or ComponentContent(
            title=title,
            subtitle=subtitle,
            text=text,
            body=body,
        )
        placement_payload = placement or ComponentPlacement(order=order)
        accessibility_payload = accessibility or ComponentAccessibility(label=label)
        render_hints_payload = render_hints or ComponentRenderHints(
            priority=priority,
            cacheable=False if cacheable is None else cacheable,
        )

        super().__init__(
            kind=kind,
            focusable=False,
            content=content_payload,
            placement=placement_payload,
            accessibility=accessibility_payload,
            render_hints=render_hints_payload,
            **kwargs,
        )


__all__ = ["TextComponent"]
