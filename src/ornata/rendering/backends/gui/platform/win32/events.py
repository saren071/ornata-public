"""Windows input event handling.

Provides input event processing for Windows GUI windows.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.events import EventHandler

logger = get_logger(__name__)


class Win32EventHandler:
    """Windows event handler for GUI input."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = {}
        self._key_queue: list[str] = []

    def add_handler(self, event_type: str, handler: EventHandler) -> None:
        """Add an event handler."""
        self._handlers.setdefault(event_type, []).append(handler)

    def remove_handler(self, event_type: str, handler: EventHandler) -> None:
        """Remove an event handler."""
        if event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] if h != handler
            ]

    def handle_key_event(self, key_code: int, pressed: bool) -> None:
        """Handle a key event."""
        # Convert Windows key code to semantic key
        key_name = self._key_code_to_name(key_code)
        if key_name and pressed:
            self._key_queue.append(key_name)

            # Dispatch to handlers
            self._dispatch_event("key_press", {"key": key_name})

    def handle_mouse_event(self, x: int, y: int, button: int, pressed: bool) -> None:
        """Handle a mouse event."""
        event_type = "mouse_press" if pressed else "mouse_release"
        self._dispatch_event(event_type, {
            "x": x,
            "y": y,
            "button": button
        })

    def get_key_queue(self) -> list[str]:
        """Get pending key events."""
        keys = self._key_queue.copy()
        self._key_queue.clear()
        return keys

    def _dispatch_event(self, event_type: str, event_data: dict[str, Any]) -> None:
        """Dispatch event to handlers."""
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    handler(event_data)
                except Exception as e:
                    logger.error(f"Event handler error: {e}")

    def _key_code_to_name(self, key_code: int) -> str | None:
        """Convert Windows virtual key code to key name."""
        # Common key mappings
        key_map = {
            0x08: "backspace",
            0x09: "tab",
            0x0D: "enter",
            0x1B: "escape",
            0x20: "space",
            0x25: "left",
            0x26: "up",
            0x27: "right",
            0x28: "down",
            0x2D: "insert",
            0x2E: "delete",
            0x30: "0",
            0x31: "1",
            0x32: "2",
            0x33: "3",
            0x34: "4",
            0x35: "5",
            0x36: "6",
            0x37: "7",
            0x38: "8",
            0x39: "9",
            0x41: "a",
            0x42: "b",
            0x43: "c",
            0x44: "d",
            0x45: "e",
            0x46: "f",
            0x47: "g",
            0x48: "h",
            0x49: "i",
            0x4A: "j",
            0x4B: "k",
            0x4C: "l",
            0x4D: "m",
            0x4E: "n",
            0x4F: "o",
            0x50: "p",
            0x51: "q",
            0x52: "r",
            0x53: "s",
            0x54: "t",
            0x55: "u",
            0x56: "v",
            0x57: "w",
            0x58: "x",
            0x59: "y",
            0x5A: "z",
        }

        return key_map.get(key_code)
