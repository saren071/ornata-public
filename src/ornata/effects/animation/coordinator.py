"""Animation coordination and sequencing."""

import threading
from typing import TYPE_CHECKING

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.effects.animation.keyframes import Animation

logger = get_logger(__name__)


class AnimationCoordinator:
    """Coordinates multiple animations and sequences."""

    def __init__(self) -> None:
        """Initialize the coordinator."""
        self._sequences: dict[str, AnimationSequence] = {}
        self._lock = threading.RLock()

    def create_sequence(self, sequence_id: str, animations: list[Animation]) -> None:
        """Create an animation sequence.

        Args:
            sequence_id: Unique identifier for the sequence.
            animations: List of animations in the sequence.
        """
        with self._lock:
            sequence = AnimationSequence(sequence_id, animations)
            self._sequences[sequence_id] = sequence
            logger.debug(f"Created animation sequence {sequence_id} with {len(animations)} animations")

    def start_sequence(self, sequence_id: str) -> None:
        """Start an animation sequence.

        Args:
            sequence_id: The sequence ID to start.
        """
        with self._lock:
            if sequence_id in self._sequences:
                self._sequences[sequence_id].start()
                logger.debug(f"Started animation sequence {sequence_id}")

    def stop_sequence(self, sequence_id: str) -> None:
        """Stop an animation sequence.

        Args:
            sequence_id: The sequence ID to stop.
        """
        with self._lock:
            if sequence_id in self._sequences:
                self._sequences[sequence_id].stop()
                logger.debug(f"Stopped animation sequence {sequence_id}")

    def update_sequences(self, delta_time: float) -> None:
        """Update all active sequences.

        Args:
            delta_time: Time elapsed since last update.
        """
        with self._lock:
            completed: list[str] = []
            for sequence_id, sequence in self._sequences.items():
                sequence.update(delta_time)
                if sequence.is_complete():
                    completed.append(sequence_id)

            # Remove completed sequences
            for sequence_id in completed:
                del self._sequences[sequence_id]
                logger.debug(f"Completed animation sequence {sequence_id}")

    def get_active_sequences(self) -> list[str]:
        """Get IDs of active sequences.

        Returns:
            List of active sequence IDs.
        """
        with self._lock:
            return list(self._sequences.keys())


class AnimationSequence:
    """Represents a sequence of animations."""

    def __init__(self, sequence_id: str, animations: list[Animation]) -> None:
        """Initialize the sequence.

        Args:
            sequence_id: Unique identifier for the sequence.
            animations: List of animations in the sequence.
        """
        self.sequence_id = sequence_id
        self._animations = animations
        self._current_index = 0
        self._is_playing = False
        self._lock = threading.RLock()

    def start(self) -> None:
        """Start the sequence."""
        with self._lock:
            self._is_playing = True
            self._current_index = 0
            if self._animations:
                self._animations[0].start()
                logger.debug(f"Started animation sequence {self.sequence_id}")

    def stop(self) -> None:
        """Stop the sequence."""
        with self._lock:
            self._is_playing = False
            for animation in self._animations:
                if not animation.is_complete():
                    animation.stop()
            logger.debug(f"Stopped animation sequence {self.sequence_id}")

    def update(self, delta_time: float) -> None:
        """Update the sequence.

        Args:
            delta_time: Time elapsed since last update.
        """
        with self._lock:
            if not self._is_playing:
                return

            # Update current animation
            if self._current_index < len(self._animations):
                current_animation = self._animations[self._current_index]
                current_animation.update(delta_time)

                # Check if current animation is complete
                if current_animation.is_complete():
                    self._current_index += 1
                    # Start next animation if available
                    if self._current_index < len(self._animations):
                        self._animations[self._current_index].start()
                    else:
                        # Sequence complete
                        self._is_playing = False
                        logger.debug(f"Completed animation sequence {self.sequence_id}")

    def is_complete(self) -> bool:
        """Check if the sequence is complete.

        Returns:
            True if the sequence is complete.
        """
        with self._lock:
            return self._current_index >= len(self._animations)
