""" All Constants for Ornata."""

from __future__ import annotations

import re
import threading
from typing import TYPE_CHECKING, Any, Final

from ornata.api.exports.utils import ThreadSafeLRUCache
from ornata.api.exports.vdom import HostBindingRegistry
from ornata.definitions.dataclasses.styling import PropertyMeta
from ornata.definitions.enums import RendererType

if TYPE_CHECKING:
    from ornata.definitions.type_alias import (
        ANSI4BitRGBMap,
        ANSISequenceList,
        CacheLimit,
        DrawRegistryMap,
        ErrorList,
        RouteMask,
        SpacingScaleMap,
        StylePropertySet,
        SuffixToUnitMap,
        TypographyScaleMap,
        VirtualKeyCode,
        WarningList,
        WindowMessageCode,
        WindowStyleFlag,
    )


# ---------------------------------------------------------------------------
# Routing bit flags (event / message routing masks)
# ---------------------------------------------------------------------------

ROUTE_FILTER: RouteMask = 1
ROUTE_HANDLER: RouteMask = 2
ROUTE_GLOBAL: RouteMask = 4
ROUTE_SUBSYSTEM: RouteMask = 8
ROUTE_ALL: RouteMask = (
    ROUTE_FILTER | ROUTE_HANDLER | ROUTE_GLOBAL | ROUTE_SUBSYSTEM
)


# ---------------------------------------------------------------------------
# Core timing / layout defaults
# ---------------------------------------------------------------------------

ZERO_TIME: float = 0.0

DEFAULT_COMPONENT_WIDTH: float = 80.0
DEFAULT_COMPONENT_HEIGHT: float = 24.0

MIN_PATCH_OPTIMIZATION: int = 128


# ---------------------------------------------------------------------------
# Thread-local state / global registries
# ---------------------------------------------------------------------------

SCHED_LOCAL: threading.local = threading.local()
RECONCILER_LOCAL: threading.local = threading.local()

GLOBAL_REGISTRY: HostBindingRegistry = HostBindingRegistry()

# ---------------------------------------------------------------------------
# Styling engine configuration
# ---------------------------------------------------------------------------

VALID_STYLING_PROPERTIES: dict[RendererType, StylePropertySet] = {
    RendererType.CPU: {
        "color", "background", "background-color", "border", "border-color",
        "border-style", "border-width", "padding", "margin", "width", "height",
        "display", "position", "font-family", "font-size", "font-weight",
        "text-decoration", "text-align", "opacity", "visibility",
    },
    RendererType.DIRECTX11: {
        "color", "background", "background-color", "border", "border-color",
        "border-style", "border-width", "border-radius", "padding", "margin",
        "width", "height", "display", "position", "font-family", "font-size",
        "font-weight", "text-decoration", "text-align", "opacity", "visibility",
        "text-shadow", "box-shadow", "transform", "transition", "animation",
        "cursor", "z-index", "overflow",
    },
    RendererType.OPENGL: {
        "color", "background", "background-color", "border", "border-color",
        "border-style", "border-width", "border-radius", "padding", "margin",
        "width", "height", "display", "position", "font-family", "font-size",
        "font-weight", "text-decoration", "text-align", "opacity", "visibility",
        "text-shadow", "box-shadow", "transform", "transition", "animation",
        "cursor", "z-index", "overflow",
    },
}

VALUE_PATTERNS = {
    "color": re.compile(
        r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})"
        r"|rgb\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)"
        r"|rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*[\d.]+\s*\)"
        r"|hsl\(\s*\d+\s*,\s*\d+%\s*,\s*\d+%\s*\)"
        r"|hsla\(\s*\d+\s*,\s*\d+%\s*,\s*\d+%\s*,\s*[\d.]+\s*\)"
        r"|[a-zA-Z]+"
        r"|\$[\w-]+"
        r"|var\([^)]+\)$"
    ),
    "background": re.compile(
        r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})"
        r"|rgb\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)"
        r"|rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*[\d.]+\s*\)"
        r"|hsl\(\s*\d+\s*,\s*\d+%\s*,\s*\d+%\s*\)"
        r"|hsla\(\s*\d+\s*,\s*\d+%\s*,\s*\d+%\s*,\s*[\d.]+\s*\)"
        r"|[a-zA-Z]+"
        r"|\$[\w-]+"
        r"|var\([^)]+\)"
        r"|none"
        r"|transparent$"
    ),
    "border-width": re.compile(r"^\d+(px|em|rem|pt|%|thin|medium|thick)$"),
    "border-style": re.compile(r"^(solid|dashed|dotted|double|groove|ridge|inset|outset|none)$"),
    "padding": re.compile(r"^\d+(px|em|rem|pt|%)(\s+\d+(px|em|rem|pt|%))*$"),
    "margin": re.compile(r"^\d+(px|em|rem|pt|%)(\s+\d+(px|em|rem|pt|%))*$"),
    "width": re.compile(r"^\d+(px|em|rem|pt|%|vw|vh|auto)$"),
    "height": re.compile(r"^\d+(px|em|rem|pt|%|vw|vh|auto)$"),
    "font-size": re.compile(r"^\d+(px|em|rem|pt|%)$"),
    "font-weight": re.compile(r"^(normal|bold|lighter|bolder|100|200|300|400|500|600|700|800|900)$"),
    "opacity": re.compile(r"^[\d.]+$"),
    "z-index": re.compile(r"^-?\d+$"),
    "border-radius": re.compile(r"^\d+(px|em|rem|pt|%)$"),
}

SPACING_SCALE: SpacingScaleMap = {
    "none": 0,
    "xs": 1,
    "sm": 2,
    "md": 4,
    "lg": 6,
    "xl": 8,
}

TYPOGRAPHY_SCALE: TypographyScaleMap = {
    "xs": 1,
    "sm": 1,
    "md": 1,
    "lg": 1,
    "xl": 1,
}

PROPERTIES: dict[str, PropertyMeta] = {
    "color": PropertyMeta("color"),
    "background": PropertyMeta("background"),
    "border": PropertyMeta("border"),
    "border-style": PropertyMeta("border-style"),
    "border-color": PropertyMeta("border-color"),
    "padding": PropertyMeta("padding"),
    "font": PropertyMeta("font"),
    "font-size": PropertyMeta("font-size"),
    "weight": PropertyMeta("weight"),
    "family": PropertyMeta("family"),
    "outline": PropertyMeta("outline"),
    "fill": PropertyMeta("fill"),
    "track": PropertyMeta("track"),
}


# ---------------------------------------------------------------------------
# Length units / suffix parsing
# ---------------------------------------------------------------------------

SUFFIX_TO_UNIT: SuffixToUnitMap = {
    "px": "px",
    "em": "em",
    "cell": "cell",
    "%": "%",
}


# ---------------------------------------------------------------------------
# Cache limits and error/warning tracking
# ---------------------------------------------------------------------------

COMPONENT_CACHE_LIMIT: CacheLimit = 8192
EFFECTS_CACHE_LIMIT: CacheLimit = 8192
EVENTS_CACHE_LIMIT: CacheLimit = 8192
GPU_CACHE_LIMIT: CacheLimit = 8192
LAYOUT_CACHE_LIMIT: CacheLimit = 8192
RENDERING_CACHE_LIMIT: CacheLimit = 8192
STYLING_CACHE_LIMIT: CacheLimit = 8192
VDOM_CACHE_LIMIT: CacheLimit = 8192

LAST_COMPONENT_ERRORS: ErrorList = []
LAST_EFFECTS_ERRORS: ErrorList = []
LAST_EVENTS_ERRORS: ErrorList = []
LAST_GPU_ERRORS: ErrorList = []
LAST_LAYOUT_ERRORS: ErrorList = []
LAST_RENDERING_ERRORS: ErrorList = []
LAST_STYLING_ERRORS: ErrorList = []
LAST_VDOM_ERRORS: ErrorList = []

LAST_COMPONENT_WARNINGS: WarningList = []
LAST_EFFECTS_WARNINGS: WarningList = []
LAST_EVENTS_WARNINGS: WarningList = []
LAST_GPU_WARNINGS: WarningList = []
LAST_LAYOUT_WARNINGS: WarningList = []
LAST_RENDERING_WARNINGS: WarningList = []
LAST_STYLING_WARNINGS: WarningList = []
LAST_VDOM_WARNINGS: WarningList = []


# Color pipeline caches (styling/ANSI/front-end)
ANSI_CACHE_LIMIT: int = 2048
BACKGROUND_CACHE_LIMIT: int = 1024
RGB_CACHE_LIMIT: int = 2048
GRADIENT_CACHE_LIMIT: int = 128

COLOR_CACHE: ThreadSafeLRUCache[Any, Any] = ThreadSafeLRUCache(max_size=1000)
REGISTRY: DrawRegistryMap = {}


# ---------------------------------------------------------------------------
# Color transforms (color-blindness simulation)
# ---------------------------------------------------------------------------

TRANSFORMS = {
    "protanopia": (
        (0.56667, 0.43333, 0.00000),
        (0.55833, 0.44167, 0.00000),
        (0.00000, 0.24167, 0.75833),
    ),
    "deuteranopia": (
        (0.62500, 0.37500, 0.00000),
        (0.70000, 0.30000, 0.00000),
        (0.00000, 0.30000, 0.70000),
    ),
    "tritanopia": (
        (0.95000, 0.05000, 0.00000),
        (0.00000, 0.43333, 0.56667),
        (0.00000, 0.47500, 0.52500),
    ),
}


# ---------------------------------------------------------------------------
# Regex patterns used by styling / parsing
# ---------------------------------------------------------------------------

VAR_PATTERN = re.compile(r"^var\((.+)\)$")
THEME_TOKEN_PATTERN = re.compile(r"^\$(.+)$")
ANSI_INDEX_PATTERN = re.compile(r"^ansi(\d+)$")
HEX_PATTERN = re.compile(r"^#[0-9a-f]{6}$", re.IGNORECASE)
RGB_PATTERN = re.compile(r"^rgb\((\d+),\s*(\d+),\s*(\d+)\)$", re.IGNORECASE)
RGBA_PATTERN = re.compile(r"^rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)$", re.IGNORECASE)
HSL_PATTERN = re.compile(r"^hsl\(([\d.]+),\s*([\d.]+%?),\s*([\d.]+%?)\)$", re.IGNORECASE)
HSLA_PATTERN = re.compile(r"^hsla\(([\d.]+),\s*([\d.]+%?),\s*([\d.]+%?),\s*([\d.]+)\)$", re.IGNORECASE)
RGB_COMMA_PATTERN = re.compile(r"^(\d+),\s*(\d+),\s*(\d+)$")


ANSI_4BIT_RGB: ANSI4BitRGBMap = {
    "30": (0, 0, 0), "31": (187, 0, 0), "32": (0, 187, 0), "33": (187, 187, 0),
    "34": (0, 0, 187), "35": (187, 0, 187), "36": (0, 187, 187), "37": (255, 255, 255),
    "90": (85, 85, 85), "91": (255, 85, 85), "92": (85, 255, 85), "93": (255, 255, 85),
    "94": (85, 85, 255), "95": (255, 85, 255), "96": (85, 255, 255), "97": (255, 255, 255),
}

BACKGROUND_COLORS = {
    "bg_red": "\033[101m", "bg_green": "\033[102m", "bg_yellow": "\033[103m",
    "bg_blue": "\033[104m", "bg_magenta": "\033[105m", "bg_cyan": "\033[106m",
    "bg_white": "\033[107m", "bg_black": "\033[40m", "bg_gray": "\033[100m",
    "bg_light_gray": "\033[47m", "bg_orange": "\033[48;5;208m", "bg_brown": "\033[48;5;94m",
    "bg_purple": "\033[48;5;93m", "bg_gold": "\033[48;5;220m", "bg_pink": "\033[48;5;205m",
    "bg_lime": "\033[48;5;46m", "bg_navy": "\033[48;5;17m", "bg_teal": "\033[48;5;30m",
}

EFFECTS = {
    "reset": "\033[0m", "bold": "\033[1m", "dim": "\033[2m", "italic": "\033[3m",
    "underline": "\033[4m", "double_underline": "\033[21m", "blink": "\033[5m",
    "reverse": "\033[7m", "hidden": "\033[8m", "strikethrough": "\033[9m",
    "overline": "\033[53m", "framed": "\033[51m", "encircled": "\033[52m",
}


# ---------------------------------------------------------------------------
# ANSI escape control sequences & SGR codes
# ---------------------------------------------------------------------------

ESC: Final[str] = "\x1b"
CSI: Final[str] = f"{ESC}["
OSC: Final[str] = f"{ESC}]"
BEL: Final[str] = "\x07"
BS: Final[str] = "\x08"
CR: Final[str] = "\r"
LF: Final[str] = "\n"
CRLF: Final[str] = f"{CR}{LF}"

SGR_RESET_ALL: Final[int] = 0
SGR_BOLD: Final[int] = 1
SGR_DIM: Final[int] = 2
SGR_ITALIC: Final[int] = 3
SGR_UNDERLINE: Final[int] = 4
SGR_BLINK: Final[int] = 5
SGR_RAPID_BLINK: Final[int] = 6
SGR_REVERSE: Final[int] = 7
SGR_HIDDEN: Final[int] = 8
SGR_STRIKETHROUGH: Final[int] = 9

SGR_RESET_BOLD_DIM: Final[int] = 22
SGR_RESET_ITALIC: Final[int] = 23
SGR_RESET_UNDERLINE: Final[int] = 24
SGR_RESET_BLINK: Final[int] = 25
SGR_RESET_REVERSE: Final[int] = 27
SGR_RESET_HIDDEN: Final[int] = 28
SGR_RESET_STRIKETHROUGH: Final[int] = 29

SGR_FONT_PRIMARY: Final[int] = 10
SGR_FONT_ALTERNATE_1: Final[int] = 11
SGR_FONT_ALTERNATE_2: Final[int] = 12
SGR_FONT_ALTERNATE_3: Final[int] = 13
SGR_FONT_ALTERNATE_4: Final[int] = 14
SGR_FONT_ALTERNATE_5: Final[int] = 15
SGR_FONT_ALTERNATE_6: Final[int] = 16
SGR_FONT_ALTERNATE_7: Final[int] = 17
SGR_FONT_ALTERNATE_8: Final[int] = 18
SGR_FONT_ALTERNATE_9: Final[int] = 19

SGR_FRAKTUR: Final[int] = 20
SGR_UNDERLINE_DOUBLE: Final[int] = 21

SGR_IDEOGRAM_UNDERLINE: Final[int] = 60
SGR_IDEOGRAM_DOUBLE_UNDERLINE: Final[int] = 61
SGR_IDEOGRAM_OVERLINE: Final[int] = 62
SGR_IDEOGRAM_DOUBLE_OVERLINE: Final[int] = 63
SGR_IDEOGRAM_STRESS: Final[int] = 64

SGR_SUPERSCRIPT: Final[int] = 73
SGR_SUBSCRIPT: Final[int] = 74

RESET_ALL: Final[str] = f"{CSI}0m"
RESET_FOREGROUND: Final[str] = f"{CSI}39m"
RESET_BACKGROUND: Final[str] = f"{CSI}49m"

FG_BLACK: Final[str] = f"{CSI}30m"
FG_RED: Final[str] = f"{CSI}31m"
FG_GREEN: Final[str] = f"{CSI}32m"
FG_YELLOW: Final[str] = f"{CSI}33m"
FG_BLUE: Final[str] = f"{CSI}34m"
FG_MAGENTA: Final[str] = f"{CSI}35m"
FG_CYAN: Final[str] = f"{CSI}36m"
FG_WHITE: Final[str] = f"{CSI}37m"

BG_BLACK: Final[str] = f"{CSI}40m"
BG_RED: Final[str] = f"{CSI}41m"
BG_GREEN: Final[str] = f"{CSI}42m"
BG_YELLOW: Final[str] = f"{CSI}43m"
BG_BLUE: Final[str] = f"{CSI}44m"
BG_MAGENTA: Final[str] = f"{CSI}45m"
BG_CYAN: Final[str] = f"{CSI}46m"
BG_WHITE: Final[str] = f"{CSI}47m"

FG_BRIGHT_BLACK: Final[str] = f"{CSI}90m"
FG_BRIGHT_RED: Final[str] = f"{CSI}91m"
FG_BRIGHT_GREEN: Final[str] = f"{CSI}92m"
FG_BRIGHT_YELLOW: Final[str] = f"{CSI}93m"
FG_BRIGHT_BLUE: Final[str] = f"{CSI}94m"
FG_BRIGHT_MAGENTA: Final[str] = f"{CSI}95m"
FG_BRIGHT_CYAN: Final[str] = f"{CSI}96m"
FG_BRIGHT_WHITE: Final[str] = f"{CSI}97m"

BG_BRIGHT_BLACK: Final[str] = f"{CSI}100m"
BG_BRIGHT_RED: Final[str] = f"{CSI}101m"
BG_BRIGHT_GREEN: Final[str] = f"{CSI}102m"
BG_BRIGHT_YELLOW: Final[str] = f"{CSI}103m"
BG_BRIGHT_BLUE: Final[str] = f"{CSI}104m"
BG_BRIGHT_MAGENTA: Final[str] = f"{CSI}105m"
BG_BRIGHT_CYAN: Final[str] = f"{CSI}106m"
BG_BRIGHT_WHITE: Final[str] = f"{CSI}107m"

ANSI_16_COLORS: dict[str, int] = {
    "black": 0, "red": 1, "green": 2, "yellow": 3, "blue": 4,
    "magenta": 5, "cyan": 6, "white": 7,
}

ANSI_16_FOREGROUND: ANSISequenceList = [
    FG_BLACK, FG_RED, FG_GREEN, FG_YELLOW, FG_BLUE, FG_MAGENTA, FG_CYAN, FG_WHITE,
    FG_BRIGHT_BLACK, FG_BRIGHT_RED, FG_BRIGHT_GREEN, FG_BRIGHT_YELLOW,
    FG_BRIGHT_BLUE, FG_BRIGHT_MAGENTA, FG_BRIGHT_CYAN, FG_BRIGHT_WHITE,
]

ANSI_16_BACKGROUND: ANSISequenceList = [
    BG_BLACK, BG_RED, BG_GREEN, BG_YELLOW, BG_BLUE, BG_MAGENTA, BG_CYAN, BG_WHITE,
    BG_BRIGHT_BLACK, BG_BRIGHT_RED, BG_BRIGHT_GREEN, BG_BRIGHT_YELLOW,
    BG_BRIGHT_BLUE, BG_BRIGHT_MAGENTA, BG_BRIGHT_CYAN, BG_BRIGHT_WHITE,
]


# ---------------------------------------------------------------------------
# High-level ANSI color objects
# ---------------------------------------------------------------------------

COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_RED = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_YELLOW = (255, 255, 0)
COLOR_MAGENTA = (255, 0, 255)
COLOR_CYAN = (0, 255, 255)
COLOR_GRAY = (128, 128, 128)


# ---------------------------------------------------------------------------
# Cursor control / screen manipulation
# ---------------------------------------------------------------------------

CURSOR_UP: Final[str] = f"{CSI}A"
CURSOR_DOWN: Final[str] = f"{CSI}B"
CURSOR_RIGHT: Final[str] = f"{CSI}C"
CURSOR_LEFT: Final[str] = f"{CSI}D"

CURSOR_HOME: Final[str] = f"{CSI}H"
CURSOR_SAVE: Final[str] = f"{CSI}s"
CURSOR_RESTORE: Final[str] = f"{CSI}u"

CURSOR_HIDE: Final[str] = f"{CSI}?25l"
CURSOR_SHOW: Final[str] = f"{CSI}?25h"

CURSOR_BLOCK: Final[str] = f"{CSI}2 q"
CURSOR_UNDERLINE: Final[str] = f"{CSI}4 q"
CURSOR_BAR: Final[str] = f"{CSI}6 q"

CLEAR_SCREEN: Final[str] = f"{CSI}2J"
CLEAR_SCREEN_FROM_CURSOR: Final[str] = f"{CSI}0J"
CLEAR_SCREEN_TO_CURSOR: Final[str] = f"{CSI}1J"

CLEAR_LINE: Final[str] = f"{CSI}2K"
CLEAR_LINE_FROM_CURSOR: Final[str] = f"{CSI}0K"
CLEAR_LINE_TO_CURSOR: Final[str] = f"{CSI}1K"

ENTER_ALTERNATE_BUFFER: Final[str] = f"{CSI}?1049h"
EXIT_ALTERNATE_BUFFER: Final[str] = f"{CSI}?1049l"

SCROLL_UP: Final[str] = f"{CSI}S"
SCROLL_DOWN: Final[str] = f"{CSI}T"

ERASE_DISPLAY: Final[str] = f"{CSI}J"
ERASE_LINE: Final[str] = f"{CSI}K"


# ---------------------------------------------------------------------------
# Windows / Win32 integration constants
# ---------------------------------------------------------------------------

WINDOW_CLASS_NAME: Final[str] = "OrnataGUIWindow"

WS_OVERLAPPEDWINDOW: WindowStyleFlag = 0x00CF0000
WS_VISIBLE: WindowStyleFlag = 0x10000000
CW_USEDEFAULT: Final[int] = 0x80000000

WM_DESTROY: WindowMessageCode = 0x0002
WM_PAINT: WindowMessageCode = 0x000F
WM_SIZE: WindowMessageCode = 0x0005
WM_CLOSE: WindowMessageCode = 0x0010

WM_KEYDOWN: WindowMessageCode = 0x0100
WM_KEYUP: WindowMessageCode = 0x0101
WM_LBUTTONDOWN: WindowMessageCode = 0x0201
WM_LBUTTONUP: WindowMessageCode = 0x0202
WM_RBUTTONDOWN: WindowMessageCode = 0x0204
WM_RBUTTONUP: WindowMessageCode = 0x0205
WM_MOUSEMOVE: WindowMessageCode = 0x0200
WM_MOUSEWHEEL: WindowMessageCode = 0x020A

VK_ESCAPE: VirtualKeyCode = 0x1B
VK_SHIFT: VirtualKeyCode = 0x10
VK_CONTROL: VirtualKeyCode = 0x11
VK_MENU: VirtualKeyCode = 0x12

HWND_MESSAGE: Final[int] = -3

__all__ = [
    "ROUTE_FILTER",
    "ROUTE_HANDLER",
    "ROUTE_GLOBAL",
    "ROUTE_SUBSYSTEM",
    "ROUTE_ALL",
    "ZERO_TIME",
    "DEFAULT_COMPONENT_WIDTH",
    "DEFAULT_COMPONENT_HEIGHT",
    "MIN_PATCH_OPTIMIZATION",
    "SCHED_LOCAL",
    "RECONCILER_LOCAL",
    "GLOBAL_REGISTRY",
    "VALID_STYLING_PROPERTIES",
    "VALUE_PATTERNS",
    "SPACING_SCALE",
    "TYPOGRAPHY_SCALE",
    "PROPERTIES",
    "SUFFIX_TO_UNIT",
    "COMPONENT_CACHE_LIMIT",
    "EFFECTS_CACHE_LIMIT",
    "EVENTS_CACHE_LIMIT",
    "GPU_CACHE_LIMIT",
    "LAYOUT_CACHE_LIMIT",
    "RENDERING_CACHE_LIMIT",
    "STYLING_CACHE_LIMIT",
    "VDOM_CACHE_LIMIT",
    "LAST_COMPONENT_ERRORS",
    "LAST_EFFECTS_ERRORS",
    "LAST_EVENTS_ERRORS",
    "LAST_GPU_ERRORS",
    "LAST_LAYOUT_ERRORS",
    "LAST_RENDERING_ERRORS",
    "LAST_STYLING_ERRORS",
    "LAST_VDOM_ERRORS",
    "LAST_COMPONENT_WARNINGS",
    "LAST_EFFECTS_WARNINGS",
    "LAST_EVENTS_WARNINGS",
    "LAST_GPU_WARNINGS",
    "LAST_LAYOUT_WARNINGS",
    "LAST_RENDERING_WARNINGS",
    "LAST_STYLING_WARNINGS",
    "LAST_VDOM_WARNINGS",
    "ANSI_CACHE_LIMIT",
    "BACKGROUND_CACHE_LIMIT",
    "RGB_CACHE_LIMIT",
    "GRADIENT_CACHE_LIMIT",
    "COLOR_CACHE",
    "TRANSFORMS",
    "VAR_PATTERN",
    "THEME_TOKEN_PATTERN",
    "ANSI_INDEX_PATTERN",
    "HEX_PATTERN",
    "RGB_PATTERN",
    "RGBA_PATTERN",
    "HSL_PATTERN",
    "HSLA_PATTERN",
    "RGB_COMMA_PATTERN",
    "NAMED_COLORS",
    "NAMED_HEX",
    "ANSI_4BIT_RGB",
    "BACKGROUND_COLORS",
    "EFFECTS",
    "ESC",
    "CSI",
    "OSC",
    "BEL",
    "BS",
    "CR",
    "LF",
    "CRLF",
    "ESC",
    "CSI",
    "SGR_RESET_ALL",
    "SGR_BOLD",
    "SGR_DIM",
    "SGR_ITALIC",
    "SGR_UNDERLINE",
    "SGR_BLINK",
    "SGR_RAPID_BLINK",
    "SGR_REVERSE",
    "SGR_HIDDEN",
    "SGR_STRIKETHROUGH",
    "SGR_RESET_BOLD_DIM",
    "SGR_RESET_ITALIC",
    "SGR_RESET_UNDERLINE",
    "SGR_RESET_BLINK",
    "SGR_RESET_REVERSE",
    "SGR_RESET_HIDDEN",
    "SGR_RESET_STRIKETHROUGH",
    "SGR_FONT_PRIMARY",
    "SGR_FONT_ALTERNATE_1",
    "SGR_FONT_ALTERNATE_2",
    "SGR_FONT_ALTERNATE_3",
    "SGR_FONT_ALTERNATE_4",
    "SGR_FONT_ALTERNATE_5",
    "SGR_FONT_ALTERNATE_6",
    "SGR_FONT_ALTERNATE_7",
    "SGR_FONT_ALTERNATE_8",
    "SGR_FONT_ALTERNATE_9",
    "SGR_FRAKTUR",
    "SGR_UNDERLINE_DOUBLE",
    "SGR_IDEOGRAM_UNDERLINE",
    "SGR_IDEOGRAM_DOUBLE_UNDERLINE",
    "SGR_IDEOGRAM_OVERLINE",
    "SGR_IDEOGRAM_DOUBLE_OVERLINE",
    "SGR_IDEOGRAM_STRESS",
    "SGR_SUPERSCRIPT",
    "SGR_SUBSCRIPT",
    "RESET_ALL",
    "RESET_FOREGROUND",
    "RESET_BACKGROUND",
    "FG_BLACK",
    "FG_RED",
    "FG_GREEN",
    "FG_YELLOW",
    "FG_BLUE",
    "FG_MAGENTA",
    "FG_CYAN",
    "FG_WHITE",
    "BG_BLACK",
    "BG_RED",
    "BG_GREEN",
    "BG_YELLOW",
    "BG_BLUE",
    "BG_MAGENTA",
    "BG_CYAN",
    "BG_WHITE",
    "FG_BRIGHT_BLACK",
    "FG_BRIGHT_RED",
    "FG_BRIGHT_GREEN",
    "FG_BRIGHT_YELLOW",
    "FG_BRIGHT_BLUE",
    "FG_BRIGHT_MAGENTA",
    "FG_BRIGHT_CYAN",
    "FG_BRIGHT_WHITE",
    "BG_BRIGHT_BLACK",
    "BG_BRIGHT_RED",
    "BG_BRIGHT_GREEN",
    "BG_BRIGHT_YELLOW",
    "BG_BRIGHT_BLUE",
    "BG_BRIGHT_MAGENTA",
    "BG_BRIGHT_CYAN",
    "BG_BRIGHT_WHITE",
    "ANSI_16_COLORS",
    "ANSI_16_FOREGROUND",
    "ANSI_16_BACKGROUND",
    "COLOR_BLACK",
    "COLOR_WHITE",
    "COLOR_RED",
    "COLOR_GREEN",
    "COLOR_BLUE",
    "COLOR_YELLOW",
    "COLOR_MAGENTA",
    "COLOR_CYAN",
    "COLOR_GRAY",
    "CURSOR_UP",
    "CURSOR_DOWN",
    "CURSOR_RIGHT",
    "CURSOR_LEFT",
    "CURSOR_HOME",
    "CURSOR_SAVE",
    "CURSOR_RESTORE",
    "CURSOR_HIDE",
    "CURSOR_SHOW",
    "CURSOR_BLOCK",
    "CURSOR_UNDERLINE",
    "CURSOR_BAR",
    "CLEAR_SCREEN",
    "CLEAR_SCREEN_FROM_CURSOR",
    "CLEAR_SCREEN_TO_CURSOR",
    "CLEAR_LINE",
    "CLEAR_LINE_FROM_CURSOR",
    "CLEAR_LINE_TO_CURSOR",
    "ENTER_ALTERNATE_BUFFER",
    "EXIT_ALTERNATE_BUFFER",
    "SCROLL_UP",
    "SCROLL_DOWN",
    "ERASE_DISPLAY",
    "ERASE_LINE",
    "WINDOW_CLASS_NAME",
    "WS_OVERLAPPEDWINDOW",
    "WS_VISIBLE",
    "CW_USEDEFAULT",
    "WM_DESTROY",
    "WM_PAINT",
    "WM_SIZE",
    "WM_CLOSE",
    "WM_KEYDOWN",
    "WM_KEYUP",
    "WM_LBUTTONDOWN",
    "WM_LBUTTONUP",
    "WM_RBUTTONDOWN",
    "WM_RBUTTONUP",
    "WM_MOUSEMOVE",
    "WM_MOUSEWHEEL",
    "VK_ESCAPE",
    "VK_SHIFT",
    "VK_CONTROL",
    "VK_MENU",
    "HWND_MESSAGE",
]