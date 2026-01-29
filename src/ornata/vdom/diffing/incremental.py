"""Incremental diffing utilities."""

from typing import Any


class IncrementalDiffer:
    """Handles incremental diffing for large trees."""

    def __init__(self) -> None:
        """Initialize the incremental differ."""
        self._previous_chunks: dict[str, Any] = {}

    def diff_incremental(self, current_chunks: list[Any], previous_chunks: list[Any]) -> list[dict[str, Any]]:
        """Perform incremental diffing between chunk sets."""
        patches: list[dict[str, Any]] = []

        # Compare chunks
        max_len = max(len(current_chunks), len(previous_chunks))

        for i in range(max_len):
            current_chunk = current_chunks[i] if i < len(current_chunks) else None
            previous_chunk = previous_chunks[i] if i < len(previous_chunks) else None

            if current_chunk != previous_chunk:
                if current_chunk is None:
                    patches.append({"type": "remove_chunk", "index": i})
                elif previous_chunk is None:
                    patches.append({"type": "add_chunk", "index": i, "chunk": current_chunk})
                else:
                    patches.append({"type": "update_chunk", "index": i, "old_chunk": previous_chunk, "new_chunk": current_chunk})

        return patches

    def update_previous_chunks(self, chunks: list[Any]) -> None:
        """Update the stored previous chunks."""
        self._previous_chunks = {str(i): chunk for i, chunk in enumerate(chunks)}
