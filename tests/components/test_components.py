"""Coverage tests for the components subsystem."""

from __future__ import annotations

from ornata.api.exports.components import (
    ButtonComponent,
    ContainerComponent,
    InputComponent,
    TableComponent,
    TextComponent,
    _load_layout_style_class,
)
from ornata.api.exports.definitions import (
    ComponentKind,
    InteractionDescriptor,
    InteractionType,
    LayoutStyle,
)


def test_load_layout_style_class_and_component_layout_style() -> None:
    """``_load_layout_style_class`` must resolve ``LayoutStyle`` and power layout snapshots."""

    layout_cls = _load_layout_style_class()
    assert layout_cls is LayoutStyle

    component = TextComponent(component_name="StatusText")
    component.visible = False
    component.placement.x = 10
    component.placement.y = 5
    component.placement.z_index = 1

    style = component.get_layout_style()
    assert isinstance(style, LayoutStyle)
    assert style.display == "none"
    assert style.position == "absolute"


def test_button_component_defaults_and_custom_interactions() -> None:
    """Button components should expose click/press interactions and allow overrides."""

    button = ButtonComponent(component_name="PrimaryButton")
    assert button.kind is ComponentKind.BUTTON
    assert button.focusable is True
    assert button.interactions.cursor == "pointer"
    assert button.interactions.types == frozenset({InteractionType.CLICK, InteractionType.PRESS})

    custom_descriptor = InteractionDescriptor(
        types=frozenset({InteractionType.PRESS}),
        cursor="hand",
        is_toggle=True,
    )
    overridden = ButtonComponent(
        component_name="SecondaryButton",
        interactions=custom_descriptor,
        focusable=False,
    )
    assert overridden.interactions is custom_descriptor
    assert overridden.focusable is False


def test_container_component_accepts_children() -> None:
    """Container components should keep appended children in order."""

    container = ContainerComponent(component_name="Shell")
    child = TextComponent(component_name="Child")
    container.add_child(child)

    assert container.kind is ComponentKind.CONTAINER
    assert container.iter_children() == (child,)


def test_input_component_default_and_override_interactions() -> None:
    """Input components expose change/focus interactions but respect overrides."""

    component = InputComponent(component_name="Field")
    assert component.kind is ComponentKind.INPUT
    assert component.focusable is True
    assert component.interactions.cursor == "text"
    assert component.interactions.types == frozenset(
        {InteractionType.CHANGE, InteractionType.FOCUS, InteractionType.BLUR}
    )

    custom_descriptor = InteractionDescriptor(
        types=frozenset({InteractionType.CHANGE}),
        cursor="ibeam",
        is_toggle=False,
    )
    overridden = InputComponent(component_name="CustomField", interactions=custom_descriptor)
    assert overridden.interactions is custom_descriptor


def test_table_component_selection_mode_defaults() -> None:
    """Table components default to single selection but accept overrides."""

    table = TableComponent(component_name="Grid")
    assert table.kind is ComponentKind.TABLE
    assert table.selection_mode == "single"
    assert table.focusable is True

    multi_select = TableComponent(component_name="MultiGrid", selection_mode="multiple")
    assert multi_select.selection_mode == "multiple"


def test_text_component_is_never_focusable() -> None:
    """Text components remain non-focusable even when metadata changes."""

    text = TextComponent(component_name="Label")
    text.meta["hint"] = "read-only"

    assert text.kind is ComponentKind.TEXT
    assert text.focusable is False
