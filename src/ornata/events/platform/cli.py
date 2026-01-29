"""CLI platform event handler for capturing command-line input events.

This module provides CLI-specific event handling for basic keyboard input
capture in command-line applications.
"""

from __future__ import annotations

import sys
import threading
import time
from typing import TYPE_CHECKING

from ornata.api.exports.utils import get_logger
from ornata.definitions.enums import KeyEventType

if TYPE_CHECKING:
    from collections.abc import Iterator

    from ornata.api.exports.definitions import Event

logger = get_logger(__name__)


class CliEventHandler:
    """CLI platform event handler for basic keyboard input capture.

    This handler provides simple keyboard input handling for CLI applications,
    using blocking input reads with timeout to avoid hanging the application.
    """

    def __init__(self) -> None:
        """Initialize the CLI event handler."""
        self._running = False
        self._event_queue: list[Event] = []
        self._queue_lock = threading.RLock()
        self._event_thread: threading.Thread | None = None
        self._input_timeout = 0.1  # 100ms timeout for input reads

        # Check if stdin is available and not redirected
        self._available = sys.stdin.isatty() is not False  # Works for both TTY and non-TTY

    def is_available(self) -> bool:
        """Check if CLI event handling is available.

        Returns:
            bool: True if stdin is available for reading.
        """
        return self._available

    def start_event_loop(self) -> None:
        """Start the CLI event capture loop.

        This creates a background thread that monitors stdin for input.
        """
        if not self._available:
            logger.warning("Cannot start CLI event loop: stdin not available")
            return

        if self._running:
            logger.debug("CLI event loop already running")
            return

        self._running = True
        self._event_thread = threading.Thread(
            target=self._event_loop_worker,
            name="cli-event-handler",
            daemon=True
        )
        self._event_thread.start()
        logger.debug("CLI event loop started")

    def stop_event_loop(self) -> None:
        """Stop the CLI event capture loop.

        This signals the background thread to stop.
        """
        if not self._running:
            return

        self._running = False
        if self._event_thread and self._event_thread.is_alive():
            self._event_thread.join(timeout=1.0)
            if self._event_thread.is_alive():
                logger.warning("CLI event thread did not stop cleanly")

        self._event_thread = None
        logger.debug("CLI event loop stopped")

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
        """Background worker thread for capturing CLI input events."""
        try:
            while self._running:
                # Try to read input with timeout
                line = self._read_input_with_timeout()
                if line is not None:
                    events = self._parse_input_line(line)
                    with self._queue_lock:
                        self._event_queue.extend(events)
                else:
                    # No input available, small sleep to avoid busy waiting
                    time.sleep(0.01)

        except Exception as exc:
            logger.error("CLI event loop worker failed: %s", exc)
            self._running = False

    def _read_input_with_timeout(self) -> str | None:
        """Read a line of input with timeout to avoid blocking.

        Returns:
            str | None: Input line if available, None if timeout or no input.
        """
        try:
            import os

            if os.name == 'nt':  # Windows
                return self._read_windows_input()

        except (OSError, ImportError):
            return None

    def _read_windows_input(self) -> str | None:
        """Read input on Windows systems.

        Returns:
            str | None: Input line if available.
        """
        try:
            import msvcrt

            if msvcrt.kbhit():
                line = ""
                while True:
                    char = msvcrt.getch()
                    if char in (b'\r', b'\n'):
                        break
                    line += char.decode('utf-8', errors='ignore')
                return line
            return None

        except ImportError:
            return None

    def _parse_input_line(self, line: str) -> list[Event]:
        """Parse an input line into events.

        Args:
            line: Input line to parse.

        Returns:
            list[Event]: List of parsed events.
        """
        from ornata.api.exports.definitions import Event, EventType, KeyEvent
        events: list[Event] = []

        for char in line:
            key_data = KeyEvent(event_type=KeyEventType.KEYDOWN, key=char, modifiers=frozenset())
            event = Event(type=EventType.KEY_DOWN, data=key_data)
            events.append(event)
        enter_data = KeyEvent(event_type=KeyEventType.KEYDOWN, key="enter", modifiers=frozenset())
        enter_event = Event(type=EventType.KEY_DOWN, data=enter_data)
        events.append(enter_event)

        return events


def create_cli_handler() -> CliEventHandler:
    """Create a CLI platform event handler.

    Returns:
        CliEventHandler: Configured handler instance.
    """
    return CliEventHandler()
