"""DirectX input layout creation module.

Creates comprehensive input layouts compatible with the ornata GPU system:
    struct VSIn {
        float3 Position : POSITION;   // 12 bytes
        float4 Color    : COLOR;      // 16 bytes (offset 12)
        float2 TexCoord : TEXCOORD0;  // 8 bytes (offset 28)
    };

This provides the foundation for advanced vertex attributes including:
- Position (3D coordinates)
- Color (RGBA)
- Texture coordinates (2D)
- Normals (optional)
- Instance data (for instanced rendering)
"""

from __future__ import annotations

import ctypes
from typing import TYPE_CHECKING, Any

from ornata.api.exports.definitions import VertexAttribute
from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.interop import ID3D11Device, ID3D11InputLayout

logger = get_logger(__name__)


class DirectXInputLayout:
    """Creates ID3D11InputLayout objects with comprehensive vertex format support."""

    # Supported DirectX format constants
    FORMAT_MAP = {
        "float": "DXGI_FORMAT_R32_FLOAT",
        "float2": "DXGI_FORMAT_R32G32_FLOAT", 
        "float3": "DXGI_FORMAT_R32G32B32_FLOAT",
        "float4": "DXGI_FORMAT_R32G32B32A32_FLOAT",
        "uint": "DXGI_FORMAT_R32_UINT",
        "uint2": "DXGI_FORMAT_R32G32_UINT",
        "uint3": "DXGI_FORMAT_R32G32B32_UINT", 
        "uint4": "DXGI_FORMAT_R32G32B32A32_UINT",
        "color_rgba": "DXGI_FORMAT_R8G8B8A8_UNORM",
        "color_rgb": "DXGI_FORMAT_R8G8B8_UNORM",
        "short": "DXGI_FORMAT_R16_SINT",
        "short2": "DXGI_FORMAT_R16G16_SINT",
        "short3": "DXGI_FORMAT_R16G16B16_SINT",
        "short4": "DXGI_FORMAT_R16G16B16A16_SINT",
    }

    def __init__(self, device: ID3D11Device | None) -> None:
        if device is None:
            raise ValueError("DirectXInputLayout requires a valid ID3D11Device")
        self._device: ID3D11Device = device
        self._initialized = True
        self._cached_layouts: dict[str, ID3D11InputLayout] = {}

    def create_standard_layout(self) -> ID3D11InputLayout:
        """Create the standard ornata input layout for position, color, and UV coordinates."""
        attributes = [
            VertexAttribute(
                semantic_name="POSITION",
                semantic_index=0,
                format="DXGI_FORMAT_R32G32B32_FLOAT",
                aligned_byte_offset=0,
                instance_step_rate=0,
            ),
            VertexAttribute(
                semantic_name="COLOR",
                semantic_index=0,
                format="DXGI_FORMAT_R8G8B8A8_UNORM",
                aligned_byte_offset=12,
                instance_step_rate=0,
            ),
            VertexAttribute(
                semantic_name="TEXCOORD",
                semantic_index=0,
                format="DXGI_FORMAT_R32G32_FLOAT",
                aligned_byte_offset=28,
                instance_step_rate=0,
            ),
        ]

        return self._create_layout_from_attributes(attributes, self._get_default_bytecode())

    def create_position_only_layout(self) -> ID3D11InputLayout:
        """Create minimal input layout for position-only rendering."""
        attributes = [
            VertexAttribute(
                semantic_name="POSITION",
                semantic_index=0,
                format="DXGI_FORMAT_R32G32B32_FLOAT",
                aligned_byte_offset=0,
                instance_step_rate=0,
            ),
        ]

        return self._create_layout_from_attributes(attributes, self._get_default_bytecode())

    def create_position_color_layout(self) -> ID3D11InputLayout:
        """Create input layout for position and color only."""
        attributes = [
            VertexAttribute(
                semantic_name="POSITION",
                semantic_index=0,
                format="DXGI_FORMAT_R32G32B32_FLOAT",
                aligned_byte_offset=0,
                instance_step_rate=0,
            ),
            VertexAttribute(
                semantic_name="COLOR",
                semantic_index=0,
                format="DXGI_FORMAT_R8G8B8A8_UNORM",
                aligned_byte_offset=12,
                instance_step_rate=0,
            ),
        ]

        return self._create_layout_from_attributes(attributes, self._get_default_bytecode())

    def create_instanced_layout(self) -> ID3D11InputLayout:
        """Create input layout with instancing support."""

        attributes = [
            # Per-vertex data (stream 0)
            VertexAttribute(
                semantic_name="POSITION",
                semantic_index=0,
                format="DXGI_FORMAT_R32G32B32_FLOAT",
                input_slot=0,
                aligned_byte_offset=0,
                instance_step_rate=0,
            ),
            VertexAttribute(
                semantic_name="TEXCOORD",
                semantic_index=0,
                format="DXGI_FORMAT_R32G32_FLOAT",
                input_slot=0,
                aligned_byte_offset=12,
                instance_step_rate=0,
            ),
            # Per-instance data (stream 1)
            VertexAttribute(
                semantic_name="TEXCOORD",
                semantic_index=1,
                format="DXGI_FORMAT_R32G32_FLOAT",
                input_slot=1,
                aligned_byte_offset=0,
                instance_step_rate=1,
            ),
            VertexAttribute(
                semantic_name="COLOR",
                semantic_index=0,
                format="DXGI_FORMAT_R8G8B8A8_UNORM",
                input_slot=1,
                aligned_byte_offset=8,
                instance_step_rate=1,
            ),
        ]

        return self._create_layout_from_attributes(attributes, self._get_instanced_bytecode())

    def create_custom_layout(self, attributes: list[VertexAttribute], bytecode_data: bytes) -> ID3D11InputLayout:
        """Create a custom input layout from attribute definitions."""
        if not attributes:
            raise ValueError("At least one vertex attribute must be specified")
        
        if not bytecode_data:
            raise ValueError("Vertex shader bytecode is required")

        # Cache key based on attributes
        cache_key = self._generate_cache_key(attributes)
        if cache_key in self._cached_layouts:
            logger.debug(f"Using cached input layout for key: {cache_key}")
            return self._cached_layouts[cache_key]

        layout = self._create_layout_from_attributes(attributes, bytecode_data)
        self._cached_layouts[cache_key] = layout
        return layout

    def _create_layout_from_attributes(self, attributes: list[VertexAttribute], bytecode_data: bytes) -> ID3D11InputLayout:
        from ornata.api.exports.interop import (
            D3D11_INPUT_ELEMENT_DESC,
            D3D11_INPUT_PER_INSTANCE_DATA,
            D3D11_INPUT_PER_VERTEX_DATA,
            ID3D11InputLayout,
        )

        if not self._initialized:
            raise RuntimeError("DirectXInputLayout not initialized")
        if not bytecode_data:
            raise ValueError("Vertex shader bytecode is required")

        # Build descriptors
        descs: list[D3D11_INPUT_ELEMENT_DESC] = []
        for a in attributes:
            fmt_enum = self._get_format_constant(a.format)  # returns a DXGI_FORMAT enum value
            descs.append(D3D11_INPUT_ELEMENT_DESC(
                SemanticName=a.semantic_name.encode("utf-8"),
                SemanticIndex=a.semantic_index,
                Format=fmt_enum,
                InputSlot=a.input_slot,
                AlignedByteOffset=a.aligned_byte_offset,
                InputSlotClass=(D3D11_INPUT_PER_INSTANCE_DATA if a.instance_step_rate > 0 else D3D11_INPUT_PER_VERTEX_DATA),
                InstanceDataStepRate=a.instance_step_rate,
            ))

        # Create a stable buffer for the bytecode and pass pointer + size
        bytecode_buf = ctypes.create_string_buffer(bytecode_data)
        p_bytecode = ctypes.cast(bytecode_buf, ctypes.c_void_p)

        layout = ID3D11InputLayout()  # COMPointer instance
        hr = self._device.CreateInputLayout(
            descs,
            ctypes.c_uint(len(descs)),
            p_bytecode,
            len(bytecode_data),
            layout,  # pass the COM object directly; wrapper handles .out_param()
        )

        if hr != 0:
            raise RuntimeError(f"CreateInputLayout failed: hr={hr}")

        logger.debug("Created DirectX input layout with %d attributes", len(attributes))
        return layout

    def _get_format_constant(self, format_name: str) -> int:
        if format_name in self.FORMAT_MAP:
            format_name = self.FORMAT_MAP[format_name]
        from ornata.api.exports.interop import DXGI_FORMAT
        # Expect full names like "DXGI_FORMAT_R32G32B32_FLOAT"
        name = format_name
        if not name.startswith("DXGI_FORMAT_"):
            name = "DXGI_FORMAT_" + format_name
        return getattr(DXGI_FORMAT, name.replace("DXGI_FORMAT_", ""), DXGI_FORMAT.UNKNOWN)

    def create_input_layout(self, input_elements_or_pointer: list[dict[str, Any]] | int, length: int = 0) -> ID3D11InputLayout:
        """Create input layout from element definitions or bytecode.
        
        Args:
            input_elements_or_pointer: Either a list of input element dictionaries
                                     (from vertex programs) or bytecode pointer (from shader compiler)
            length: Length of bytecode data (only used when first arg is a pointer)
            
        Returns:
            ID3D11InputLayout object
        """
        if isinstance(input_elements_or_pointer, list):
            # Called from vertex program with element definitions
            logger.debug("Creating DirectX input layout from element definitions")
            attributes: list[VertexAttribute] = []
            current_offset = 0
            
            for element in input_elements_or_pointer:
                attr = VertexAttribute(
                    semantic_name=element["semantic"],
                    semantic_index=element["index"],
                    format=self._map_format_to_directx(element["format"]),
                    aligned_byte_offset=current_offset,
                    instance_step_rate=0,
                )
                attributes.append(attr)
                # Update offset based on format size
                current_offset += self._get_format_size(element["format"])
            
            # Use proper vertex shader bytecode if available
            if hasattr(self, '_vertex_bytecode') and self._vertex_bytecode:
                return self._create_layout_from_attributes(attributes, self._vertex_bytecode)
            else:
                return self._create_layout_from_attributes(attributes, self._get_default_bytecode())
        
        elif isinstance(input_elements_or_pointer, int):
            # Called with VS bytecode pointer + length from the shader compiler
            ptr_val = input_elements_or_pointer
            logger.debug(
                "DirectXInputLayout.create_input_layout called with bytecode pointer=%d length=%d",
                ptr_val, length
            )
            if ptr_val <= 0 or length <= 0:
                raise ValueError("Invalid vertex shader bytecode pointer/length")

            # Reconstruct bytes from the pointer so we can pass a stable buffer to D3D
            ptr = ctypes.c_void_p(ptr_val)
            bytecode_data = ctypes.string_at(ptr, length)

            # Build a reasonable default attribute set if none was provided:
            attributes = [
                VertexAttribute("POSITION", 0, "DXGI_FORMAT_R32G32B32_FLOAT", 0, 0, 0),
                VertexAttribute("TEXCOORD", 0, "DXGI_FORMAT_R32G32_FLOAT",    0, 12, 0),
                VertexAttribute("NORMAL",   0, "DXGI_FORMAT_R32G32B32_FLOAT", 0, 20, 0),
            ]

            return self._create_layout_from_attributes(attributes, bytecode_data)
        
        else:
            raise ValueError(f"Unsupported input type: {type(input_elements_or_pointer)}")
    
    def _map_format_to_directx(self, format_name: str) -> str:
        """Map format names to DirectX format constants."""
        format_map = {
            "vec2": "DXGI_FORMAT_R32G32_FLOAT",
            "vec3": "DXGI_FORMAT_R32G32B32_FLOAT",
            "vec4": "DXGI_FORMAT_R32G32B32A32_FLOAT",
            "float2": "DXGI_FORMAT_R32G32_FLOAT",
            "float3": "DXGI_FORMAT_R32G32B32_FLOAT",
            "float4": "DXGI_FORMAT_R32G32B32A32_FLOAT",
        }
        return format_map.get(format_name, "DXGI_FORMAT_R32G32B32A32_FLOAT")
    
    def _get_format_size(self, format_name: str) -> int:
        """Get size in bytes for format."""
        size_map = {
            "vec2": 8, "float2": 8,
            "vec3": 12, "float3": 12,
            "vec4": 16, "float4": 16,
        }
        return size_map.get(format_name, 16)
    
    def set_vertex_bytecode(self, bytecode: bytes) -> None:
        """Store vertex shader bytecode for input layout reflection."""
        self._vertex_bytecode = bytecode
        logger.debug("Vertex bytecode set for input layout creation")

    def _get_default_bytecode(self) -> bytes:
        """Get default vertex shader bytecode for basic layout."""
        # This would typically be compiled HLSL shader bytecode
        # For now, return a minimal bytecode structure
        return b'\x00' * 1024  # Placeholder

    def _get_instanced_bytecode(self) -> bytes:
        """Get vertex shader bytecode for instanced layout."""
        return b'\x00' * 2048  # Placeholder

    def _generate_cache_key(self, attributes: list[VertexAttribute]) -> str:
        """Generate cache key for layout based on attributes."""
        key_parts: list[str] = []
        for attr in attributes:
            key_parts.append(f"{attr.semantic_name}{attr.semantic_index}_{attr.format}_{attr.input_slot}_{attr.aligned_byte_offset}")
        return "|".join(key_parts)

    def clear_cache(self) -> None:
        """Clear all cached input layouts."""
        for layout in self._cached_layouts.values():
            if layout:
                try:
                    layout.release()
                except Exception as e:
                    logger.warning(f"Error releasing cached layout: {e}")
        self._cached_layouts.clear()
        logger.debug("Cleared DirectX input layout cache")

    def __del__(self) -> None:
        """Destructor - release all resources."""
        self.clear_cache()
