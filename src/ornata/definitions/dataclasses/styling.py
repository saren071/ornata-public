""" Styling Dataclasses for Ornata """

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

from ornata.definitions.enums import BackendTarget

if TYPE_CHECKING:
    from collections.abc import Mapping

    from ornata.definitions.dataclasses.components import ComponentRule
    from ornata.definitions.dataclasses.effects import Animation, Keyframes
    from ornata.definitions.dataclasses.layout import LayoutStyle
    from ornata.definitions.type_alias import ColorSpec, LengthUnit


PX_UNIT: Literal["px"] = "px"


@dataclass(slots=True, frozen=True)
class PaletteEntry:
    """Palette entry mapping a semantic token to a color literal.
    
    This represents a named color in the palette that can be resolved
    to different backend-specific formats (ANSI for CLI, RGB for GUI).
    """
    token: str
    literal: ColorLiteral
    cached_rgb: tuple[int, int, int] | None = None


@dataclass(slots=True, frozen=True)
class Span:
    """Location information for diagnostics."""
    filename: str
    line: int
    column: int


@dataclass(slots=True, frozen=True)
class ColorToken:
    """Named colour entry declared through ``@colors``."""
    name: str
    value: str
    span: Span


@dataclass(slots=True, frozen=True)
class FontDef:
    """Font profile declared through ``@fonts``."""
    name: str
    size: float | None
    weight: str | int | None
    family: str | None
    span: Span


@dataclass(slots=True, frozen=True)
class Property:
    """Single property assignment in a state block."""
    name: str
    value: Any
    span: Span


@dataclass(slots=True, frozen=True)
class Stylesheet:
    """Top level stylesheet container."""
    filename: str
    colors: dict[str, ColorToken]
    fonts: dict[str, FontDef]
    keyframes: dict[str, Keyframes]
    media_rules: list[MediaRule]
    rules: list[ComponentRule]


@dataclass(slots=True)
class ResolvedStyle:
    """Fully resolved style for a component."""
    color: ColorSpec | None = None
    background: ColorSpec | None = None
    border: Border | None = None
    border_color: ColorSpec | None = None
    border_radius: BorderRadius | None = None
    padding: Insets | None = None
    margin: Insets | None = None
    font: str | None = None
    font_size: Length | None = None
    weight: str | int | None = None
    outline: ColorSpec | None = None
    line_height: float | Length | None = None
    letter_spacing: Length | None = None
    word_spacing: Length | None = None
    text_decoration: str | None = None
    text_decoration_color: ColorSpec | None = None
    text_decoration_style: str | None = None
    text_transform: str | None = None
    text_shadow: TextShadow | None = None
    box_shadow: list[BoxShadow] | None = None
    text_align: str | None = None
    vertical_align: str | None = None
    display: str | None = None
    position: str | None = None
    top: Length | None = None
    right: Length | None = None
    bottom: Length | None = None
    left: Length | None = None
    width: Length | None = None
    height: Length | None = None
    min_width: Length | None = None
    min_height: Length | None = None
    max_width: Length | None = None
    max_height: Length | None = None
    flex_direction: str | None = None
    flex_wrap: str | None = None
    justify_content: str | None = None
    align_items: str | None = None
    align_content: str | None = None
    flex_grow: float | None = None
    flex_shrink: float | None = None
    flex_basis: Length | None = None
    align_self: str | None = None
    grid_template_columns: str | None = None
    grid_template_rows: str | None = None
    grid_gap: Length | None = None
    grid_column_gap: Length | None = None
    grid_row_gap: Length | None = None
    animations: list[Animation] | None = None
    transitions: list[Transition] | None = None
    keyframes: dict[str, Keyframes] | None = None
    filter: str | None = None
    transform: str | None = None
    transform_origin: str | None = None
    opacity: float | None = None
    background_image: Gradient | str | None = None
    background_position: str | None = None
    background_size: str | None = None
    background_repeat: str | None = None
    component_extras: dict[str, list[Any]] | None = field(default_factory=dict)
    raw_meta: dict[str, Any] | None = None
    custom_properties: dict[str, str] | None = field(default_factory=dict)

    def merge(self, other: ResolvedStyle) -> ResolvedStyle:
        merged = ResolvedStyle()
        for field_name in merged.__dataclass_fields__:
            value = getattr(other, field_name)
            if value is not None and field_name not in {"component_extras", "custom_properties"}:
                setattr(merged, field_name, value)
            else:
                setattr(merged, field_name, getattr(self, field_name))
        
        base_extras = self.component_extras or {}
        incoming_extras = other.component_extras or {}
        if base_extras or incoming_extras:
            merged.component_extras = {
                key: list(value)
                for key, value in base_extras.items()
            }
            for key, value in incoming_extras.items():
                if key in merged.component_extras:
                    merged.component_extras[key].extend(value)
                else:
                    merged.component_extras[key] = list(value)
        else:
            merged.component_extras = None

        base_props = self.custom_properties or {}
        incoming_props = other.custom_properties or {}
        if base_props or incoming_props:
            merged.custom_properties = {**base_props, **incoming_props}
        else:
            merged.custom_properties = None
        return merged


@dataclass(slots=True, frozen=True)
class Border:
    """Border definition containing width and optional style."""
    width: float
    style: str | None = None
    color: str | None = None


@dataclass(slots=True, frozen=True)
class FontProfile:
    """Semantic font declaration."""
    name: str
    size_px: float | None = None
    weight: str | int | None = None
    family: str | None = None


@dataclass(slots=True, frozen=True)
class RGBA:
    """RGBA colour with floating point alpha."""
    r: int
    g: int
    b: int
    a: float = 1.0


@dataclass(slots=True, frozen=True)
class HSLA:
    """HSLA colour specification."""
    h: float
    s: float
    lightness: float
    a: float = 1.0


@dataclass(slots=True, frozen=True)
class ColorFunction:
    """Generic functional colour specification (e.g. ``color-mix``)."""
    name: str
    args: list[str]


@dataclass(slots=True, frozen=True)
class ColorBlend:
    """Two colour blending specification."""
    mode: Literal[
        "multiply", "screen", "overlay", "soft-light", "hard-light",
        "color-dodge", "color-burn", "difference", "exclusion",
        "hue", "saturation", "color", "luminosity",
    ]
    color_a: str | RGBA | HSLA
    color_b: str | RGBA | HSLA


@dataclass(slots=True, frozen=True)
class ColorLiteral:
    """Renderer-agnostic color literal for internal representation.
    
    Represents a color value that is independent of any rendering backend.
    The kind field indicates the color format, and value holds the actual data.
    
    Attributes:
        kind: The color format - "hex", "rgb", "rgba", "hsl", "hsla", "ref", or "named"
        value: The color data:
            - hex: "#rrggbb" or "#rrggbbaa" string
            - rgb/rgba: (r, g, b) or (r, g, b, a) tuple
            - hsl/hsla: (h, s, l) or (h, s, l, a) tuple
            - ref/named: the reference name string
    """
    kind: Literal["hex", "rgb", "rgba", "hsl", "hsla", "ref", "named"]
    value: str | tuple[int, int, int] | tuple[int, int, int, int] | tuple[int, int, int, float] | tuple[float, float, float] | tuple[float, float, float, float]
    
    def to_rgb(self) -> tuple[int, int, int] | None:
        """Convert the color literal to an RGB tuple.
        
        Returns:
            RGB tuple (r, g, b) or None if conversion is not possible
        """
        from ornata.styling.colorkit.spaces import ColorSpaces
        
        if self.kind == "hex":
            hex_str = self.value if isinstance(self.value, str) else ""
            if len(hex_str) >= 6:
                cleaned = hex_str.lstrip("#")
                try:
                    r = int(cleaned[0:2], 16)
                    g = int(cleaned[2:4], 16)
                    b = int(cleaned[4:6], 16)
                    return (r, g, b)
                except ValueError:
                    return None
        elif self.kind in ("rgb", "rgba"):
            if isinstance(self.value, tuple) and len(self.value) >= 3:
                return (int(self.value[0]), int(self.value[1]), int(self.value[2]))
        elif self.kind in ("hsl", "hsla"):
            if isinstance(self.value, tuple) and len(self.value) >= 3:
                h, s, l_val = float(self.value[0]), float(self.value[1]), float(self.value[2])
                rgb = ColorSpaces.hsl_to_rgb((h, s, l_val))
                if rgb:
                    return (int(rgb[0]), int(rgb[1]), int(rgb[2]))
                return None
        return None


@dataclass(slots=True, frozen=True)
class BoxShadow:
    """Box shadow definition."""
    offset_x: Length
    offset_y: Length
    blur_radius: Length
    spread_radius: Length
    color: ColorSpec
    inset: bool = False


@dataclass(slots=True, frozen=True)
class BorderRadius:
    """Border radius for the four corners."""
    top_left: Length
    top_right: Length
    bottom_right: Length
    bottom_left: Length


@dataclass(slots=True, frozen=True)
class TextShadow:
    """Text shadow specification."""
    offset_x: Length
    offset_y: Length
    blur_radius: Length
    color: ColorSpec


@dataclass(slots=True, frozen=True)
class Gradient:
    """Representation of a linear, radial, or conic gradient."""
    type: Literal["linear", "radial", "conic"]
    colors: list[tuple[ColorSpec, float]]
    angle: float = 0.0
    center_x: float = 0.5
    center_y: float = 0.5


@dataclass(slots=True, frozen=True)
class StylingContext:
    """Context required to resolve a component style."""
    component_name: str
    state: Mapping[str, bool] | None = None
    theme_overrides: Mapping[str, str] | None = None
    caps: Any = None
    backend: BackendTarget = BackendTarget.GUI

    def active_states(self) -> frozenset[str]:
        return frozenset(key for key, value in (self.state or {}).items() if value)


@dataclass(slots=True)
class BackendStylePayload:
    """Backend-conditioned styling data produced by the styling subsystem."""
    backend: BackendTarget
    style: ResolvedStyle
    renderer_metadata: dict[str, Any] = field(default_factory=dict)
    layout_style: LayoutStyle | None = None
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Color:
    """RGBA color representation (0-255)."""
    r: int
    g: int
    b: int
    a: int = 255

    def __post_init__(self) -> None:
        self.r = max(0, min(255, int(self.r)))
        self.g = max(0, min(255, int(self.g)))
        self.b = max(0, min(255, int(self.b)))
        self.a = max(0, min(255, int(self.a)))

    @classmethod
    def from_rgba_bytes(cls, r: int, g: int, b: int, a: int = 255) -> Color:
        return cls(r, g, b, a)

    @classmethod
    def from_hex(cls, value: str) -> Color:
        cleaned = value.lstrip("#")
        if len(cleaned) not in (6, 8):
            raise ValueError(f"Invalid color literal: {value}")
        r = int(cleaned[0:2], 16)
        g = int(cleaned[2:4], 16)
        b = int(cleaned[4:6], 16)
        a = int(cleaned[6:8], 16) if len(cleaned) == 8 else 255
        return cls(r, g, b, a)

    def to_tuple(self) -> tuple[int, int, int, int]:
        return (self.r, self.g, self.b, self.a)

    def with_alpha(self, alpha: int) -> Color:
        return Color(self.r, self.g, self.b, alpha)

    def blend_over(self, other: Color) -> Color:
        src_alpha = self.a / 255.0
        dst_alpha = other.a / 255.0
        out_a = src_alpha + dst_alpha * (1.0 - src_alpha)
        if out_a == 0:
            return Color(0, 0, 0, 0)

        def blend_channel(src: int, dst: int) -> int:
            return int(
                ((src / 255.0) * src_alpha + (dst / 255.0) * dst_alpha * (1.0 - src_alpha))
                / out_a
                * 255
            )

        return Color(
            blend_channel(self.r, other.r),
            blend_channel(self.g, other.g),
            blend_channel(self.b, other.b),
            int(out_a * 255),
        )


@dataclass(slots=True)
class Font:
    """Font definition for styling/rendering."""
    family: str | None = None
    size: float | None = None
    weight: str | int | None = None
    style: str | None = None


@dataclass(slots=True, frozen=True)
class TypographyStyle:
    """Typography attributes shared between styling and rendering."""
    family: str = "Segoe UI"
    size: float = 14.0
    weight: str | int = "400"
    line_height: float | None = None
    letter_spacing: float | None = None
    casing: str | None = None


@dataclass(slots=True, frozen=True)
class BorderStyle:
    """Represents resolved border information for a component edge."""
    color: Color
    width: float = 1.0
    style: str = "solid"
    radius: float = 0.0


@dataclass(slots=True, frozen=True)
class ShadowStyle:
    """Represents a drop shadow configuration."""
    color: Color
    offset_x: float = 0.0
    offset_y: float = 0.0
    blur_radius: float = 0.0
    spread_radius: float = 0.0


@dataclass(slots=True, frozen=True)
class Theme:
    """A theme defines semantic color tokens mapped to color specs."""
    name: str
    palette: dict[str, str]


@dataclass(slots=True, frozen=True)
class ThemePalette:
    """Resolved palette for a theme with semantic color tokens."""
    name: str
    colors: dict[str, Color] = field(default_factory=dict)

    def get(self, token: str, default: Color | None = None) -> Color | None:
        return self.colors.get(token, default)


@dataclass(slots=True, frozen=True)
class ANSIColor:
    """Represents an ANSI color with RGB components."""
    red: int
    green: int
    blue: int

    def __post_init__(self) -> None:
        if not (0 <= self.red <= 255):
            raise ValueError(f"Red component must be 0-255, got {self.red}")
        if not (0 <= self.green <= 255):
            raise ValueError(f"Green component must be 0-255, got {self.green}")
        if not (0 <= self.blue <= 255):
            raise ValueError(f"Blue component must be 0-255, got {self.blue}")

    @classmethod
    def from_hex(cls, hex_color: str) -> ANSIColor:
        if hex_color.startswith("#"):
            hex_color = hex_color[1:]
        if len(hex_color) != 6:
            raise ValueError(f"Invalid hex color: {hex_color}")
        return cls(
            red=int(hex_color[0:2], 16),
            green=int(hex_color[2:4], 16),
            blue=int(hex_color[4:6], 16),
        )

    def to_ansi_16(self) -> int:
        if self.red > 128:
            if self.green > 128:
                return 10 if self.blue > 128 else 14
            if self.blue > 128:
                return 13
            return 9
        if self.green > 128:
            if self.blue > 128:
                return 6
            return 2
        if self.blue > 128:
            return 4
        return 0

    def to_ansi_256(self) -> int:
        r = (self.red * 5) // 255
        g = (self.green * 5) // 255
        b = (self.blue * 5) // 255
        return 16 + (r * 36) + (g * 6) + b


@dataclass(slots=True, frozen=True)
class TextStyle:
    """Represents text styling attributes."""
    foreground: ANSIColor | None = None
    background: ANSIColor | None = None
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strikethrough: bool = False
    blink: bool = False
    reverse: bool = False


@dataclass(frozen=True)
class CacheKey:
    """Immutable cache key for resolved styles."""
    component: str
    states: frozenset[str]
    overrides: tuple[tuple[str, str], ...]
    style_version: int
    theme_version: int
    caps_signature: int

    def __hash__(self) -> int:
        return hash((self.component, tuple(sorted(self.states)), self.theme_version, self.caps_signature))


@dataclass(slots=True)
class Lexer:
    """Small lexer providing character level utilities."""
    text: str
    filename: str
    pos: int = 0
    line: int = 1
    col: int = 1

    def peek(self) -> str:
        return self.text[self.pos : self.pos + 1]

    def advance(self) -> str:
        ch = self.text[self.pos : self.pos + 1]
        if not ch:
            return ""
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def span(self) -> Span:
        return Span(self.filename, self.line, self.col)

    def skip_ws_and_comments(self) -> None:
        while True:
            while self.peek() and self.peek().isspace():
                self.advance()
            if self.peek() == "#":
                while self.peek() and self.peek() != "\n":
                    self.advance()
                continue
            break


@dataclass(slots=True, frozen=True)
class Length:
    """Numeric value tagged with a unit."""
    value: float | int
    unit: LengthUnit = PX_UNIT

    @classmethod
    def from_token(cls, token: str) -> Length:
        stripped = token.strip()
        if not stripped:
            raise ValueError("length token cannot be empty")
        detected_unit: LengthUnit = PX_UNIT

        number = stripped
        from ornata.definitions.constants import SUFFIX_TO_UNIT
        for suffix, unit in SUFFIX_TO_UNIT.items():
            if stripped.endswith(suffix) and suffix != "px":
                detected_unit = unit
                number = stripped[: -len(suffix)]
                break
        else:
            if stripped.endswith("px"):
                detected_unit = PX_UNIT
                number = stripped[:-2]
        return cls(float(number), detected_unit)


@dataclass(slots=True, frozen=True)
class Insets:
    """Four sided inset (top/right/bottom/left)."""
    top: Length
    right: Length
    bottom: Length
    left: Length

    @classmethod
    def from_tokens(cls, tokens: list[str]) -> Insets:
        if not tokens:
            raise ValueError("at least one token required for insets")
        parsed = [Length.from_token(token) for token in tokens]
        if len(parsed) == 1:
            top = right = bottom = left = parsed[0]
        elif len(parsed) == 2:
            top, right = parsed
            bottom = top
            left = right
        elif len(parsed) == 3:
            top, right, bottom = parsed
            left = right
        else:
            top, right, bottom, left = parsed[:4]
        return cls(top, right, bottom, left)


@dataclass(slots=True, frozen=True)
class Transition:
    """Property transition metadata."""
    property: str
    duration: float
    delay: float = 0.0
    timing_function: str = "ease"


@dataclass(slots=True, frozen=True)
class MediaQuery:
    """Single media query constraint."""
    feature: str
    operator: str
    value: str | int | float
    negated: bool = False


@dataclass(slots=True, frozen=True)
class MediaRule:
    """A collection of component rules under media constraints."""
    queries: list[MediaQuery]
    rules: list[ComponentRule]


@dataclass(slots=True, frozen=True)
class PropertyMeta:
    name: str
    inheritable: bool = False

__all__ = [
    "HSLA",
    "RGBA",
    "ANSIColor",
    "Border",
    "BorderRadius",
    "BorderStyle",
    "BoxShadow",
    "Color",
    "ColorBlend",
    "ColorFunction",
    "ColorLiteral",
    "ColorToken",
    "Font",
    "FontDef",
    "FontProfile",
    "Gradient",
    "Insets",
    "Length",
    "MediaQuery",
    "MediaRule",
    "PaletteEntry",
    "Property",
    "PropertyMeta",
    "ResolvedStyle",
    "ShadowStyle",
    "Span",
    "Stylesheet",
    "StylingContext",
    "BackendStylePayload",
    "TextShadow",
    "TextStyle",
    "Theme",
    "ThemePalette",
    "Transition",
    "TypographyStyle",
    "CacheKey",
    "Lexer",
]