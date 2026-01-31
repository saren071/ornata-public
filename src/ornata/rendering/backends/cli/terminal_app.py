"""Terminal live app loop supporting input and ticking.

This is a minimal adapter that keeps the same public shape while removing
hard dependencies on a separate mouse module.
"""

from __future__ import annotations

import atexit
import os
import sys
import time as _t
from typing import TYPE_CHECKING, TextIO

from ornata.api.exports.definitions import BackendTarget, Event, EventType, KeyEvent, KeyEventType, QuitEvent, TickEvent
from ornata.api.exports.events import EventBus
from ornata.api.exports.interop import kernel32
from ornata.api.exports.utils import get_logger
from ornata.rendering.backends.cli.input import read_key
from ornata.rendering.backends.cli.session import LiveSessionRenderer

if TYPE_CHECKING:
    from collections.abc import Callable


def enable_mouse_reporting() -> str:
    return "\x1b[?1000;1002;1006;1004h"


def disable_mouse_reporting() -> str:
    return "\x1b[?1000;1002;1006;1004l"


def hide_cursor() -> str:
    return "\x1b[?25l"


def show_cursor() -> str:
    return "\x1b[?25h"


def enter_alternate_buffer() -> str:
    return "\x1b[?1049h"


def exit_alternate_buffer() -> str:
    return "\x1b[?1049l"


def _emergency_cleanup() -> None:
    """Emergency cleanup function registered with atexit."""
    try:
        # Print directly to stdout in case stream is closed
        sys.stdout.write(disable_mouse_reporting() + show_cursor() + exit_alternate_buffer())
        sys.stdout.flush()
    except Exception:
        pass


class CLIInputManager:
    """Manages input focus and routes keyboard input to focused components."""

    def __init__(self, event_bus: EventBus) -> None:
        """Initialize the input manager.

        Parameters
        ----------
        event_bus : EventBus
            Event bus for subscribing to key events.
        """
        self._bus = event_bus
        self._focused_component: str | None = None
        self._component_values: dict[str, str] = {}
        self._logger = get_logger(__name__ + ".input_manager")
        self._sub_token: object | None = None

    def attach(self) -> None:
        """Subscribe to key events."""
        self._sub_token = self._bus.subscribe(EventType.KEY_DOWN.value, self._on_key_event)
        self._logger.debug("input_manager: attached to event bus")

    def detach(self) -> None:
        """Unsubscribe from key events."""
        if self._sub_token is not None:
            try:
                if callable(self._sub_token):
                    self._sub_token()
            except Exception:
                pass
            self._sub_token = None
        self._logger.debug("input_manager: detached from event bus")

    def focus(self, component_id: str | None) -> None:
        """Set focus to a component.

        Parameters
        ----------
        component_id : str | None
            Component ID to focus, or None to clear focus.
        """
        if self._focused_component != component_id:
            self._logger.debug("input_manager: focus changed from %r to %r", self._focused_component, component_id)
            self._focused_component = component_id

    def get_value(self, component_id: str) -> str:
        """Get current input value for a component.

        Parameters
        ----------
        component_id : str
            Component ID.

        Returns
        -------
        str
            Current input value.
        """
        return self._component_values.get(component_id, "")

    def _on_key_event(self, evt: Event) -> None:
        """Handle key down events.

        Parameters
        ----------
        evt : Event
            Key event.
        """
        if self._focused_component is None:
            return

        try:
            payload = evt.data
            if not isinstance(payload, KeyEvent):
                return

            key = payload.key
            current_value = self._component_values.get(self._focused_component, "")

            # Handle special keys
            if key == "enter":
                self._logger.debug("input_manager: submit on %s", self._focused_component)
                # Emit submit event
                self._emit_submit(current_value)
            elif key == "backspace":
                if current_value:
                    new_value = current_value[:-1]
                    self._component_values[self._focused_component] = new_value
                    self._logger.debug("input_manager: backspace on %s, value=%r", self._focused_component, new_value)
                    self._emit_change(new_value)
            elif key == "escape":
                # Clear focus on escape
                self._logger.debug("input_manager: escape pressed, clearing focus")
                self.focus(None)
            elif key == "mouse":
                # Ignore mouse events in input manager
                pass
            elif len(key) == 1 and key.isprintable():
                # Regular character input
                new_value = current_value + key
                self._component_values[self._focused_component] = new_value
                self._logger.debug("input_manager: char input on %s, value=%r", self._focused_component, new_value)
                self._emit_change(new_value)

        except Exception as exc:
            self._logger.debug("input_manager: error handling key event: %s", exc)

    def _emit_change(self, value: str) -> None:
        """Emit change event to the focused component.

        Parameters
        ----------
        value : str
            New input value.
        """
        from ornata.definitions.dataclasses.events import ComponentEvent

        event = ComponentEvent(
            name="change",
            component_id=self._focused_component,
            payload=value,
            timestamp=_t.perf_counter(),
        )
        # Publish to bus for component to receive
        self._bus.publish(Event(
            type=EventType.COMPONENT_EVENT,
            data=event,
        ))

    def _emit_submit(self, value: str) -> None:
        """Emit submit event to the focused component.

        Parameters
        ----------
        value : str
            Current input value.
        """
        from ornata.definitions.dataclasses.events import ComponentEvent

        event = ComponentEvent(
            name="submit",
            component_id=self._focused_component,
            payload=value,
            timestamp=_t.perf_counter(),
        )
        self._bus.publish(Event(
            type=EventType.COMPONENT_EVENT,
            data=event,
        ))
        # Clear value after submit
        if self._focused_component is not None:
            self._component_values[self._focused_component] = ""


def _enable_vt_mode(stream: TextIO, logger) -> None:
    """Enable Windows VT processing/input when possible."""

    if os.name != "nt":
        logger.debug("terminal_session: VT mode not required on %s", os.name)
        return

    if kernel32.GetStdHandle is None or kernel32.GetConsoleMode is None or kernel32.SetConsoleMode is None:
        logger.warning("terminal_session: kernel32 console bindings unavailable")
        return

    handles = {
        "out": kernel32.GetStdHandle(kernel32.STD_OUTPUT_HANDLE),
        "in": kernel32.GetStdHandle(kernel32.STD_INPUT_HANDLE),
    }
    for name, handle in handles.items():
        if handle in (0, None, kernel32.INVALID_HANDLE_VALUE):
            logger.debug("terminal_session: no handle for %s stream", name)
            continue
        mode_value = kernel32.get_console_mode(handle)
        if mode_value is None:
            logger.debug("terminal_session: GetConsoleMode failed for %s", name)
            continue
        target_bits = 0x0004 if name == "out" else 0x0200
        if mode_value & target_bits:
            logger.debug("terminal_session: VT flags already set for %s (mode=%#x)", name, mode_value)
            continue
        new_mode = mode_value | target_bits
        if kernel32.set_console_mode(handle, new_mode):
            logger.debug(
                "terminal_session: enabled VT for %s (mode=%#x -> %#x)", name, mode_value, new_mode
            )
        else:
            logger.debug("terminal_session: failed to set VT mode for %s (mode=%#x)", name, mode_value)


class TerminalSession(LiveSessionRenderer):
    """Extended live session with input-driven app loop support."""

    def __init__(self, stream: TextIO) -> None:
        super().__init__(BackendTarget.CLI)
        self._bus = EventBus()
        self._running = False
        self._stream = stream
        self._logger = get_logger(__name__)
        self._input_manager = CLIInputManager(self._bus)

    @property
    def events(self) -> EventBus:
        """Access the event bus for subscribing to input and timer events."""
        return self._bus

    @property
    def input_manager(self) -> CLIInputManager:
        """Access the input manager for focus and text input."""
        return self._input_manager

    def run(self, app: TerminalApp, *, fps: float = 30.0) -> None:
        """Run the application in a live terminal session with input handling."""
        self._logger.debug("terminal_session: running app %r", app)
        self._running = True
        app.attach(self._bus)
        self._input_manager.attach()
        frame: str = app.render()
        _enable_vt_mode(self._stream, self._logger)
        self._logger.debug("terminal_session: VT mode setup complete")
        # Enable mouse reporting in terminal
        try:
            self._logger.debug("terminal_session: about to enter alternate buffer")
            self._stream.write(
                enter_alternate_buffer() + hide_cursor() + enable_mouse_reporting() + frame
            )
            self._stream.flush()
            self._logger.debug(
                "terminal_session: sent enable_mouse_reporting (frame=%d chars)",
                len(frame),
            )
            # Register emergency cleanup in case of abnormal exit
            atexit.register(_emergency_cleanup)
        except Exception as exc:
            self._logger.error("terminal_session: exception in setup: %s", exc)
            self._stream.write(frame)
        self._logger.debug("terminal_session: setup complete, preparing loop")

        interval = 1.0 / max(1e-6, fps)
        last = _t.perf_counter()
        idle_cycles = 0
        loop_count = 0
        self._logger.debug("terminal_session: entering main loop (running=%s, should_quit=%s)", self._running, app.should_quit)
        import sys
        sys.stdout.flush()
        sys.stderr.flush()
        # Wait for terminal to settle after mode changes, then drain any spurious input
        _t.sleep(0.1)
        for _ in range(10):
            if not read_key(timeout=0.01):
                break
        while self._running and not app.should_quit:
            try:
                loop_count += 1
                if loop_count == 1:
                    self._logger.debug("terminal_session: first loop iteration")
                now = _t.perf_counter()
                dt = now - last
                last = now
                key = read_key(timeout=0.0)
                if key:
                    idle_cycles = 0
                    self._logger.debug("terminal_session: read key %r", key)
                    self._bus.publish(
                        Event(
                            type=EventType.KEY_DOWN,
                            data=KeyEvent(event_type=KeyEventType.KEYDOWN, key=key),
                        )
                    )
                else:
                    idle_cycles += 1
                    if idle_cycles >= int(fps):  # log once per second of idle time
                        self._logger.debug("terminal_session: no input detected for %.1fs", idle_cycles / fps)
                        idle_cycles = 0
                # Tick after input so values can be updated before render
                self._bus.publish(Event(type=EventType.TICK, data=TickEvent(dt=dt)))
                new_frame = app.render()
                if new_frame != frame:
                    frame = new_frame
                    self._logger.debug("terminal_session: new frame rendered (len=%d)", len(new_frame))
                    self._stream.write(frame)
                sleep_for = interval - (_t.perf_counter() - now)
                if sleep_for > 0:
                    _t.sleep(sleep_for)
            except Exception as exc:
                self._logger.error("terminal_session: error in main loop: %s", exc, exc_info=True)
                raise
        # Cleanup after loop exits
        self._logger.debug("terminal_session: exited main loop after %d iterations (running=%s, should_quit=%s)", loop_count, self._running, app.should_quit)
        self._logger.debug("terminal_session: starting cleanup")
        self._bus.publish(Event(type=EventType.WINDOW_CLOSE, data=QuitEvent()))
        app.detach()
        # Disable mouse reporting
        try:
            self._stream.write(disable_mouse_reporting() + show_cursor() + exit_alternate_buffer())
            self._stream.flush()
            self._logger.debug("terminal_session: sent disable_mouse_reporting")
        except Exception as exc:
            self._logger.debug("terminal_session: cleanup exception: %s", exc)
        # Unregister emergency cleanup since we did normal cleanup
        try:
            atexit.unregister(_emergency_cleanup)
        except Exception:
            pass
        self._logger.debug("terminal_session: cleanup complete")

    def stop(self) -> None:
        """Stop the running session loop."""
        self._logger.debug("terminal_session: stop() called")
        self._running = False


class TerminalApp:
    """Base class for custom terminal applications."""

    def __init__(self) -> None:
        self._bus: EventBus | None = None
        self.should_quit: bool = False
        self._subs: list[Callable[[], None]] = []

    def attach(self, bus: EventBus) -> None:
        """Attach the app to an event bus."""
        self._bus = bus
        self._subs.append(bus.subscribe(EventType.KEY_DOWN.value, self._on_key_event))
        self._subs.append(bus.subscribe(EventType.TICK.value, self._on_tick_event))
        self._subs.append(bus.subscribe(EventType.WINDOW_CLOSE.value, self._on_quit_event))

    def detach(self) -> None:
        """Detach the app and unsubscribe from events."""
        for unsub in self._subs:
            try:
                unsub()
            except Exception:
                pass
        self._subs.clear()
        self._bus = None

    def _on_key_event(self, evt: Event) -> None:
        try:
            payload = evt.data
            if isinstance(payload, KeyEvent):
                self.on_key(payload.key)
        except Exception:  #
            pass

    def _on_tick_event(self, evt: Event) -> None:
        try:
            payload = evt.data
            if isinstance(payload, TickEvent):
                self.on_tick(payload.dt)
        except Exception:
            pass

    def _on_quit_event(self, evt: Event) -> None:
        try:
            if isinstance(evt.data, QuitEvent) or evt.type is EventType.WINDOW_CLOSE:
                self.should_quit = True
        except Exception:
            pass

    def on_key(self, key: str) -> None:
        """Handle quit gestures."""
        if key and key.lower() in {"q", "escape", "ctrl+c"}:
            self.should_quit = True
        # Ignore mouse events for quit purposes
        if key == "mouse":
            pass

    def on_tick(self, dt: float) -> None:
        _ = dt

    def render(self) -> str:
        return ""
