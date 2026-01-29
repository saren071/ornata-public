"""Windows platform event handler for capturing system input events.

This module provides Windows-specific event handling using ctypes to interface
with the Windows API for keyboard and mouse input capture.
"""

from __future__ import annotations

import ctypes
import threading
import time
from ctypes import wintypes
from typing import TYPE_CHECKING

from ornata.api.exports.definitions import HWND_MESSAGE, VK_CONTROL, VK_MENU, VK_SHIFT
from ornata.api.exports.utils import get_logger
from ornata.definitions.enums import KeyEventType, MouseEventType
from ornata.interop.ctypes_compilation.windows.kernel32 import GetModuleHandleW
from ornata.interop.ctypes_compilation.windows.user32 import (
    WNDCLASS,
    WNDPROC,
    CreateWindowExW,
    DefWindowProcW,
    DestroyWindow,
    DispatchMessageW,
    GetAsyncKeyState,
    PeekMessageW,
    RegisterClassW,
    TranslateMessage,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from ornata.api.exports.definitions import Event, EventType

logger = get_logger(__name__)


class WindowsEventHandler:
    """Windows platform event handler using Win32 API for input capture.

    This handler captures keyboard and mouse events from the Windows message queue
    and translates them into Ornata Event objects.
    """

    def __init__(self) -> None:
        """Initialize the Windows event handler."""
        self._running = False
        self._event_queue: list[Event] = []
        self._queue_lock = threading.RLock()
        self._event_thread: threading.Thread | None = None
        self._last_mouse_x = 0
        self._last_mouse_y = 0

        if (
            RegisterClassW is None
            or CreateWindowExW is None
            or DestroyWindow is None
            or DispatchMessageW is None
            or PeekMessageW is None
            or TranslateMessage is None
            or GetAsyncKeyState is None
            or DefWindowProcW is None
        ):
            logger.warning("Windows API not available: required Win32 bindings missing")
            self._available = False
            return

        self._available = True
        self._register_class = RegisterClassW
        self._create_window = CreateWindowExW
        self._destroy_window = DestroyWindow
        self._dispatch_message = DispatchMessageW
        self._peek_message = PeekMessageW
        self._translate_message = TranslateMessage
        self._get_async_key_state = GetAsyncKeyState
        self._def_window_proc = DefWindowProcW
        self._get_module_handle = GetModuleHandleW
        self._wnd_proc_callback = WNDPROC(self._build_window_proc())

    def is_available(self) -> bool:
        """Check if Windows event handling is available on this system.

        Returns:
            bool: True if Windows APIs are available and accessible.
        """
        return self._available

    def start_event_loop(self) -> None:
        """Start the Windows event capture loop.

        This creates a background thread that monitors Windows messages
        and translates them into Ornata events.
        """
        if not self._available:
            logger.warning("Cannot start Windows event loop: APIs not available")
            return

        if self._running:
            logger.debug("Windows event loop already running")
            return

        self._running = True
        self._event_thread = threading.Thread(
            target=self._event_loop_worker,
            name="windows-event-handler",
            daemon=True
        )
        self._event_thread.start()
        logger.debug("Windows event loop started")

    def stop_event_loop(self) -> None:
        """Stop the Windows event capture loop.

        This signals the background thread to stop and waits for it to complete.
        """
        if not self._running:
            return

        self._running = False
        if self._event_thread and self._event_thread.is_alive():
            self._event_thread.join(timeout=1.0)
            if self._event_thread.is_alive():
                logger.warning("Windows event thread did not stop cleanly")

        self._event_thread = None
        logger.debug("Windows event loop stopped")

    def poll_events(self) -> Iterator[Event]:
        """Poll for captured events.

        Returns:
            Iterator[Event]: Iterator over available events.
        """
        with self._queue_lock:
            events = list(self._event_queue)
            self._event_queue.clear()

        yield from events

    def _event_loop_worker(self) -> None:
        """Background worker thread for capturing Windows events."""
        try:
            # Create a message-only window for capturing global events
            hwnd = self._create_message_window()
            if hwnd == 0:
                logger.error("Failed to create Windows message window")
                return

            msg = wintypes.MSG()
            while self._running:
                # Process pending messages
                while self._peek_message(ctypes.byref(msg), hwnd, 0, 0, 1):  # PM_REMOVE = 1
                    self._translate_message(ctypes.byref(msg))
                    self._dispatch_message(ctypes.byref(msg))

                    # Convert Windows message to Ornata event
                    event = self._convert_message_to_event(msg)
                    if event:
                        with self._queue_lock:
                            self._event_queue.append(event)

                # Small sleep to prevent busy waiting
                time.sleep(0.001)

            # Clean up
            if hwnd:
                self._destroy_window(hwnd)

        except Exception as exc:
            logger.error("Windows event loop worker failed: %s", exc)
            self._running = False

    def _build_window_proc(self) -> Callable[[int, int, int, int], int]:
        """Create the Win32 window procedure for the helper window."""

        def window_proc(hwnd: int, msg: int, wparam: int, lparam: int) -> int:
            return int(self._def_window_proc(hwnd, msg, wparam, lparam))
        logger.debug("Built window proc")
        return window_proc

    def _create_message_window(self) -> int:
        """Create a message-only window for event capture.

        Returns:
            int: Window handle, or 0 on failure.
        """
        # Define window class
        wc = WNDCLASS()
        wc.lpfnWndProc = self._wnd_proc_callback
        wc.hInstance = self._get_module_handle(None)
        class_name = "OrnataEventWindow"
        wc.lpszClassName = class_name

        # Register window class
        if not self._register_class(ctypes.byref(wc)):
            last_error = ctypes.get_last_error()
            if last_error == 1410: # ERROR_CLASS_ALREADY_EXISTS
                logger.debug("Windows window class '%s' already registered", class_name)
            else:
                logger.error("Failed to register Windows window class: %s (error code: %d)", class_name, last_error)
                return 0

        # Create message-only window
        hwnd = self._create_window(
            0,  # dwExStyle
            class_name,  # lpClassName
            None,  # lpWindowName
            0,  # dwStyle
            0, 0, 0, 0,  # x, y, nWidth, nHeight
            HWND_MESSAGE,  # hWndParent (message-only)
            None,  # hMenu
            wc.hInstance,  # hInstance
            None  # lpParam
        )

        if hwnd == 0:
            logger.error("Failed to create Windows message window")
            return 0

        logger.debug("Created Windows message window: %d", hwnd)
        return int(hwnd)

    def _convert_message_to_event(self, msg: wintypes.MSG) -> Event | None:
        """Convert a Windows message to an Ornata Event.

        Args:
            msg: Windows message structure.

        Returns:
            Event | None: Converted event, or None if message should be ignored.
        """
        from ornata.api.exports.definitions import WM_KEYDOWN, WM_KEYUP, WM_LBUTTONDOWN, WM_LBUTTONUP, WM_MOUSEMOVE, WM_MOUSEWHEEL, WM_RBUTTONDOWN, WM_RBUTTONUP, EventType
        modifiers = self._get_current_modifiers()

        if msg.message == WM_KEYDOWN:
            return self._create_key_event(EventType.KEY_DOWN, msg.wParam, modifiers)

        elif msg.message == WM_KEYUP:
            return self._create_key_event(EventType.KEY_UP, msg.wParam, modifiers)

        elif msg.message in (WM_LBUTTONDOWN, WM_RBUTTONDOWN):
            button = "left" if msg.message == WM_LBUTTONDOWN else "right"
            return self._create_mouse_event(EventType.MOUSE_DOWN, msg.lParam, button, modifiers)

        elif msg.message in (WM_LBUTTONUP, WM_RBUTTONUP):
            button = "left" if msg.message == WM_LBUTTONUP else "right"
            return self._create_mouse_event(EventType.MOUSE_UP, msg.lParam, button, modifiers)

        elif msg.message == WM_MOUSEMOVE:
            return self._create_mouse_event(EventType.MOUSE_MOVE, msg.lParam, None, modifiers)

        elif msg.message == WM_MOUSEWHEEL:
            delta = ctypes.c_short(msg.wParam >> 16).value
            return self._create_mouse_wheel_event(msg.lParam, delta, modifiers)

        return None

    def _create_key_event(self, event_type: EventType, vk_code: int, modifiers: set[str]) -> Event:
        from ornata.api.exports.definitions import Event, KeyEvent
        key_name = self._vk_code_to_key_name(vk_code)
        key_data = KeyEvent(
            event_type=KeyEventType.KEYDOWN,
            key=key_name,
            modifiers=frozenset(modifiers),
            repeat=False,
        )
        return Event(type=event_type, data=key_data)

    def _create_mouse_event(self, event_type: EventType, lparam: int, button: str | None, modifiers: set[str]) -> Event:
        from ornata.api.exports.definitions import Event, MouseEvent
        x = ctypes.c_short(lparam & 0xFFFF).value
        y = ctypes.c_short((lparam >> 16) & 0xFFFF).value
        delta_x = x - self._last_mouse_x
        delta_y = y - self._last_mouse_y
        self._last_mouse_x = x
        self._last_mouse_y = y
        button_code: int | None = None
        if button is not None:
            if button == "left":
                button_code = 1
            elif button == "right":
                button_code = 3
        mouse_data = MouseEvent(
            event_type=MouseEventType.BUTTON_DOWN,
            x=x,
            y=y,
            button=button_code,
            button_name=button,
            modifiers=frozenset(modifiers),
            delta_x=delta_x,
            delta_y=delta_y,
        )
        return Event(type=event_type, data=mouse_data)

    def _create_mouse_wheel_event(self, lparam: int, delta: int, modifiers: set[str]) -> Event:
        from ornata.api.exports.definitions import Event, EventType, MouseEvent
        x = ctypes.c_short(lparam & 0xFFFF).value
        y = ctypes.c_short((lparam >> 16) & 0xFFFF).value
        mouse_data = MouseEvent(event_type=MouseEventType.SCROLL_DOWN, x=x, y=y, button=None, modifiers=frozenset(modifiers), delta_x=0, delta_y=delta)
        return Event(type=EventType.MOUSE_WHEEL, data=mouse_data)

    def _get_current_modifiers(self) -> set[str]:
        """Get the current state of modifier keys.

        Returns:
            set[str]: Set of active modifier key names.
        """
        modifiers: set[str] = set()

        if int(self._get_async_key_state(VK_SHIFT)) & 0x8000:
            modifiers.add("shift")
        if int(self._get_async_key_state(VK_CONTROL)) & 0x8000:
            modifiers.add("ctrl")
        if int(self._get_async_key_state(VK_MENU)) & 0x8000:
            modifiers.add("alt")

        return modifiers

    def _vk_code_to_key_name(self, vk_code: int) -> str:
        """Convert Windows virtual key code to key name.

        Args:
            vk_code: Windows virtual key code.

        Returns:
            str: Human-readable key name.
        """
        # Common key mappings
        key_map = {
            0x08: "backspace",
            0x09: "tab",
            0x0D: "enter",
            0x1B: "escape",
            0x20: "space",
            0x21: "page_up",
            0x22: "page_down",
            0x23: "end",
            0x24: "home",
            0x25: "left",
            0x26: "up",
            0x27: "right",
            0x28: "down",
            0x2D: "insert",
            0x2E: "delete",
        }

        # Function keys
        if 0x70 <= vk_code <= 0x87:  # F1-F24
            return f"f{vk_code - 0x6F}"

        # Number keys
        if 0x30 <= vk_code <= 0x39:  # 0-9
            return str(vk_code - 0x30)

        # Letter keys
        if 0x41 <= vk_code <= 0x5A:  # A-Z
            return chr(vk_code).lower()

        return key_map.get(vk_code, f"key_{vk_code}")

def create_windows_handler() -> WindowsEventHandler:
    """Create a Windows platform event handler.

    Returns:
        WindowsEventHandler: Configured handler instance.
    """
    return WindowsEventHandler()
