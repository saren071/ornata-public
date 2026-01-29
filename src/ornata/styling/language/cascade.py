"""Cascade resolution for the Ornata Styling language."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from ornata.api.exports.definitions import ComponentRule, ResolvedStyle, StateBlock, Stylesheet
    

def resolve_stylesheet(
    sheet: Stylesheet,
    component: str,
    states: frozenset[str],
    colors: Mapping[str, str],
    fonts: Mapping[str, Any],
) -> ResolvedStyle:
    """Resolve ``component`` for ``states`` using ``sheet``."""
    from ornata.api.exports.definitions import ResolvedStyle

    resolved = ResolvedStyle()
    resolved.keyframes = dict(sheet.keyframes)
    custom_properties: dict[str, str] = {}
    extras: dict[str, Any] = {}

    applicable_rules = [rule for rule in sheet.rules if _matches_component(rule, component)]
    if not applicable_rules:
        return resolved

    # Sort rules by specificity (universal rules first, then component-specific)
    # This ensures proper cascade order without redundant processing
    applicable_rules.sort(key=lambda r: 0 if r.component == "*" else 1)

    # Early termination: if we have a universal rule and no component-specific rules,
    # we can skip further processing for this component
    has_universal = any(r.component == "*" for r in applicable_rules)
    has_specific = any(r.component != "*" for r in applicable_rules)
    if has_universal and not has_specific:
        # Only process universal rules for this component
        applicable_rules = [r for r in applicable_rules if r.component == "*"]

    # Pre-resolve color lookups for faster access
    color_cache = dict(colors)

    for rule in applicable_rules:
        for block in rule.blocks:
            if not block.matches(states):
                continue
            _apply_block(resolved, block, color_cache, fonts, custom_properties, extras)

    resolved.custom_properties = custom_properties or None
    resolved.component_extras = extras or None
    return resolved


def _matches_component(rule: ComponentRule, component: str) -> bool:
    """Return ``True`` when ``rule`` applies to ``component``."""

    selector = rule.component.strip()
    if selector == "*":
        return True
    return selector.lower() == component.lower()


def _apply_block(
    resolved: ResolvedStyle,
    block: StateBlock,
    colors: Mapping[str, str],
    fonts: Mapping[str, Any],
    custom_properties: dict[str, str],
    extras: dict[str, Any],
) -> None:
    """Apply a state block to ``resolved``."""

    raw_props = block.raw_props or [(prop.name, str(prop.value)) for prop in block.properties]
    # Use global property handlers lookup
    handlers = _property_handlers
    for name, value in raw_props:
        if name.startswith("--"):
            custom_properties[name] = value
            continue
        handler = handlers.get(name.lower())
        if handler:
            handler(resolved, value, colors, fonts)
            continue
        extras.setdefault(name, []).append(value)


def _split_tokens(value: str) -> list[str]:
    """Split a property value into tokens while respecting parentheses."""

    tokens: list[str] = []
    buff: list[str] = []
    depth = 0
    quote: str | None = None
    for ch in value.strip():
        if quote:
            buff.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in {'"', "'"}:
            buff.append(ch)
            quote = ch
            continue
        if ch == '(':
            depth += 1
            buff.append(ch)
            continue
        if ch == ')':
            depth = max(0, depth - 1)
            buff.append(ch)
            continue
        if ch.isspace() and depth == 0:
            if buff:
                tokens.append("".join(buff))
                buff = []
            continue
        buff.append(ch)
    if buff:
        tokens.append("".join(buff))
    return tokens


def _resolve_color(value: str, colors: Mapping[str, str]) -> str:
    """Resolve a colour token using ``colors`` as lookup table."""

    stripped = value.strip()
    if stripped.startswith("var(") and stripped.endswith(")"):
        inner = stripped[4:-1].strip()
        return colors.get(inner, stripped)
    if stripped.startswith("#") or stripped.startswith("rgb") or stripped.startswith("hsl"):
        return stripped
    # Fast path for common color names using direct dict access
    return colors.get(stripped, stripped)


def _handle_color(resolved: ResolvedStyle, value: str, colors: Mapping[str, str], _: Mapping[str, Any]) -> None:
    """Handle the ``color`` property."""

    resolved.color = _resolve_color(value, colors)


def _handle_background(resolved: ResolvedStyle, value: str, colors: Mapping[str, str], _: Mapping[str, Any]) -> None:
    """Handle the ``background`` property."""

    resolved.background = _resolve_color(value, colors)


def _handle_outline(resolved: ResolvedStyle, value: str, colors: Mapping[str, str], _: Mapping[str, Any]) -> None:
    """Handle the ``outline`` property."""

    resolved.outline = _resolve_color(value, colors)


def _handle_border_color(resolved: ResolvedStyle, value: str, colors: Mapping[str, str], _: Mapping[str, Any]) -> None:
    """Handle the ``border-color`` property."""

    resolved.border_color = _resolve_color(value, colors)


def _handle_padding(resolved: ResolvedStyle, value: str, _: Mapping[str, str], __: Mapping[str, Any]) -> None:
    """Handle the ``padding`` shorthand."""
    from ornata.api.exports.definitions import Insets

    tokens = _split_tokens(value)
    resolved.padding = Insets.from_tokens(tokens if tokens else [value])


def _handle_margin(resolved: ResolvedStyle, value: str, _: Mapping[str, str], __: Mapping[str, Any]) -> None:
    """Handle the ``margin`` shorthand."""
    from ornata.api.exports.definitions import Insets

    tokens = _split_tokens(value)
    resolved.margin = Insets.from_tokens(tokens if tokens else [value])


def _handle_font(resolved: ResolvedStyle, value: str, _: Mapping[str, str], fonts: Mapping[str, Any]) -> None:
    """Handle the ``font`` property referencing theme fonts."""
    from ornata.api.exports.definitions import Length

    token = value.strip()
    resolved.font = token
    if token in fonts:
        font = fonts[token]
        if font.size is not None:
            resolved.font_size = Length(font.size, "px")
        if font.weight is not None:
            resolved.weight = font.weight


def _handle_font_weight(resolved: ResolvedStyle, value: str, _: Mapping[str, str], __: Mapping[str, Any]) -> None:
    """Handle ``font-weight`` overrides."""

    resolved.weight = value.strip()


def _handle_font_size(resolved: ResolvedStyle, value: str, _: Mapping[str, str], __: Mapping[str, Any]) -> None:
    """Handle ``font-size`` overrides."""
    from ornata.api.exports.definitions import Length

    resolved.font_size = Length.from_token(value.strip())


def _handle_border(resolved: ResolvedStyle, value: str, colors: Mapping[str, str], __: Mapping[str, Any]) -> None:
    """Handle the ``border`` shorthand."""
    from ornata.api.exports.definitions import Border

    tokens = _split_tokens(value)
    width = float(tokens[0].rstrip("px")) if tokens else 0.0
    style = tokens[1] if len(tokens) > 1 else "solid"
    color = _resolve_color(tokens[2], colors) if len(tokens) > 2 else None
    resolved.border = Border(width, style, color)


def _handle_border_radius(resolved: ResolvedStyle, value: str, _: Mapping[str, str], __: Mapping[str, Any]) -> None:
    """Handle the ``border-radius`` shorthand."""
    from ornata.api.exports.definitions import BorderRadius, Insets

    tokens = _split_tokens(value)
    insets = Insets.from_tokens(tokens if tokens else [value])
    resolved.border_radius = BorderRadius(
        top_left=insets.top,
        top_right=insets.right,
        bottom_right=insets.bottom,
        bottom_left=insets.left,
    )


def _handle_box_shadow(resolved: ResolvedStyle, value: str, colors: Mapping[str, str], __: Mapping[str, Any]) -> None:
    """Handle ``box-shadow`` declarations."""
    from ornata.api.exports.definitions import BoxShadow, Length

    tokens = _split_tokens(value)
    inset = False
    if tokens and tokens[-1].lower() == "inset":
        inset = True
        tokens = tokens[:-1]
    if len(tokens) < 4:
        return
    offset_x = Length.from_token(tokens[0])
    offset_y = Length.from_token(tokens[1])
    blur = Length.from_token(tokens[2])
    color_index = 3
    try:
        spread = Length.from_token(tokens[3])
        color_index = 4
    except ValueError:
        spread = Length(0.0, "px")
    color = _resolve_color(tokens[color_index], colors) if len(tokens) > color_index else "#000000"
    shadow = BoxShadow(offset_x, offset_y, blur, spread, color, inset)
    if resolved.box_shadow is None:
        resolved.box_shadow = [shadow]
    else:
        resolved.box_shadow.append(shadow)


def _handle_line_height(resolved: ResolvedStyle, value: str, _: Mapping[str, str], __: Mapping[str, Any]) -> None:
    """Handle numeric and relative ``line-height`` values."""
    from ornata.api.exports.definitions import Length

    stripped = value.strip()
    try:
        resolved.line_height = float(stripped)
    except ValueError:
        resolved.line_height = Length.from_token(stripped)


def _handle_letter_spacing(resolved: ResolvedStyle, value: str, _: Mapping[str, str], __: Mapping[str, Any]) -> None:
    """Handle ``letter-spacing`` declarations."""
    from ornata.api.exports.definitions import Length

    resolved.letter_spacing = Length.from_token(value.strip())


def _handle_word_spacing(resolved: ResolvedStyle, value: str, _: Mapping[str, str], __: Mapping[str, Any]) -> None:
    """Handle ``word-spacing`` declarations."""
    from ornata.api.exports.definitions import Length

    resolved.word_spacing = Length.from_token(value.strip())


def _handle_text_align(resolved: ResolvedStyle, value: str, _: Mapping[str, str], __: Mapping[str, Any]) -> None:
    """Handle ``text-align`` declarations."""

    resolved.text_align = value.strip()


def _handle_text_transform(resolved: ResolvedStyle, value: str, _: Mapping[str, str], __: Mapping[str, Any]) -> None:
    """Handle ``text-transform`` declarations."""

    resolved.text_transform = value.strip()


def _handle_transform(resolved: ResolvedStyle, value: str, _: Mapping[str, str], __: Mapping[str, Any]) -> None:
    """Handle generic ``transform`` declarations."""

    resolved.transform = value.strip()


def _handle_text_decoration(resolved: ResolvedStyle, value: str, colors: Mapping[str, str], __: Mapping[str, Any]) -> None:
    """Handle the ``text-decoration`` shorthand."""

    tokens = _split_tokens(value)
    if tokens:
        resolved.text_decoration = tokens[0]
    if len(tokens) > 1:
        resolved.text_decoration_style = tokens[1]
    if len(tokens) > 2:
        resolved.text_decoration_color = _resolve_color(tokens[2], colors)


def _handle_opacity(resolved: ResolvedStyle, value: str, _: Mapping[str, str], __: Mapping[str, Any]) -> None:
    """Handle ``opacity`` declarations."""

    resolved.opacity = float(value)


def _handle_height(resolved: ResolvedStyle, value: str, _: Mapping[str, str], __: Mapping[str, Any]) -> None:
    """Handle ``height`` declarations."""
    from ornata.api.exports.definitions import Length

    resolved.height = Length.from_token(value.strip())


def _handle_width(resolved: ResolvedStyle, value: str, _: Mapping[str, str], __: Mapping[str, Any]) -> None:
    """Handle ``width`` declarations."""
    from ornata.api.exports.definitions import Length

    resolved.width = Length.from_token(value.strip())


def _handle_background_image(resolved: ResolvedStyle, value: str, _: Mapping[str, str], __: Mapping[str, Any]) -> None:
    """Handle ``background-image`` declarations."""

    resolved.background_image = value.strip()


def _handle_background_repeat(resolved: ResolvedStyle, value: str, _: Mapping[str, str], __: Mapping[str, Any]) -> None:
    """Handle ``background-repeat`` declarations."""

    resolved.background_repeat = value.strip()


def _handle_background_size(resolved: ResolvedStyle, value: str, _: Mapping[str, str], __: Mapping[str, Any]) -> None:
    """Handle ``background-size`` declarations."""

    resolved.background_size = value.strip()


def _handle_background_position(resolved: ResolvedStyle, value: str, _: Mapping[str, str], __: Mapping[str, Any]) -> None:
    """Handle ``background-position`` declarations."""

    resolved.background_position = value.strip()


def _handle_component_extra(resolved: ResolvedStyle, value: str, _: Mapping[str, str], __: Mapping[str, Any]) -> None:
    """Store unknown properties for downstream consumers."""

    extras = resolved.component_extras or {}
    extras.setdefault("extras", []).append(value)
    resolved.component_extras = extras


def _layout_setter(attr: str) -> Callable[[ResolvedStyle, str, Mapping[str, str], Mapping[str, Any]], None]:
    def setter(resolved: ResolvedStyle, value: str, _: Mapping[str, str], __: Mapping[str, Any]) -> None:
        setattr(resolved, attr, value.strip())
    return setter


_property_handlers: dict[str, Any] = {
    "color": _handle_color,
    "background": _handle_background,
    "outline": _handle_outline,
    "border-color": _handle_border_color,
    "padding": _handle_padding,
    "margin": _handle_margin,
    "font": _handle_font,
    "font-weight": _handle_font_weight,
    "font-size": _handle_font_size,
    "border": _handle_border,
    "border-radius": _handle_border_radius,
    "box-shadow": _handle_box_shadow,
    "line-height": _handle_line_height,
    "letter-spacing": _handle_letter_spacing,
    "word-spacing": _handle_word_spacing,
    "text-align": _handle_text_align,
    "text-transform": _handle_text_transform,
    "transform": _handle_transform,
    "text-decoration": _handle_text_decoration,
    "opacity": _handle_opacity,
    "height": _handle_height,
    "width": _handle_width,
    "background-image": _handle_background_image,
    "background-repeat": _handle_background_repeat,
    "background-size": _handle_background_size,
    "background-position": _handle_background_position,
    "component-extra": _handle_component_extra,
    # Layout properties for performance
    "display": _layout_setter("display"),
    "position": _layout_setter("position"),
    "flex-direction": _layout_setter("flex_direction"),
    "flex-wrap": _layout_setter("flex_wrap"),
    "wrap": _layout_setter("flex_wrap"),
    "justify-content": _layout_setter("justify_content"),
    "align-items": _layout_setter("align_items"),
}

__all__ = ["resolve_stylesheet"]
