"""Frame buffer and frame timing for the rendering system.

Frames represent discrete rendering snapshots with timing information
and state tracking for synchronization.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.definitions import Frame


logger = get_logger(__name__)


class FrameBuffer:
    """Manages a circular buffer of frames for multi-buffering.
    
    Parameters
    ----------
    buffer_size : int
        Number of frames to buffer (2 for double-buffer, 3 for triple-buffer).
        
    Returns
    -------
    FrameBuffer
        A frame buffer manager.
    """

    def __init__(self, buffer_size: int = 2) -> None:
        """Initialize the frame buffer.
        
        Parameters
        ----------
        buffer_size : int
            Number of frames to buffer.
            
        Returns
        -------
        None
        """
        if buffer_size < 1:
            raise ValueError(f"Buffer size must be at least 1, got {buffer_size}")
        self.buffer_size = buffer_size
        self._frames: list[Frame | None] = [None] * buffer_size
        self._current_index: int = 0
        self._frame_counter: int = 0
        logger.debug(f"Initialized FrameBuffer with size {buffer_size}")

    def acquire_next_frame(self) -> Frame:
        """Acquire the next available frame for rendering.
        
        Returns
        -------
        Frame
            A frame ready for rendering.
        """
        from ornata.api.exports.definitions import Frame
        self._current_index = (self._current_index + 1) % self.buffer_size
        frame = Frame(frame_number=self._frame_counter)
        self._frames[self._current_index] = frame
        self._frame_counter += 1
        logger.log(5, f"Acquired frame {frame.frame_number} at index {self._current_index}")
        return frame

    def get_current_frame(self) -> Frame | None:
        """Get the current frame.
        
        Returns
        -------
        Frame | None
            The current frame, or None if buffer is empty.
        """
        return self._frames[self._current_index]

    def get_ready_frame(self) -> Frame | None:
        """Get the next frame that's ready for presentation.
        
        Returns
        -------
        Frame | None
            A frame in READY state, or None if no frames are ready.
        """
        from ornata.api.exports.definitions import FrameState
        for frame in self._frames:
            if frame and frame.state == FrameState.READY:
                return frame
        return None

    def clear(self) -> None:
        """Clear all frames from the buffer.
        
        Returns
        -------
        None
        """
        self._frames = [None] * self.buffer_size
        logger.debug("Cleared frame buffer")

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about the frame buffer.
        
        Returns
        -------
        dict[str, Any]
            Statistics including frame count, buffer usage, etc.
        """
        from ornata.api.exports.definitions import FrameState
        active_frames = sum(1 for f in self._frames if f is not None)
        ready_frames = sum(1 for f in self._frames if f and f.state == FrameState.READY)
        return {
            "buffer_size": self.buffer_size,
            "active_frames": active_frames,
            "ready_frames": ready_frames,
            "total_frames": self._frame_counter,
        }
