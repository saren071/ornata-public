"""Windows platform window implementation using Win32 API.

Provides window creation and management using the Windows API,
with integrated GPU context creation and rendering support.
"""

from __future__ import annotations

import ctypes
import threading
import time
from typing import TYPE_CHECKING

from ornata.api.exports.gpu import PlatformWindow
from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.definitions import GuiNode, WindowPumpHandle
    from ornata.api.exports.gpu import GPUContext
    from ornata.api.exports.interop import HWND

logger = get_logger(__name__)


class Win32Window(PlatformWindow):
    """Windows platform window implementation."""

    _class_registered = False
    _class_lock = threading.Lock()

    def __init__(self, title: str, width: int, height: int) -> None:
        super().__init__(title, width, height)
        self._gpu_context: GPUContext | None = None
        self._pump_handle: WindowPumpHandle | None = None
        self._running = False
        self._root_node: GuiNode | None = None

        try:
            self._initialize()
        except Exception as e:
            logger.error(f"Failed to create Win32 window: {e}")
            self._cleanup()
            from ornata.api.exports.definitions import WindowCreationError
            raise WindowCreationError(f"Window creation failed: {e}") from e

    @property
    def root_node(self) -> GuiNode | None:
        return self._root_node

    @root_node.setter
    def root_node(self, value: GuiNode | None) -> None:
        self._root_node = value

    def start(self) -> WindowPumpHandle:
        """Mark the window as running and return the pump handle."""
        from ornata.api.exports.definitions import WindowPumpHandle
        if self._running and self._pump_handle:
            return self._pump_handle

        self._running = True
        self._pump_handle = WindowPumpHandle(thread=threading.current_thread())
        return self._pump_handle

    def _initialize(self) -> None:
        """Initialize the Windows window."""
        from ornata.api.exports.definitions import CW_USEDEFAULT, WINDOW_CLASS_NAME, WS_OVERLAPPEDWINDOW, WS_VISIBLE
        from ornata.api.exports.interop import GetModuleHandleW, user32
        
        if not user32:
            from ornata.api.exports.definitions import WindowCreationError
            raise WindowCreationError("user32.dll is unavailable on this platform")

        self._register_window_class()

        get_module_handle = GetModuleHandleW
        create_window = user32.CreateWindowExW
        if get_module_handle is None or create_window is None:
            from ornata.api.exports.definitions import WindowCreationError
            raise WindowCreationError("Required Win32 window functions are unavailable")

        hinstance = get_module_handle(None)
        self._hwnd = create_window(
            0,
            WINDOW_CLASS_NAME,
            self.title,
            WS_OVERLAPPEDWINDOW | WS_VISIBLE,
            CW_USEDEFAULT,
            CW_USEDEFAULT,
            self.width,
            self.height,
            None,
            None,
            hinstance,
            None
        )

        if not self._hwnd:
            from ornata.api.exports.definitions import WindowCreationError
            raise WindowCreationError("CreateWindowExW failed")

        self._native_handle = self._hwnd
        logger.debug(f"Created Win32 window: {self._hwnd}")

    def pump(self) -> None:
        """Run the window message pump."""
        from ornata.api.exports.interop import ctwt, user32
        msg = ctwt.MSG()
        peek = user32.PeekMessageW
        translate = user32.TranslateMessage
        dispatch = user32.DispatchMessageW
        if peek is None or translate is None or dispatch is None:
            return

        while self._running:
            if peek(ctypes.byref(msg), None, 0, 0, 1):
                translate(ctypes.byref(msg))
                dispatch(ctypes.byref(msg))
            else:
                # Idle processing: present if context exists
                ctx = self._gpu_context
                if ctx is not None and getattr(ctx, "_initialized", False):
                    present = getattr(ctx, "present", None)
                    if callable(present):
                        present()
                time.sleep(0.001)

    def poll(self) -> None:
        """Drain any pending Windows messages on the calling thread."""
        from ornata.api.exports.interop import ctwt, user32
        if not self._running:
            return
        
        msg = ctwt.MSG()
        peek = user32.PeekMessageW
        translate = user32.TranslateMessage
        dispatch = user32.DispatchMessageW
        if peek is None or translate is None or dispatch is None:
            return

        while self._running and peek(ctypes.byref(msg), None, 0, 0, 1):
            translate(ctypes.byref(msg))
            dispatch(ctypes.byref(msg))

    def _register_window_class(self) -> None:
        """Register the window class."""
        from ornata.api.exports.definitions import WINDOW_CLASS_NAME
        from ornata.api.exports.interop import user32
        
        with self._class_lock:
            if self._class_registered:
                return

            register_class = user32.RegisterClassW
            if register_class is None:
                from ornata.api.exports.definitions import WindowCreationError
                raise WindowCreationError("RegisterClassW is unavailable")

            def wnd_proc(hwnd: HWND, msg: int, wparam: int, lparam: int) -> int:
                from ornata.api.exports.definitions import WM_CLOSE, WM_DESTROY, WM_SIZE
                from ornata.interop.ctypes_compilation.windows import PostQuitMessage
                
                if msg == WM_DESTROY:
                    self._running = False
                    if PostQuitMessage is not None:
                        PostQuitMessage(0)
                    return 0
                elif msg == WM_CLOSE:
                    self.close()
                    return 0
                elif msg == WM_SIZE:
                    width = lparam & 0xFFFF
                    height = (lparam >> 16) & 0xFFFF
                    self.resize(int(width), int(height))
                    return 0

                def_proc = user32.DefWindowProcW
                if def_proc is None:
                    return 0
                return def_proc(hwnd, msg, wparam, lparam)

            wndclass = user32.WNDCLASS()
            wndclass.style = 0
            self._wnd_proc_cb = user32.WNDPROC(wnd_proc)
            wndclass.lpfnWndProc = self._wnd_proc_cb
            wndclass.cbClsExtra = 0
            wndclass.cbWndExtra = 0
            wndclass.hInstance = None
            wndclass.hIcon = None
            wndclass.hCursor = None
            wndclass.hbrBackground = None
            wndclass.lpszMenuName = None
            wndclass.lpszClassName = WINDOW_CLASS_NAME

            if not user32.RegisterClassW(ctypes.byref(wndclass)):
                from ornata.api.exports.definitions import WindowCreationError
                raise WindowCreationError("RegisterClassW failed")

            self._class_registered = True

    @property
    def handle(self) -> HWND | None:
        return self._native_handle

    def show(self) -> None:
        from ornata.api.exports.interop import user32
        handle = self._native_handle
        if handle:
            show_window = user32.ShowWindow
            if show_window is None:
                return
            show_window(handle, 5)

    def hide(self) -> None:
        from ornata.api.exports.interop import user32
        handle = self._native_handle
        if handle:
            show_window = user32.ShowWindow
            if show_window is None:
                return
            show_window(handle, 0)

    def close(self) -> None:
        from ornata.api.exports.interop import user32
        self._running = False
        handle = self._native_handle
        if handle:
            destroy_window = user32.DestroyWindow
            if destroy_window is not None:
                destroy_window(handle)
            self._native_handle = None

    def set_title(self, title: str) -> None:
        from ornata.api.exports.interop import user32
        self.title = title
        handle = self._native_handle
        if handle:
            set_window_text = user32.SetWindowTextW
            if set_window_text is None:
                return
            set_window_text(handle, title)

    def resize(self, width: int, height: int) -> None:
        if width < 1 or height < 1:
            return
        self.width = width
        self.height = height
        ctx = self._gpu_context
        if ctx is not None:
            resize_method = getattr(ctx, "resize", None)
            if callable(resize_method):
                resize_method(width, height)

    def get_gpu_context(self) -> GPUContext | None:
        return self._gpu_context

    def create_gpu_context(self, backend: str = "auto") -> GPUContext:
        from ornata.rendering.backends.gui.contexts.gpu_integration import GPUIntegratedRenderContext
        
        try:
            self._gpu_context = GPUIntegratedRenderContext(self)
            self._gpu_context.initialize()
            
            # Initial clear
            try:
                from ornata.api.exports.definitions import Color
                self._gpu_context.clear(Color(0, 0, 0, 255))
                self._gpu_context.present()
            except Exception:
                pass
                
            return self._gpu_context
        except Exception as e:
            logger.error(f"Failed to create GPU context: {e}")
            from ornata.api.exports.definitions import GPUBackendNotAvailableError
            raise GPUBackendNotAvailableError(f"GPU integration failed: {e}") from e

    def render_gui_node(self, node: GuiNode) -> None:
        """Render a GUI node tree to the window."""
        from ornata.api.exports.gpu import Canvas
        from ornata.rendering.backends.gui.renderer import render_tree
        
        if not node or not self._gpu_context:
            return
            
        try:
            # Use the centralized renderer logic
            canvas = Canvas(self._gpu_context, self.width, self.height)
            self._root_node = node
            
            # Delegate to the renderer module which handles the registry and drawing
            render_tree(canvas, node)
            
            self._gpu_context.present()
        except Exception as e:
            logger.error(f"Failed to render GUI node: {e}")

    def _cleanup(self) -> None:
        self._running = False
        ctx = self._gpu_context
        if ctx is not None:
            cleanup_method = getattr(ctx, "cleanup", None)
            if callable(cleanup_method):
                cleanup_method()
            self._gpu_context = None

    def __del__(self) -> None:
        self._cleanup()


def is_available() -> bool:
    from ornata.api.exports.interop import user32
    # Use getattr to avoid relying on optionality in type stubs.
    return bool(getattr(user32, "RegisterClassW", None) and getattr(user32, "CreateWindowExW", None))