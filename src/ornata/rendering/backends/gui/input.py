"""GUI input handling and event processing.

Provides comprehensive input handling for GUI applications including keyboard,
mouse, touch, and window events with platform-specific implementations.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable

    from ornata.api.exports.definitions import EventType, GuiInputEvent, InputContext, InputEventType, InputModifierState, KeyEvent, MouseEvent
    from ornata.api.exports.events import EventBus

logger = get_logger(__name__)


class InputProcessor:
    """GUI input event processor.
    
    Processes and dispatches input events to the event system,
    handling filtering, coalescing, and routing.
    
    Parameters
    ----------
    event_bus : EventBus
        Event bus for dispatching processed events.
    window_id : str
        Associated window identifier.
    
    Returns
    -------
    InputProcessor
        Input processor instance.
    """
    
    def __init__(self, event_bus: EventBus, window_id: str) -> None:
        """Initialize the input processor.
        
        Parameters
        ----------
        event_bus : EventBus
            Event bus for event dispatching.
        window_id : str
            Associated window identifier.
        
        Returns
        -------
        None
        """
        from ornata.api.exports.definitions import InputModifierState, InputState
        self.event_bus = event_bus
        self.window_id = window_id
        self.state = InputState.IDLE
        self._lock = threading.Lock()
        self._modifiers = InputModifierState()
        self._last_mouse_pos = (0, 0)
        self._input_handlers: dict[InputEventType, list[Callable[[GuiInputEvent], None]]] = {}
        self._enabled = True
        
        # Register default handlers
        self._setup_default_handlers()
        
        logger.debug(f"Initialized InputProcessor for window {window_id}")

    def process_event(self, event: GuiInputEvent) -> None:
        """Process a raw input event.
        
        Parameters
        ----------
        event : GuiInputEvent
            Raw input event to process.
        
        Returns
        -------
        None
        """
        from ornata.api.exports.definitions import InputState
        if not self._enabled or not self.state == InputState.ACTIVE:
            return
        
        with self._lock:
            try:
                # Update modifier state
                self._update_modifiers(event)
                
                # Apply filtering and processing
                processed_event = self._filter_event(event)
                if processed_event is None:
                    return
                
                # Dispatch to event system
                self._dispatch_to_event_system(processed_event)
                
                # Call registered handlers
                self._call_handlers(processed_event)
                
            except Exception as e:
                logger.error(f"Failed to process input event: {e}")

    def register_handler(self, event_type: InputEventType, handler: Callable[[GuiInputEvent], None]) -> None:
        """Register an input event handler.
        
        Parameters
        ----------
        event_type : InputEventType
            Type of event to handle.
        handler : Callable[[GuiInputEvent], None]
            Handler function.
        
        Returns
        -------
        None
        """
        if event_type not in self._input_handlers:
            self._input_handlers[event_type] = []
        self._input_handlers[event_type].append(handler)

    def unregister_handler(self, event_type: InputEventType, handler: Callable[[GuiInputEvent], None]) -> None:
        """Unregister an input event handler.
        
        Parameters
        ----------
        event_type : InputEventType
            Type of event to unregister.
        handler : Callable[[GuiInputEvent], None]
            Handler function to remove.
        
        Returns
        -------
        None
        """
        if event_type in self._input_handlers:
            try:
                self._input_handlers[event_type].remove(handler)
            except ValueError:
                pass

    def start_processing(self) -> None:
        """Start input event processing.
        
        Returns
        -------
        None
        """
        from ornata.api.exports.definitions import InputState
        self.state = InputState.ACTIVE
        self._enabled = True
        logger.debug(f"Started input processing for window {self.window_id}")

    def stop_processing(self) -> None:
        """Stop input event processing.
        
        Returns
        -------
        None
        """
        from ornata.api.exports.definitions import InputState
        self.state = InputState.IDLE
        self._enabled = False
        logger.debug(f"Stopped input processing for window {self.window_id}")

    def suspend_processing(self) -> None:
        """Suspend input event processing.
        
        Returns
        -------
        None
        """
        from ornata.api.exports.definitions import InputState
        self.state = InputState.SUSPENDED
        logger.debug(f"Suspended input processing for window {self.window_id}")

    def resume_processing(self) -> None:
        """Resume input event processing.
        
        Returns
        -------
        None
        """
        from ornata.api.exports.definitions import InputState
        self.state = InputState.ACTIVE
        logger.debug(f"Resumed input processing for window {self.window_id}")

    def get_modifier_state(self) -> InputModifierState:
        """Get current modifier key state.
        
        Returns
        -------
        InputModifierState
            Current modifier state.
        """
        return self._modifiers

    def _get_context(self) -> InputContext:
        """Get the input context.
        
        Returns
        -------
        InputContext
            Input context instance.
        """
        from ornata.api.exports.definitions import InputContext, InputState
        return InputContext(
            event_bus=self.event_bus,
            window_id=self.window_id,
            is_active=self.state == InputState.ACTIVE,
            modifiers=self._modifiers
        )

    def _setup_default_handlers(self) -> None:
        """Setup default input event handlers.
        
        Returns
        -------
        None
        """
        # Default handlers can be overridden by user handlers
        pass

    def _update_modifiers(self, event: GuiInputEvent) -> None:
        """Update modifier state based on event.
        
        Parameters
        ----------
        event : GuiInputEvent
            Input event to process.
        
        Returns
        -------
        None
        """
        from ornata.api.exports.definitions import InputEventType
        if event.event_type == InputEventType.KEY_DOWN:
            if event.key == "control":
                self._modifiers.ctrl = True
            elif event.key == "alt":
                self._modifiers.alt = True
            elif event.key == "shift":
                self._modifiers.shift = True
            elif event.key == "meta":
                self._modifiers.meta = True
        elif event.event_type == InputEventType.KEY_UP:
            if event.key == "control":
                self._modifiers.ctrl = False
            elif event.key == "alt":
                self._modifiers.alt = False
            elif event.key == "shift":
                self._modifiers.shift = False
            elif event.key == "meta":
                self._modifiers.meta = False

    def _filter_event(self, event: GuiInputEvent) -> GuiInputEvent | None:
        """Filter and process input event.
        
        Parameters
        ----------
        event : GuiInputEvent
            Input event to filter.
        
        Returns
        -------
        GuiInputEvent | None
            Filtered event or None if event should be ignored.
        """
        from ornata.api.exports.definitions import InputEventType
        # Basic event filtering - can be extended
        if event.event_type == InputEventType.MOUSE_MOVE:
            # Only send mouse move events if position changed significantly
            dx = abs(event.x - self._last_mouse_pos[0])
            dy = abs(event.y - self._last_mouse_pos[1])
            if dx < 1 and dy < 1:
                return None
            self._last_mouse_pos = (event.x, event.y)
        
        return event

    def _dispatch_to_event_system(self, event: GuiInputEvent) -> None:
        """Dispatch event to the system event bus.
        
        Parameters
        ----------
        event : GuiInputEvent
            Event to dispatch.
        
        Returns
        -------
        None
        """
        from ornata.api.exports.definitions import Event, EventPriority
        # Map GUI input events to system events
        system_event_type = self._map_to_system_event_type(event.event_type)
        if system_event_type is None:
            return
        
        # Create system event
        system_event = Event(
            type=system_event_type,
            data=self._create_event_data(event),
            priority=EventPriority.NORMAL,
            timestamp=event.timestamp,
            source=f"gui_input:{self.window_id}"
        )
        
        # Dispatch to event bus (EventBus publishes events)
        self.event_bus.publish(system_event)

    def _map_to_system_event_type(self, gui_event_type: InputEventType) -> EventType | None:
        """Map GUI input event type to system event type.
        
        Parameters
        ----------
        gui_event_type : InputEventType
            GUI input event type.
        
        Returns
        -------
        EventType | None
            System event type or None if no mapping.
        """
        from ornata.api.exports.definitions import EventType, InputEventType
        mapping = {
            InputEventType.KEY_DOWN: EventType.KEY_DOWN,
            InputEventType.KEY_UP: EventType.KEY_UP,
            InputEventType.MOUSE_DOWN: EventType.MOUSE_DOWN,
            InputEventType.MOUSE_UP: EventType.MOUSE_UP,
            InputEventType.MOUSE_MOVE: EventType.MOUSE_MOVE,
            InputEventType.MOUSE_WHEEL: EventType.MOUSE_WHEEL,
            InputEventType.WINDOW_FOCUS: EventType.WINDOW_FOCUS,
            InputEventType.WINDOW_BLUR: EventType.WINDOW_BLUR,
            InputEventType.WINDOW_RESIZE: EventType.WINDOW_RESIZE,
            InputEventType.WINDOW_CLOSE: EventType.WINDOW_CLOSE,
        }
        return mapping.get(gui_event_type)

    def _create_event_data(self, event: GuiInputEvent) -> KeyEvent | MouseEvent | dict[str, Any]:
        """Create system event data from GUI input event.
        
        Parameters
        ----------
        event : GuiInputEvent
            GUI input event.
        
        Returns
        -------
        KeyEvent | MouseEvent | dict[str, Any]
            System event data.
        """
        from ornata.api.exports.definitions import (
            EventType,
            InputEventType,
            KeyEvent,
            KeyEventType,
            MouseEvent,
            MouseEventType,
        )

        if event.event_type in (InputEventType.KEY_DOWN, InputEventType.KEY_UP):
            modifiers_set: set[str] = set()
            if event.modifiers.ctrl:
                modifiers_set.add("ctrl")
            if event.modifiers.alt:
                modifiers_set.add("alt")
            if event.modifiers.shift:
                modifiers_set.add("shift")
            if event.modifiers.meta:
                modifiers_set.add("meta")

            key_event_type = KeyEventType.KEYDOWN if event.event_type == InputEventType.KEY_DOWN else KeyEventType.KEYUP

            return KeyEvent(
                event_type=key_event_type,
                key=event.key or "",
                char=event.char or None,
                modifiers=frozenset(modifiers_set),
                ctrl=event.modifiers.ctrl,
                alt=event.modifiers.alt,
                shift=event.modifiers.shift,
                repeat=False,
            )

        if event.event_type in (
            InputEventType.MOUSE_DOWN,
            InputEventType.MOUSE_UP,
            InputEventType.MOUSE_MOVE,
            InputEventType.MOUSE_WHEEL,
        ):
            button_code: int | None = event.button if isinstance(event.button, int) else None
            button_name_map: dict[int, str] = {1: "left", 2: "middle", 3: "right"}
            button_name: str | None = button_name_map[button_code] if button_code is not None and button_code in button_name_map else None

            if event.event_type == InputEventType.MOUSE_DOWN:
                mouse_event_type = MouseEventType.BUTTON_DOWN
            elif event.event_type == InputEventType.MOUSE_UP:
                mouse_event_type = MouseEventType.BUTTON_UP
            elif event.event_type == InputEventType.MOUSE_MOVE:
                mouse_event_type = MouseEventType.MOVE
            else:
                # Basic wheel mapping; positive delta as scroll up, negative as scroll down
                if getattr(event, "delta_y", 0) > 0:
                    mouse_event_type = MouseEventType.SCROLL_UP
                elif getattr(event, "delta_y", 0) < 0:
                    mouse_event_type = MouseEventType.SCROLL_DOWN
                else:
                    mouse_event_type = MouseEventType.MOVE

            return MouseEvent(
                event_type=mouse_event_type,
                x=event.x,
                y=event.y,
                button=button_code,
                button_name=button_name,
            )
        else:
            return {
                "window_id": self.window_id,
                "event_type": event.event_type,
                "x": event.x,
                "y": event.y,
            }

    def _call_handlers(self, event: GuiInputEvent) -> None:
        """Call registered event handlers.
        
        Parameters
        ----------
        event : GuiInputEvent
            Event to handle.
        
        Returns
        -------
        None
        """
        handlers = self._input_handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Input handler failed: {e}")


class InputRouter:
    """Input event router for multiple windows and contexts.
    
    Routes input events to the appropriate input processors
    based on window focus and event source.
    
    Parameters
    ----------
    event_bus : EventBus
        Event bus for system events.
    
    Returns
    -------
    InputRouter
        Input router instance.
    """
    
    def __init__(self, event_bus: EventBus) -> None:
        """Initialize the input router.
        
        Parameters
        ----------
        event_bus : EventBus
            Event bus for system events.
        
        Returns
        -------
        None
        """
        self.event_bus = event_bus
        self._processors: dict[str, InputProcessor] = {}
        self._focused_window: str | None = None
        self._lock = threading.Lock()
        
        logger.debug("Initialized InputRouter")

    def register_window(self, window_id: str) -> InputProcessor:
        """Register a window for input processing.
        
        Parameters
        ----------
        window_id : str
            Window identifier.
        
        Returns
        -------
        InputProcessor
            Input processor for the window.
        """
        with self._lock:
            if window_id not in self._processors:
                processor = InputProcessor(self.event_bus, window_id)
                self._processors[window_id] = processor
                logger.debug(f"Registered window {window_id} for input processing")
                
                # Set as focused if it's the first window
                if self._focused_window is None:
                    self._set_focused_window(window_id)
            
            return self._processors[window_id]

    def unregister_window(self, window_id: str) -> None:
        """Unregister a window from input processing.
        
        Parameters
        ----------
        window_id : str
            Window identifier.
        
        Returns
        -------
        None
        """
        with self._lock:
            if window_id in self._processors:
                processor = self._processors[window_id]
                processor.stop_processing()
                del self._processors[window_id]
                
                if self._focused_window == window_id:
                    self._focused_window = None
                    # Focus another window if available
                    if self._processors:
                        next_window = next(iter(self._processors.keys()))
                        self._set_focused_window(next_window)
                
                logger.debug(f"Unregistered window {window_id} from input processing")

    def route_event(self, event: GuiInputEvent) -> None:
        """Route an input event to the appropriate processor.
        
        Parameters
        ----------
        event : GuiInputEvent
            Input event to route.
        
        Returns
        -------
        None
        """
        with self._lock:
            # Route to event source if specified
            if event.source and event.source in self._processors:
                self._processors[event.source].process_event(event)
            # Route to focused window for general input
            elif self._focused_window and self._focused_window in self._processors:
                self._processors[self._focused_window].process_event(event)

    def set_focused_window(self, window_id: str) -> None:
        """Set the focused window for input routing.
        
        Parameters
        ----------
        window_id : str
            Window identifier to focus.
        
        Returns
        -------
        None
        """
        self._set_focused_window(window_id)

    def _set_focused_window(self, window_id: str) -> None:
        """Internal method to set focused window.
        
        Parameters
        ----------
        window_id : str
            Window identifier to focus.
        
        Returns
        -------
        None
        """
        from ornata.api.exports.definitions import GuiInputEvent, InputEventType
        with self._lock:
            # Remove focus from previous window
            if self._focused_window and self._focused_window in self._processors:
                old_processor = self._processors[self._focused_window]
                old_processor.suspend_processing()
            
            # Set focus to new window
            if window_id in self._processors:
                self._focused_window = window_id
                new_processor = self._processors[window_id]
                new_processor.resume_processing()
                
                # Send focus event
                focus_event = GuiInputEvent(
                    event_type=InputEventType.WINDOW_FOCUS,
                    source=window_id
                )
                new_processor.process_event(focus_event)
                
                logger.debug(f"Set focused window to {window_id}")

    def get_focused_window(self) -> str | None:
        """Get the currently focused window.
        
        Returns
        -------
        str | None
            Focused window identifier or None.
        """
        return self._focused_window

    def get_processor(self, window_id: str) -> InputProcessor | None:
        """Get input processor for a window.
        
        Parameters
        ----------
        window_id : str
            Window identifier.
        
        Returns
        -------
        InputProcessor | None
            Input processor or None if not found.
        """
        return self._processors.get(window_id)


# Factory function for creating input systems
def create_input_system(event_bus: EventBus) -> InputRouter:
    """Create a complete GUI input system.
    
    Parameters
    ----------
    event_bus : EventBus
        Event bus for system integration.
    
    Returns
    -------
    InputRouter
        Complete input system.
    """
    return InputRouter(event_bus)


__all__ = [
    "InputProcessor",
    "InputRouter",
    "create_input_system",
]