"""Layout container components."""

from __future__ import annotations

from typing import Any

from ornata.definitions.dataclasses.components import Component
from ornata.definitions.enums import ComponentKind


class ContainerComponent(Component):
    """Layout container that may host other components."""

    def __init__(
        self,
        *,
        kind: ComponentKind = ComponentKind.CONTAINER,
        **kwargs: Any,
    ) -> None:
        """Create a container component.

        Args:
            kind (ComponentKind): Component kind override.
            **kwargs (Any): Additional component arguments.

        Returns:
            None
        """

        super().__init__(kind=kind, **kwargs)


__all__ = ["ContainerComponent"]
