"""Software buffer management for GPU fallback emulation."""

from __future__ import annotations

import threading


class SwVertexBuffer:
    """Software vertex buffer emulation for GPU fallback.

    Provides vertex buffer functionality using CPU memory when GPU
    acceleration is unavailable. Maintains vertex data and provides
    manipulation and access methods.
    """

    def __init__(self, data: list[float], usage: str = "static", stride_floats: int = 5) -> None:
        """Initialize software vertex buffer with data.

        Args:
            data: List of vertex data (floats representing positions, normals, etc.)
            usage: Buffer usage pattern ('static', 'dynamic', 'stream') - informational only
            stride_floats: Number of floats per vertex (default 5: x, y, z, u, v)
        """
        self._data = list(data)
        self._usage = usage
        self._stride_floats = max(1, int(stride_floats))
        self._vertex_count = len(data) // self._stride_floats
        self._lock = threading.RLock()

        if len(data) % self._stride_floats != 0:
            raise ValueError(f"Data length {len(data)} not divisible by stride {self._stride_floats}")

    @property
    def data(self) -> list[float]:
        """Get the buffer data."""
        with self._lock:
            return self._data.copy()

    @property
    def usage(self) -> str:
        """Get the buffer usage pattern."""
        return self._usage

    @property
    def vertex_count(self) -> int:
        """Get the number of vertices in the buffer."""
        with self._lock:
            return self._vertex_count

    @property
    def stride_floats(self) -> int:
        """Get the number of floats per vertex."""
        return self._stride_floats

    def bind(self) -> None:
        """Bind the buffer for operations (no-op in software emulation)."""
        pass

    def unbind(self) -> None:
        """Unbind the buffer (no-op in software emulation)."""
        pass

    def update_data(self, data: list[float]) -> None:
        """Update all buffer data.

        Args:
            data: New vertex data to store in the buffer.
        """
        with self._lock:
            if len(data) % self._stride_floats != 0:
                raise ValueError(f"Data length {len(data)} not divisible by stride {self._stride_floats}")
            self._data = list(data)
            self._vertex_count = len(data) // self._stride_floats

    def update_sub_data(self, offset: int, data: list[float]) -> None:
        """Update a portion of the buffer data.

        Args:
            offset: Starting vertex index to update.
            data: New vertex data to upload.
        """
        with self._lock:
            if offset < 0 or offset >= self._vertex_count:
                raise ValueError(f"Invalid offset {offset} for buffer with {self._vertex_count} vertices")

            data_vertices = len(data) // self._stride_floats
            if data_vertices == 0:
                raise ValueError("Data must contain at least one complete vertex")

            if offset + data_vertices > self._vertex_count:
                raise ValueError("Data would exceed buffer bounds")

            start_idx = offset * self._stride_floats
            end_idx = start_idx + len(data)
            self._data[start_idx:end_idx] = data

    def get_vertex(self, index: int) -> list[float]:
        """Get vertex data at the specified index.

        Args:
            index: Vertex index to retrieve.

        Returns:
            List of floats representing the vertex data.
        """
        with self._lock:
            if index < 0 or index >= self._vertex_count:
                raise IndexError(f"Vertex index {index} out of range [0, {self._vertex_count})")
            start_idx = index * self._stride_floats
            end_idx = start_idx + self._stride_floats
            return self._data[start_idx:end_idx]

    def set_vertex(self, index: int, vertex_data: list[float]) -> None:
        """Set vertex data at the specified index.

        Args:
            index: Vertex index to update.
            vertex_data: New vertex data (must match stride_floats length).
        """
        with self._lock:
            if index < 0 or index >= self._vertex_count:
                raise IndexError(f"Vertex index {index} out of range [0, {self._vertex_count})")
            if len(vertex_data) != self._stride_floats:
                raise ValueError(f"Vertex data length {len(vertex_data)} must match stride {self._stride_floats}")
            start_idx = index * self._stride_floats
            end_idx = start_idx + self._stride_floats
            self._data[start_idx:end_idx] = vertex_data

    def append_vertex(self, vertex_data: list[float]) -> None:
        """Append a new vertex to the buffer.

        Args:
            vertex_data: Vertex data to append (must match stride_floats length).
        """
        with self._lock:
            if len(vertex_data) != self._stride_floats:
                raise ValueError(f"Vertex data length {len(vertex_data)} must match stride {self._stride_floats}")
            self._data.extend(vertex_data)
            self._vertex_count += 1

    def get_data_range(self, start_vertex: int, end_vertex: int) -> list[float]:
        """Get a range of vertex data.

        Args:
            start_vertex: Starting vertex index (inclusive).
            end_vertex: Ending vertex index (exclusive).

        Returns:
            List of floats for the vertex range.
        """
        with self._lock:
            if start_vertex < 0 or end_vertex > self._vertex_count or start_vertex > end_vertex:
                raise ValueError(f"Invalid range [{start_vertex}, {end_vertex}) for buffer with {self._vertex_count} vertices")
            start_idx = start_vertex * self._stride_floats
            end_idx = end_vertex * self._stride_floats
            return self._data[start_idx:end_idx]


class SwIndexBuffer:
    """Software index buffer emulation for GPU fallback.

    Provides index buffer functionality using CPU memory when GPU
    acceleration is unavailable. Maintains index data and provides
    manipulation and access methods.
    """

    def __init__(self, indices: list[int], usage: str = "static") -> None:
        """Initialize software index buffer with indices.

        Args:
            indices: List of vertex indices for indexed rendering.
            usage: Buffer usage pattern ('static', 'dynamic', 'stream') - informational only.
        """
        self._data = list(indices)
        self._usage = usage
        self._index_count = len(indices)
        self._lock = threading.RLock()

    @property
    def data(self) -> list[int]:
        """Get the buffer data."""
        with self._lock:
            return self._data.copy()

    @property
    def usage(self) -> str:
        """Get the buffer usage pattern."""
        return self._usage

    @property
    def index_count(self) -> int:
        """Get the number of indices in the buffer."""
        with self._lock:
            return self._index_count

    def bind(self) -> None:
        """Bind the buffer for operations (no-op in software emulation)."""
        pass

    def unbind(self) -> None:
        """Unbind the buffer (no-op in software emulation)."""
        pass

    def update_data(self, data: list[int]) -> None:
        """Update all buffer data.

        Args:
            data: New index data to store in the buffer.
        """
        with self._lock:
            self._data = list(data)
            self._index_count = len(data)

    def update_sub_data(self, offset: int, data: list[int]) -> None:
        """Update a portion of the buffer data.

        Args:
            offset: Starting index position to update.
            data: New index data to upload.
        """
        with self._lock:
            if offset < 0 or offset >= self._index_count:
                raise ValueError(f"Invalid offset {offset} for buffer with {self._index_count} indices")

            if offset + len(data) > self._index_count:
                raise ValueError("Data would exceed buffer bounds")

            self._data[offset:offset + len(data)] = data

    def get_index(self, index: int) -> int:
        """Get index value at the specified position.

        Args:
            index: Index position to retrieve.

        Returns:
            The vertex index at the specified position.
        """
        with self._lock:
            if index < 0 or index >= self._index_count:
                raise IndexError(f"Index position {index} out of range [0, {self._index_count})")
            return self._data[index]

    def set_index(self, index: int, value: int) -> None:
        """Set index value at the specified position.

        Args:
            index: Index position to update.
            value: New vertex index value.
        """
        with self._lock:
            if index < 0 or index >= self._index_count:
                raise IndexError(f"Index position {index} out of range [0, {self._index_count})")
            self._data[index] = value

    def append_index(self, value: int) -> None:
        """Append a new index to the buffer.

        Args:
            value: Index value to append.
        """
        with self._lock:
            self._data.append(value)
            self._index_count += 1

    def get_data_range(self, start_index: int, end_index: int) -> list[int]:
        """Get a range of index data.

        Args:
            start_index: Starting index position (inclusive).
            end_index: Ending index position (exclusive).

        Returns:
            List of indices for the specified range.
        """
        with self._lock:
            if start_index < 0 or end_index > self._index_count or start_index > end_index:
                raise ValueError(f"Invalid range [{start_index}, {end_index}) for buffer with {self._index_count} indices")
            return self._data[start_index:end_index]