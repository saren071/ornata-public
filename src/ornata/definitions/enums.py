"""All Enum definitions for Ornata."""

from __future__ import annotations

from enum import Enum, IntEnum, auto


class AnimationEventType(Enum):
    ANIMATION_START = "animation_start"
    ANIMATION_END = "animation_end"
    ANIMATION_FRAME = "animation_frame"
    ANIMATION_PAUSE = "animation_pause"
    ANIMATION_RESUME = "animation_resume"
    SEQUENCE_START = "sequence_start"
    SEQUENCE_END = "sequence_end"


class AnimationDirection(Enum):
    NORMAL = "normal"
    REVERSE = "reverse"
    ALTERNATE = "alternate"
    ALTERNATE_REVERSE = "alternate_reverse"


class BufferUsage(Enum):
    STATIC = "static"
    DYNAMIC = "dynamic"
    STREAM = "stream"


class RendererType(Enum):
    DIRECTX11 = "directx11"
    OPENGL = "opengl"
    CPU = "cpu"


class BlendMode(Enum):
    NORMAL = "normal"
    REPLACE = "replace"
    ALPHA = "alpha"
    ADD = "add"
    SUBTRACT = "subtract"
    MULTIPLY = "multiply"
    SCREEN = "screen"
    OVERLAY = "overlay"
    DARKEN = "darken"
    LIGHTEN = "lighten"
    COLOR_DODGE = "color_dodge"
    COLOR_BURN = "color_burn"
    HARD_LIGHT = "hard_light"
    SOFT_LIGHT = "soft_light"
    DIFFERENCE = "difference"
    EXCLUSION = "exclusion"
    HUE = "hue"
    SATURATION = "saturation"
    COLOR = "color"
    LUMINOSITY = "luminosity"


class BlendFactor(Enum):
    ZERO = "zero"
    ONE = "one"
    SRC_COLOR = "src_color"
    ONE_MINUS_SRC_COLOR = "one_minus_src_color"
    DST_COLOR = "dst_color"
    ONE_MINUS_DST_COLOR = "one_minus_dst_color"
    SRC_ALPHA = "src_alpha"
    ONE_MINUS_SRC_ALPHA = "one_minus_src_alpha"
    DST_ALPHA = "dst_alpha"
    ONE_MINUS_DST_ALPHA = "one_minus_dst_alpha"


class BlendOperation(Enum):
    ADD = "add"
    SUBTRACT = "subtract"
    REVERSE_SUBTRACT = "reverse_subtract"
    MIN = "min"
    MAX = "max"


class DepthFunction(Enum):
    NEVER = "never"
    LESS = "less"
    EQUAL = "equal"
    LESS_EQUAL = "less_equal"
    GREATER = "greater"
    NOT_EQUAL = "not_equal"
    GREATER_EQUAL = "greater_equal"
    ALWAYS = "always"


class CullMode(Enum):
    NONE = "none"
    FRONT = "front"
    BACK = "back"


class FillMode(Enum):
    SOLID = "solid"
    WIREFRAME = "wireframe"


class ResidencyState(Enum):
    RESIDENT = "resident"
    EVICTED = "evicted"
    PENDING_EVICTION = "pending_eviction"


class TransferDirection(Enum):
    CPU_TO_GPU = "cpu_to_gpu"
    GPU_TO_CPU = "gpu_to_cpu"


class BarrierType(Enum):
    READ = "read"
    WRITE = "write"
    READ_WRITE = "read_write"
    ALL = "all"


class SyncType(Enum):
    FENCE = "fence"
    EVENT = "event"
    SEMAPHORE = "semaphore"


class FilterMode(Enum):
    NEAREST = "nearest"
    LINEAR = "linear"
    NEAREST_MIPMAP_NEAREST = "nearest_mipmap_nearest"
    LINEAR_MIPMAP_NEAREST = "linear_mipmap_nearest"
    NEAREST_MIPMAP_LINEAR = "nearest_mipmap_linear"
    LINEAR_MIPMAP_LINEAR = "linear_mipmap_linear"


class WrapMode(Enum):
    CLAMP_TO_EDGE = "clamp_to_edge"
    CLAMP_TO_BORDER = "clamp_to_border"
    REPEAT = "repeat"
    MIRRORED_REPEAT = "mirrored_repeat"


class CubeMapFace(Enum):
    POSITIVE_X = 0
    NEGATIVE_X = 1
    POSITIVE_Y = 2
    NEGATIVE_Y = 3
    POSITIVE_Z = 4
    NEGATIVE_Z = 5


class TextureFormat(Enum):
    RGBA8 = "rgba8"
    RGB8 = "rgb8"
    RGBA16F = "rgba16f"
    RGB16F = "rgb16f"
    RGBA32F = "rgba32f"
    RGB32F = "rgb32f"
    DEPTH24 = "depth24"
    DEPTH32F = "depth32f"
    STENCIL8 = "stencil8"


class TextureUsage(Enum):
    SHADER_READ = "shader_read"
    SHADER_WRITE = "shader_write"
    RENDER_TARGET = "render_target"
    DEPTH_STENCIL = "depth_stencil"


class InputEventType(Enum):
    KEY_DOWN = auto()
    KEY_UP = auto()
    MOUSE_DOWN = auto()
    MOUSE_UP = auto()
    MOUSE_MOVE = auto()
    MOUSE_WHEEL = auto()
    TOUCH_START = auto()
    TOUCH_MOVE = auto()
    TOUCH_END = auto()
    WINDOW_FOCUS = auto()
    WINDOW_BLUR = auto()
    WINDOW_RESIZE = auto()
    WINDOW_CLOSE = auto()


class InputState(Enum):
    IDLE = auto()
    ACTIVE = auto()
    SUSPENDED = auto()


class KeyEventType(Enum):
    KEYDOWN = auto()
    KEYUP = auto()


class MouseEventType(Enum):
    BUTTON_DOWN = auto()
    BUTTON_UP = auto()
    MOVE = auto()
    SCROLL_UP = auto()
    SCROLL_DOWN = auto()


class FrameState(Enum):
    PENDING = auto()
    RENDERING = auto()
    READY = auto()
    PRESENTED = auto()
    DROPPED = auto()


class PipelineStage(Enum):
    IDLE = auto()
    LAYOUT = auto()
    RENDER = auto()
    COMPOSE = auto()
    PRESENT = auto()
    ERROR = auto()


class SignalType(Enum):
    RENDER_START = auto()
    RENDER_COMPLETE = auto()
    RENDER_ERROR = auto()
    FRAME_DROPPED = auto()
    LAYOUT_START = auto()
    LAYOUT_COMPLETE = auto()
    COMPOSE_START = auto()
    COMPOSE_COMPLETE = auto()
    PERFORMANCE_WARNING = auto()
    CAPABILITY_CHECK = auto()


class PatchType(Enum):
    ADD_NODE = "add_node"
    REMOVE_NODE = "remove_node"
    UPDATE_PROPS = "update_props"
    REPLACE_ROOT = "replace_root"
    MOVE_NODE = "move_node"


class BackendTarget(str, Enum):
    CLI = "cli"
    TTY = "tty"
    GUI = "gui"

    def default_capabilities(self) -> dict[str, object]:
        if self is BackendTarget.CLI:
            return {"color_depth": 16, "unicode": True, "animations": False, "hardware_accelerated": False}
        if self is BackendTarget.TTY:
            return {"color_depth": 256, "unicode": True, "animations": False, "hardware_accelerated": False}
        if self is BackendTarget.GUI:
            return {"color_depth": 16_777_216, "unicode": True, "animations": True, "hardware_accelerated": True}
        return {"color_depth": 16_777_216, "unicode": True, "animations": True, "hardware_accelerated": True}


class TerminalCapability(Enum):
    ANSI_COLORS = "ansi_colors"
    ANSI_CURSOR = "ansi_cursor"
    ANSI_SCREEN = "ansi_screen"
    TRUE_COLOR = "true_color"
    UNICODE = "unicode"
    ALTERNATE_BUFFER = "alternate_buffer"
    MOUSE_TRACKING = "mouse_tracking"


class TerminalType(Enum):
    GNOME_TERMINAL = "gnome-terminal"
    KONSOLE = "konsole"
    ITERM2 = "iterm2"
    WINDOWS_TERMINAL = "windows-terminal"
    CONHOST = "conhost"
    UNKNOWN = "unknown"


class TerminalMode(Enum):
    NORMAL = "normal"
    RAW = "raw"
    CBREAK = "cbreak"


class SGRCode(IntEnum):
    RESET = 0
    BOLD = 1
    DIM = 2
    ITALIC = 3
    UNDERLINE = 4
    BLINK = 5
    REVERSE = 7
    HIDDEN = 8
    STRIKETHROUGH = 9
    NORMAL_INTENSITY = 22
    NO_ITALIC = 23
    NO_UNDERLINE = 24
    NO_BLINK = 25
    NO_REVERSE = 27
    NO_HIDDEN = 28
    NO_STRIKETHROUGH = 29


class Color8(IntEnum):
    BLACK = 0
    RED = 1
    GREEN = 2
    YELLOW = 3
    BLUE = 4
    MAGENTA = 5
    CYAN = 6
    WHITE = 7


class EraseMode(IntEnum):
    TO_END = 0
    TO_START = 1
    ALL = 2


class EventPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class EventType(Enum):
    KEY_DOWN = "key_down"
    KEY_UP = "key_up"
    MOUSE_DOWN = "mouse_down"
    MOUSE_UP = "mouse_up"
    MOUSE_MOVE = "mouse_move"
    MOUSE_WHEEL = "mouse_wheel"
    WINDOW_RESIZE = "window_resize"
    WINDOW_CLOSE = "window_close"
    WINDOW_FOCUS = "window_focus"
    WINDOW_BLUR = "window_blur"
    WINDOW_MOVE = "window_move"
    COMPONENT_MOUNT = "component_mount"
    COMPONENT_UNMOUNT = "component_unmount"
    COMPONENT_UPDATE = "component_update"
    COMPONENT_FOCUS = "component_focus"
    COMPONENT_BLUR = "component_blur"
    COMPONENT_EVENT = "component_event"
    TICK = "tick"
    RENDER_FRAME = "render_frame"
    LAYOUT_INVALIDATED = "layout_invalidated"
    STYLE_INVALIDATED = "style_invalidated"
    ANIMATION_START = "animation_start"
    ANIMATION_END = "animation_end"
    ANIMATION_FRAME = "animation_frame"
    PARTICLE_SYSTEM_START = "particle_system_start"
    PARTICLE_SYSTEM_END = "particle_system_end"
    BATCHED_EVENT = "batched_event"


class ComponentKind(str, Enum):
    GENERIC = "generic"
    BUTTON = "button"
    TEXT = "text"
    INPUT = "input"
    TABLE = "table"
    CONTAINER = "container"
    MEDIA = "media"
    DECORATION = "decoration"


class InteractionType(str, Enum):
    CLICK = "click"
    PRESS = "press"
    SUBMIT = "submit"
    CHANGE = "change"
    FOCUS = "focus"
    BLUR = "blur"
    HOVER = "hover"
    SCROLL = "scroll"
    SELECT = "select"
    ACTIVATE = "activate"


class Alignment(str, Enum):
    START = "start"
    CENTER = "center"
    END = "end"
    STRETCH = "stretch"
    SPACE_BETWEEN = "space_between"
    SPACE_AROUND = "space_around"


class AssetType(str, Enum):
    TEXTURE = "texture"
    FONT = "font"
    BUFFER = "buffer"
    SHADER = "shader"
    GENERIC = "generic"


class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ShaderStage(Enum):
    VERTEX = "vertex"
    FRAGMENT = "fragment"
    COMPUTE = "compute"
    GEOMETRY = "geometry"
    MESH = "mesh"
    TASK = "task"
    TESSELLATION_CONTROL = "tessellation_control"
    TESSELLATION_EVALUATION = "tessellation_evaluation"
    RAY_GENERATION = "ray_generation"
    RAY_MISS = "ray_miss"
    RAY_CLOSEST_HIT = "ray_closest_hit"


class CompilationStatus(Enum):
    PENDING = "pending"
    COMPILED = "compiled"
    FAILED = "failed"
    DEPRECATED = "deprecated"


class ShaderBackendType(str, Enum):
    DIRECTX11 = "directx11"
    DIRECTX12 = "directx12"
    OPENGL = "opengl"
    CPU_FALLBACK = "cpu_fallback"

__all__ = [
    "AnimationEventType",
    "AnimationDirection",
    "BufferUsage",
    "RendererType",
    "BlendMode",
    "BlendFactor",
    "BlendOperation",
    "DepthFunction",
    "CullMode",
    "FillMode",
    "ResidencyState",
    "TransferDirection",
    "BarrierType",
    "SyncType",
    "FilterMode",
    "WrapMode",
    "CubeMapFace",
    "TextureFormat",
    "TextureUsage",
    "InputEventType",
    "InputState",
    "KeyEventType",
    "MouseEventType",
    "FrameState",
    "PipelineStage",
    "SignalType",
    "PatchType",
    "BackendTarget",
    "TerminalCapability",
    "TerminalType",
    "TerminalMode",
    "SGRCode",
    "Color8",
    "EraseMode",
    "EventPriority",
    "EventType",
    "ComponentKind",
    "InteractionType",
    "Alignment",
    "AssetType",
    "LogLevel",
    "ShaderStage",
    "CompilationStatus",
    "ShaderBackendType",
]