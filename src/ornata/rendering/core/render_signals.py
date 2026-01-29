"""Rendering event signals and notifications.

Provides a signal system for rendering events like frame start, frame complete,
errors, and performance warnings.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
        from ornata.api.exports.definitions import RenderSignal, SignalHandler, SignalType

logger = get_logger(__name__)


class SignalDispatcher:
    """Dispatches rendering signals to registered handlers.
    
    The dispatcher allows components to subscribe to specific signal types
    and receive notifications when those signals are emitted.
    
    Returns
    -------
    SignalDispatcher
        A signal dispatcher instance.
    """

    def __init__(self) -> None:
        """Initialize the signal dispatcher.
        
        Returns
        -------
        None
        """
        self._handlers: dict[SignalType, list[SignalHandler]] = {}
        self._all_handlers: list[SignalHandler] = []
        logger.debug("Initialized SignalDispatcher")

    def connect(self, signal_type: SignalType, handler: SignalHandler) -> None:
        """Connect a handler to a specific signal type.
        
        Parameters
        ----------
        signal_type : SignalType
            The signal type to listen for.
        handler : SignalHandler
            The handler function to call.
            
        Returns
        -------
        None
        """
        if signal_type not in self._handlers:
            self._handlers[signal_type] = []
        self._handlers[signal_type].append(handler)
        logger.log(5, f"Connected handler to {signal_type}")

    def connect_all(self, handler: SignalHandler) -> None:
        """Connect a handler to all signal types.
        
        Parameters
        ----------
        handler : SignalHandler
            The handler function to call for all signals.
            
        Returns
        -------
        None
        """
        self._all_handlers.append(handler)
        logger.log(5, "Connected handler to all signals")

    def disconnect(self, signal_type: SignalType, handler: SignalHandler) -> None:
        """Disconnect a handler from a specific signal type.
        
        Parameters
        ----------
        signal_type : SignalType
            The signal type to disconnect from.
        handler : SignalHandler
            The handler function to remove.
            
        Returns
        -------
        None
        """
        if signal_type in self._handlers and handler in self._handlers[signal_type]:
            self._handlers[signal_type].remove(handler)
            logger.log(5, f"Disconnected handler from {signal_type}")

    def disconnect_all(self, handler: SignalHandler) -> None:
        """Disconnect a handler from all signal types.
        
        Parameters
        ----------
        handler : SignalHandler
            The handler function to remove.
            
        Returns
        -------
        None
        """
        if handler in self._all_handlers:
            self._all_handlers.remove(handler)
        for handlers in self._handlers.values():
            if handler in handlers:
                handlers.remove(handler)
        logger.log(5, "Disconnected handler from all signals")

    def emit(self, signal: RenderSignal) -> None:
        """Emit a signal to all registered handlers.
        
        Parameters
        ----------
        signal : RenderSignal
            The signal to emit.
            
        Returns
        -------
        None
        """
        logger.log(5, f"Emitting signal: {signal.signal_type}")

        # Call all-signal handlers
        for handler in self._all_handlers:
            try:
                handler(signal)
            except Exception as e:
                logger.error(f"Error in signal handler: {e}")

        # Call type-specific handlers
        handlers = self._handlers.get(signal.signal_type, [])
        for handler in handlers:
            try:
                handler(signal)
            except Exception as e:
                logger.error(f"Error in signal handler for {signal.signal_type}: {e}")

    def clear_handlers(self, signal_type: SignalType | None = None) -> None:
        """Clear all handlers for a signal type, or all handlers if None.
        
        Parameters
        ----------
        signal_type : SignalType | None
            The signal type to clear handlers for, or None for all.
            
        Returns
        -------
        None
        """
        if signal_type is None:
            self._handlers.clear()
            self._all_handlers.clear()
            logger.debug("Cleared all signal handlers")
        elif signal_type in self._handlers:
            self._handlers[signal_type].clear()
            logger.debug(f"Cleared handlers for {signal_type}")

    def get_handler_count(self, signal_type: SignalType | None = None) -> int:
        """Get the number of handlers registered.
        
        Parameters
        ----------
        signal_type : SignalType | None
            Signal type to count, or None for total.
            
        Returns
        -------
        int
            Number of registered handlers.
        """
        if signal_type is None:
            total = len(self._all_handlers)
            for handlers in self._handlers.values():
                total += len(handlers)
            return total
        return len(self._handlers.get(signal_type, []))


class SignalEmitter:
    """Helper for emitting rendering signals.
    
    Parameters
    ----------
    dispatcher : SignalDispatcher
        The dispatcher to emit signals through.
        
    Returns
    -------
    SignalEmitter
        A signal emitter instance.
    """

    def __init__(self, dispatcher: SignalDispatcher) -> None:
        """Initialize the signal emitter.
        
        Parameters
        ----------
        dispatcher : SignalDispatcher
            The dispatcher to use.
            
        Returns
        -------
        None
        """
        self.dispatcher = dispatcher

    def emit_render_start(self, frame_number: int, **kwargs: Any) -> None:
        """Emit a render start signal.
        
        Parameters
        ----------
        frame_number : int
            The frame number being rendered.
        **kwargs : Any
            Additional signal data.
            
        Returns
        -------
        None
        """
        import time

        from ornata.api.exports.definitions import RenderSignal, SignalType

        signal = RenderSignal(
            signal_type=SignalType.RENDER_START,
            data=kwargs,
            timestamp=time.time(),
            frame_number=frame_number,
        )
        self.dispatcher.emit(signal)

    def emit_render_complete(self, frame_number: int, duration: float, **kwargs: Any) -> None:
        """Emit a render complete signal.
        
        Parameters
        ----------
        frame_number : int
            The frame number that completed.
        duration : float
            Render duration in seconds.
        **kwargs : Any
            Additional signal data.
            
        Returns
        -------
        None
        """
        import time

        from ornata.api.exports.definitions import RenderSignal, SignalType

        data = {"duration": duration, **kwargs}
        signal = RenderSignal(
            signal_type=SignalType.RENDER_COMPLETE,
            data=data,
            timestamp=time.time(),
            frame_number=frame_number,
        )
        self.dispatcher.emit(signal)

    def emit_render_error(self, frame_number: int | None, error: Exception, **kwargs: Any) -> None:
        """Emit a render error signal.
        
        Parameters
        ----------
        frame_number : int | None
            The frame number where error occurred.
        error : Exception
            The error that occurred.
        **kwargs : Any
            Additional signal data.
            
        Returns
        -------
        None
        """
        import time

        from ornata.api.exports.definitions import RenderSignal, SignalType

        data = {"error": str(error), "error_type": type(error).__name__, **kwargs}
        signal = RenderSignal(
            signal_type=SignalType.RENDER_ERROR,
            data=data,
            timestamp=time.time(),
            frame_number=frame_number,
        )
        self.dispatcher.emit(signal)

    def emit_frame_dropped(self, frame_number: int, reason: str, **kwargs: Any) -> None:
        """Emit a frame dropped signal.
        
        Parameters
        ----------
        frame_number : int
            The frame number that was dropped.
        reason : str
            Why the frame was dropped.
        **kwargs : Any
            Additional signal data.
            
        Returns
        -------
        None
        """
        import time

        from ornata.api.exports.definitions import RenderSignal, SignalType

        data = {"reason": reason, **kwargs}
        signal = RenderSignal(
            signal_type=SignalType.FRAME_DROPPED,
            data=data,
            timestamp=time.time(),
            frame_number=frame_number,
        )
        self.dispatcher.emit(signal)

    def emit_performance_warning(self, message: str, metric: str, value: float, threshold: float, **kwargs: Any) -> None:
        """Emit a performance warning signal.
        
        Parameters
        ----------
        message : str
            Warning message.
        metric : str
            The performance metric name.
        value : float
            The measured value.
        threshold : float
            The threshold that was exceeded.
        **kwargs : Any
            Additional signal data.
            
        Returns
        -------
        None
        """
        import time

        from ornata.api.exports.definitions import RenderSignal, SignalType

        data = {"message": message, "metric": metric, "value": value, "threshold": threshold, **kwargs}
        signal = RenderSignal(
            signal_type=SignalType.PERFORMANCE_WARNING,
            data=data,
            timestamp=time.time(),
        )
        self.dispatcher.emit(signal)


_global_dispatcher: SignalDispatcher | None = None


def get_global_dispatcher() -> SignalDispatcher:
    """Get the global signal dispatcher instance.
    
    Returns
    -------
    SignalDispatcher
        The global dispatcher.
    """
    global _global_dispatcher
    if _global_dispatcher is None:
        _global_dispatcher = SignalDispatcher()
    return _global_dispatcher


def get_global_emitter() -> SignalEmitter:
    """Get a signal emitter using the global dispatcher.
    
    Returns
    -------
    SignalEmitter
        An emitter using the global dispatcher.
    """
    return SignalEmitter(get_global_dispatcher())
