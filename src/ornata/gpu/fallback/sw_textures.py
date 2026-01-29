"""Software texture management for GPU fallback emulation."""

from __future__ import annotations

import threading


class SwTexture2D:
    """Software texture 2D emulation for GPU fallback.

    Provides texture data storage and sampling functionality using CPU memory
    when GPU acceleration is unavailable. Supports RGBA pixel data and
    nearest-neighbor sampling with coordinate processing.
    """

    def __init__(self, width: int, height: int, data: list[int] | None = None, format_: str = "rgba") -> None:
        """Initialize software texture with dimensions and optional data.

        Args:
            width: Texture width in pixels.
            height: Texture height in pixels.
            data: Optional pixel data as flat list of RGBA values (4 ints per pixel).
            format_: Pixel format ('rgba' supported, 4 channels per pixel).
        """
        if width <= 0 or height <= 0:
            raise ValueError(f"Invalid texture dimensions: {width}x{height}")

        self._width = width
        self._height = height
        self._format = format_
        self._channels = 4  # RGBA
        self._pixel_count = width * height
        self._data_size = self._pixel_count * self._channels

        if data is None:
            # Initialize with transparent black
            self._data = [0] * self._data_size
        else:
            if len(data) != self._data_size:
                raise ValueError(f"Data size {len(data)} does not match expected {self._data_size} for {width}x{height} texture")
            self._data = list(data)

        self._lock = threading.RLock()

    @property
    def width(self) -> int:
        """Get texture width."""
        return self._width

    @property
    def height(self) -> int:
        """Get texture height."""
        return self._height

    @property
    def format(self) -> str:
        """Get texture pixel format."""
        return self._format

    @property
    def data(self) -> list[int]:
        """Get copy of texture pixel data."""
        with self._lock:
            return self._data.copy()

    def bind(self) -> None:
        """Bind texture for operations (no-op in software emulation)."""
        pass

    def unbind(self) -> None:
        """Unbind texture (no-op in software emulation)."""
        pass

    def update_data(self, data: list[int]) -> None:
        """Update all texture pixel data.

        Args:
            data: New pixel data (must match texture size and format).
        """
        if len(data) != self._data_size:
            raise ValueError(f"Data size {len(data)} does not match texture size {self._data_size}")
        with self._lock:
            self._data = list(data)

    def update_sub_data(self, x: int, y: int, width: int, height: int, data: list[int]) -> None:
        """Update a rectangular region of texture data.

        Args:
            x: Starting X coordinate.
            y: Starting Y coordinate.
            width: Region width.
            height: Region height.
            data: Pixel data for the region.
        """
        if x < 0 or y < 0 or width <= 0 or height <= 0:
            raise ValueError(f"Invalid region: x={x}, y={y}, w={width}, h={height}")
        if x + width > self._width or y + height > self._height:
            raise ValueError("Region exceeds texture bounds")

        expected_size = width * height * self._channels
        if len(data) != expected_size:
            raise ValueError(f"Data size {len(data)} does not match region size {expected_size}")

        with self._lock:
            for dy in range(height):
                src_start = dy * width * self._channels
                src_end = src_start + width * self._channels
                dst_start = ((y + dy) * self._width + x) * self._channels
                dst_end = dst_start + width * self._channels
                self._data[dst_start:dst_end] = data[src_start:src_end]

    def get_pixel(self, x: int, y: int) -> list[int]:
        """Get RGBA pixel data at coordinates.

        Args:
            x: X coordinate (0 to width-1).
            y: Y coordinate (0 to height-1).

        Returns:
            List of 4 ints [R, G, B, A].
        """
        if x < 0 or x >= self._width or y < 0 or y >= self._height:
            raise ValueError(f"Coordinates ({x}, {y}) out of bounds for {self._width}x{self._height} texture")

        with self._lock:
            start_idx = (y * self._width + x) * self._channels
            return self._data[start_idx:start_idx + self._channels]

    def set_pixel(self, x: int, y: int, rgba: list[int]) -> None:
        """Set RGBA pixel data at coordinates.

        Args:
            x: X coordinate (0 to width-1).
            y: Y coordinate (0 to height-1).
            rgba: List of 4 ints [R, G, B, A] (0-255 range).
        """
        if x < 0 or x >= self._width or y < 0 or y >= self._height:
            raise ValueError(f"Coordinates ({x}, {y}) out of bounds for {self._width}x{self._height} texture")
        if len(rgba) != self._channels:
            raise ValueError(f"RGBA data must have {self._channels} channels")

        with self._lock:
            start_idx = (y * self._width + x) * self._channels
            self._data[start_idx:start_idx + self._channels] = rgba

    def sample(self, u: float, v: float, wrap_mode: str = "clamp") -> list[int]:
        """Sample texture at normalized coordinates using nearest neighbor.

        Args:
            u: U coordinate (0.0 to 1.0).
            v: V coordinate (0.0 to 1.0).
            wrap_mode: Coordinate wrapping mode ('clamp', 'repeat', 'mirror').

        Returns:
            List of 4 ints [R, G, B, A] sampled color.
        """
        x, y = self._process_coordinates(u, v, wrap_mode)
        return self.get_pixel(x, y)

    def sample_bilinear(self, u: float, v: float, wrap_mode: str = "clamp") -> list[int]:
        """Sample texture at normalized coordinates using bilinear interpolation.

        Args:
            u: U coordinate (0.0 to 1.0).
            v: V coordinate (0.0 to 1.0).
            wrap_mode: Coordinate wrapping mode ('clamp', 'repeat', 'mirror').

        Returns:
            List of 4 ints [R, G, B, A] interpolated color.
        """
        # Convert to pixel coordinates with fractional part
        x_f, y_f = self._process_coordinates_float(u, v, wrap_mode)

        # Get integer coordinates for bilinear sampling
        x0 = int(x_f)
        y0 = int(y_f)
        x1 = min(x0 + 1, self._width - 1)
        y1 = min(y0 + 1, self._height - 1)

        # Fractional weights
        wx = x_f - x0
        wy = y_f - y0

        # Sample four corners
        c00 = self.get_pixel(x0, y0)
        c10 = self.get_pixel(x1, y0)
        c01 = self.get_pixel(x0, y1)
        c11 = self.get_pixel(x1, y1)

        # Bilinear interpolation
        result: list[int] = []
        for i in range(self._channels):
            top = c00[i] * (1 - wx) + c10[i] * wx
            bottom = c01[i] * (1 - wx) + c11[i] * wx
            result.append(int(top * (1 - wy) + bottom * wy))

        return result

    def _process_coordinates(self, u: float, v: float, wrap_mode: str) -> tuple[int, int]:
        """Process normalized coordinates into integer pixel coordinates.

        Args:
            u: U coordinate (0.0 to 1.0).
            v: V coordinate (0.0 to 1.0).
            wrap_mode: Wrapping mode.

        Returns:
            Tuple of (x, y) pixel coordinates.
        """
        x_f, y_f = self._process_coordinates_float(u, v, wrap_mode)
        return int(x_f), int(y_f)

    def _process_coordinates_float(self, u: float, v: float, wrap_mode: str) -> tuple[float, float]:
        """Process normalized coordinates with wrapping, returning float pixel coords.

        Args:
            u: U coordinate (0.0 to 1.0).
            v: V coordinate (0.0 to 1.0).
            wrap_mode: Wrapping mode ('clamp', 'repeat', 'mirror').

        Returns:
            Tuple of (x, y) float pixel coordinates.
        """
        if wrap_mode == "clamp":
            u = max(0.0, min(1.0, u))
            v = max(0.0, min(1.0, v))
        elif wrap_mode == "repeat":
            u = u % 1.0
            v = v % 1.0
        elif wrap_mode == "mirror":
            u = u % 2.0
            if u > 1.0:
                u = 2.0 - u
            v = v % 2.0
            if v > 1.0:
                v = 2.0 - v
        else:
            raise ValueError(f"Unsupported wrap mode: {wrap_mode}")

        x = u * (self._width - 1)
        y = v * (self._height - 1)

        return x, y


def process_texture_coordinates(uv_coords: list[float], wrap_mode: str = "clamp") -> list[float]:
    """Process a list of texture coordinates with wrapping.

    Args:
        uv_coords: Flat list of UV coordinates [u0, v0, u1, v1, ...].
        wrap_mode: Coordinate wrapping mode ('clamp', 'repeat', 'mirror').

    Returns:
        Processed UV coordinates (clamped/repeated as specified).
    """
    if len(uv_coords) % 2 != 0:
        raise ValueError("UV coordinates must be pairs (even length)")

    result: list[float] = []
    for i in range(0, len(uv_coords), 2):
        u, v = uv_coords[i], uv_coords[i + 1]

        if wrap_mode == "clamp":
            u = max(0.0, min(1.0, u))
            v = max(0.0, min(1.0, v))
        elif wrap_mode == "repeat":
            u = u % 1.0
            v = v % 1.0
        elif wrap_mode == "mirror":
            u = u % 2.0
            if u > 1.0:
                u = 2.0 - u
            v = v % 2.0
            if v > 1.0:
                v = 2.0 - v
        else:
            raise ValueError(f"Unsupported wrap mode: {wrap_mode}")

        result.extend([u, v])

    return result