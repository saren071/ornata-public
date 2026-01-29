""" All Type aliases for Ornata. """
from typing import Callable, Literal

from ornata.definitions.dataclasses.rendering import RenderSignal
from ornata.definitions.dataclasses.styling import HSLA, RGBA, ColorBlend, ColorFunction
from ornata.definitions.protocols import Canvas, GuiNodeLike

type Vector2 = tuple[float, float]
type Vector3 = tuple[float, float, float]
type Vector4 = tuple[float, float, float, float]
type LengthUnit = Literal["px", "cell", "%", "em"]
type ColorSpec = str | RGBA | HSLA | ColorFunction | ColorBlend
type EasingFunction = Literal["linear", "ease", "ease-in", "ease-out", "ease-in-out", "step-start", "step-end", "cubic-bezier"]
type ErrorList = list[str]
type WarningList = list[str]
type CacheLimit = int
type BorderStyleType = dict[str, dict[str, str]]
type ANSI4BitRGBMap = dict[str, tuple[int, int, int]]
type AnsiColorCache = dict[str, tuple[int, int, int]]
type ANSISequenceList = list[str]
type BackgroundColorMap = dict[str, tuple[int, int, int]]
type BoxGlyphMap = dict[str, tuple[int, int, int]]
type ColorTransformMap = dict[str, tuple[int, int, int]]
type DrawRegistryMap = dict[str, tuple[int, int, int]]
type EffectCodeMap = dict[str, tuple[int, int, int]]
type LoggingColorMap = dict[str, tuple[int, int, int]]
type NamedColorMap = dict[str, tuple[int, int, int]]
type NamedHexMap = dict[str, tuple[int, int, int]]
type RegexPattern = str
type RouteMask = int
type SpacingScaleMap = dict[str, int]
type StylePropertySet = set[str]
type SuffixToUnitMap = dict[str, LengthUnit]
type TypographyScaleMap = dict[str, int]
type ValuePatternMap = dict[str, str]
type VirtualKeyCode = int
type WindowMessageCode = int
type WindowStyleFlag = int
type FlexDirection = Literal["row", "column"]
type JustifyContent = Literal["start", "center", "end", "space-between", "space-around", "space-evenly"]
type AlignItems = Literal["start", "center", "end", "stretch"]
type TextDecorationStyle = Literal["solid", "double", "dotted", "dashed", "wavy"]
type TextTransform = Literal["uppercase", "lowercase", "capitalize", "none"]
type TextAlign = Literal["left", "right", "center", "justify"]
type VerticalAlign = Literal["top", "middle", "bottom", "baseline"]
type SignalHandler = Callable[[RenderSignal], None]
type DrawFunc = Callable[[Canvas, GuiNodeLike], None]

__all__ = [
    "Vector2",
    "Vector3",
    "Vector4",
    "LengthUnit",
    "ColorSpec",
    "EasingFunction",
    "ErrorList",
    "WarningList",
    "CacheLimit",
    "BorderStyleType",
    "ANSI4BitRGBMap",
    "AnsiColorCache",
    "ANSISequenceList",
    "BackgroundColorMap",
    "BoxGlyphMap",
    "ColorTransformMap",
    "DrawRegistryMap",
    "EffectCodeMap",
    "LoggingColorMap",
    "NamedColorMap",
    "NamedHexMap",
    "RegexPattern",
    "RouteMask",
    "SpacingScaleMap",
    "StylePropertySet",
    "SuffixToUnitMap",
    "TypographyScaleMap",
    "ValuePatternMap",
    "VirtualKeyCode",
    "WindowMessageCode",
    "WindowStyleFlag",
    "FlexDirection",
    "JustifyContent",
    "AlignItems",
    "TextDecorationStyle",
    "TextTransform",
    "TextAlign",
    "VerticalAlign",
    "SignalHandler",
    "DrawFunc",
]