"""GPU buffer utility functions for shared functionality across all buffer types."""

from __future__ import annotations

import logging
from typing import Any

from ornata.api.exports.definitions import BufferUsage, GPUBufferAlignmentError, MemoryAlignment, RendererType
from ornata.api.exports.utils import get_logger

logger = get_logger(__name__)


class GPUBufferUtils:
    """Shared utilities for GPU buffer operations."""

    # Standard memory alignment requirements as per GPU_TODO.md specification
    ALIGNMENT_REQUIREMENTS = {
        "float": MemoryAlignment("float", 4, 4),
        "vec2": MemoryAlignment("vec2", 8, 8),
        "vec3": MemoryAlignment("vec3", 16, 12),   # Padded to 16 bytes
        "vec4": MemoryAlignment("vec4", 16, 16),
        "mat3": MemoryAlignment("mat3", 16, 36),   # 3x4 vec4 rows
        "mat4": MemoryAlignment("mat4", 16, 64),   # 4x4 vec4 rows
        "int": MemoryAlignment("int", 4, 4),
        "uint": MemoryAlignment("uint", 4, 4),
        "short": MemoryAlignment("short", 2, 2),
        "color_rgba": MemoryAlignment("color_rgba", 4, 4),  # RGBA
        "color_rgb": MemoryAlignment("color_rgb", 4, 3),    # RGB (padded)
    }

    @classmethod
    def validate_memory_alignment(cls, data: list[Any], types: list[str]) -> list[Any]:
        """Validate and pad data according to GPU memory alignment requirements.
        
        Args:
            data: List of data values
            types: List of type names corresponding to each data element
            
        Returns:
            Padded data list with proper alignment padding
            
        Raises:
            ValueError: If data and types lists have different lengths
            KeyError: If an unknown type is specified
        """
        if len(data) != len(types):
            raise ValueError(f"Data length ({len(data)}) must match types length ({len(types)})")
        
        validated_data: list[Any] = []
        
        for i, (value, type_name) in enumerate(zip(data, types, strict=True)):
            if type_name not in cls.ALIGNMENT_REQUIREMENTS:
                raise KeyError(f"Unknown type: {type_name}")
            
            alignment = cls.ALIGNMENT_REQUIREMENTS[type_name]
            validated_data.append(value)
            
            # Add padding after this element if needed
            current_offset = sum(cls.ALIGNMENT_REQUIREMENTS[t].size_bytes for t in types[:i+1])
            padding_needed = alignment.alignment_bytes - (current_offset % alignment.alignment_bytes)
            
            if padding_needed > 0:
                validated_data.extend([0.0] * (padding_needed // 4))
        
        return validated_data

    @classmethod
    def calculate_buffer_size(cls, data: list[Any], types: list[str] | None = None) -> int:
        """Calculate the exact byte size of buffer data.
        
        Args:
            data: Data values to calculate size for
            types: Optional type names for proper alignment calculation
            
        Returns:
            Total byte size of the buffer
        """
        if types is None:
            # Assume all data are floats
            return len(data) * 4  # 4 bytes per float
        
        total_size = 0
        for _, (_value, type_name) in enumerate(zip(data, types, strict=True)):
            if type_name not in cls.ALIGNMENT_REQUIREMENTS:
                logger.warning(f"Unknown type '{type_name}', assuming 4 bytes")
                size = 4
            else:
                size = cls.ALIGNMENT_REQUIREMENTS[type_name].size_bytes
            
            total_size += size
            
            # Add padding
            alignment = cls.ALIGNMENT_REQUIREMENTS.get(type_name)
            if alignment:
                total_size += (alignment.alignment_bytes - (size % alignment.alignment_bytes)) % alignment.alignment_bytes
        
        return total_size

    @classmethod
    def create_staged_data(cls, data: list[float], usage: BufferUsage) -> list[float]:
        """Create properly staged data for GPU upload.
        
        Args:
            data: Source data
            usage: How the data will be used (affects staging strategy)
            
        Returns:
            Staged data ready for GPU upload
        """
        if usage == BufferUsage.STATIC:
            # Static data: copy once, GPU will cache it
            return data.copy()
        elif usage == BufferUsage.DYNAMIC:
            # Dynamic data: keep original data, staging overhead acceptable
            return data.copy()
        else:  # STREAM
            # Stream data: create a new buffer to avoid cache pollution
            return data.copy()

    @staticmethod
    def get_usage_constant(renderer: RendererType, usage: BufferUsage) -> int:
        """Get renderer-specific usage constant.
        
        Args:
            renderer: Target GPU renderer
            usage: Usage pattern
            
        Returns:
            Renderer-specific constant value
        """
        if renderer == RendererType.OPENGL:
            usage_map = {
                BufferUsage.STATIC: 0x88E4,  # GL_STATIC_DRAW
                BufferUsage.DYNAMIC: 0x88E8,  # GL_DYNAMIC_DRAW
                BufferUsage.STREAM: 0x88E0,  # GL_STREAM_DRAW
            }
        elif renderer == RendererType.DIRECTX11:
            usage_map = {
                BufferUsage.STATIC: 0,  # D3D11_USAGE_DEFAULT
                BufferUsage.DYNAMIC: 1,  # D3D11_USAGE_DYNAMIC
                BufferUsage.STREAM: 2,   # D3D11_USAGE_STAGING
            }
        else:
            usage_map = {
                BufferUsage.STATIC: 0,
                BufferUsage.DYNAMIC: 0,
                BufferUsage.STREAM: 0,
            }

        return usage_map.get(usage, 0)

    @staticmethod
    def format_directx_buffer_desc(usage: BufferUsage, size_bytes: int, bind_flags: int, cpu_access: int = 0) -> dict[str, Any]:
        """Create DirectX buffer description dictionary.
        
        Args:
            usage: Buffer usage pattern
            size_bytes: Size of buffer in bytes
            bind_flags: D3D11_BIND_* flags
            cpu_access: D3D11_CPU_ACCESS_* flags (default: 0)
            
        Returns:
            Dictionary containing DirectX buffer description
        """
        return {
            "ByteWidth": size_bytes,
            "Usage": GPUBufferUtils.get_usage_constant(RendererType.DIRECTX11, usage),
            "BindFlags": bind_flags,
            "CPUAccessFlags": cpu_access,
            "MiscFlags": 0,
        }


def safe_com_release(com_object: Any) -> bool:
    """Safely release COM object with error handling.
    
    Args:
        com_object: COM object to release
        
    Returns:
        True if successfully released, False otherwise
    """
    try:
        if com_object is None:
            return False

        release_method = getattr(com_object, "Release", None)
        if release_method is None:
            release_method = getattr(com_object, "release", None)

        if release_method is None:
            logger.warning("COM object %s has no Release method", type(com_object).__name__)
            return False

        release_method()
        return True
    except Exception as e:
        logger.warning(f"Error releasing COM object: {e}")

    return False


def validate_buffer_data(data: list[float], expected_floats: int | None = None) -> None:
    """Validate buffer data before GPU operations.
    
    Args:
        data: Buffer data to validate
        expected_floats: Expected number of floats (optional)
        
    Raises:
        GPUBufferAlignmentError: If validation fails
    """
    if expected_floats is not None and len(data) != expected_floats:
        raise GPUBufferAlignmentError(f"Expected {expected_floats} floats, got {len(data)}")
    
    if len(data) == 0:
        logger.warning("Empty buffer data provided")


def format_buffer_info(buffer_type: str, renderer: RendererType | str, usage: BufferUsage | str, size_bytes: int) -> str:
    """Format buffer information for logging.
    
    Args:
        buffer_type: Type of buffer ("vertex", "index", "uniform")
        renderer: GPU renderer used
        usage: Buffer usage pattern
        size_bytes: Buffer size in bytes
        
    Returns:
        Formatted string with buffer information
    """
    # Handle both enum and string values for backward compatibility
    renderer_value = renderer.value if isinstance(renderer, RendererType) else str(renderer)
    usage_value = usage.value if isinstance(usage, BufferUsage) else str(usage)
    
    return f"{buffer_type} buffer [{renderer_value}, {usage_value}, {size_bytes} bytes]"


def log_buffer_operation(operation: str, buffer_info: str, success: bool, details: str = "") -> None:
    """Log buffer operation with consistent formatting.
    
    Args:
        operation: Operation name ("created", "updated", "bound", etc.)
        buffer_info: Buffer information string
        success: Whether the operation succeeded
        details: Additional details to log
    """
    status = "SUCCESS" if success else "FAILED"
    log_level = logging.DEBUG if success else logging.WARNING
    
    if details:
        logger.log(log_level, f"GPU buffer {operation} {status}: {buffer_info} - {details}")
    else:
        logger.log(log_level, f"GPU buffer {operation} {status}: {buffer_info}")