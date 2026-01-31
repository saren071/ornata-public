"""Layout container components."""

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


class ContainerComponent(Component):
    """Layout container that may host other components."""

    def __init__(
        self,
        *,
        order: int | None = None,
        label: str | None = None,
        priority: int | None = None,
        cacheable: bool | None = None,
        kind: ComponentKind = ComponentKind.CONTAINER,
        content: ComponentContent | None = None,
        placement: ComponentPlacement | None = None,
        accessibility: ComponentAccessibility | None = None,
        render_hints: ComponentRenderHints | None = None,
        **kwargs: Any,
    ) -> None:
        """Create a container component with ergonomic arguments."""

        content_payload = content or ComponentContent()
        placement_payload = placement or ComponentPlacement(order=order)
        accessibility_payload = accessibility or ComponentAccessibility(label=label)
        render_hints_payload = render_hints or ComponentRenderHints(
            priority=priority,
            cacheable=False if cacheable is None else cacheable,
        )

        super().__init__(
            kind=kind,
            content=content_payload,
            placement=placement_payload,
            accessibility=accessibility_payload,
            render_hints=render_hints_payload,
            **kwargs,
        )


__all__ = ["ContainerComponent"]
