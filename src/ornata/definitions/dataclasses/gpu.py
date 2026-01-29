""" GPU Dataclasses for Ornata """

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ornata.definitions.dataclasses.rendering import Rect, Transform
from ornata.definitions.enums import BarrierType, BlendFactor, BlendMode, BlendOperation, CompilationStatus, CullMode, DepthFunction, FillMode, RendererType, ResidencyState, SyncType, TransferDirection

if TYPE_CHECKING:
    import ctypes
    from collections.abc import Callable

    from ornata.api.exports.gpu import Texture

@dataclass(slots=True)
class GPUResourceHandle:
    """Opaque handle to a registered GPU resource."""
    resource_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class GPUTextureInfo:
    """Metadata about a GPU texture."""
    width: int
    height: int
    format_name: str
    mip_levels: int = 1
    layers: int = 1
    label: str | None = None


@dataclass(slots=True)
class GPUBufferHandle(GPUResourceHandle):
    """Handle representing a GPU buffer."""
    size_bytes: int | None = None
    usage: str | None = None


@dataclass(slots=True)
class GPUTextureHandle(GPUResourceHandle):
    """Handle representing a GPU texture."""
    width: int | None = None
    height: int | None = None
    mip_levels: int = 1

    def get_info(self) -> GPUTextureInfo:
        """Return lightweight texture info."""
        return GPUTextureInfo(
            label=self.metadata.get("label", "unknown"),
            width=self.width or 0,
            height=self.height or 0,
            mip_levels=self.mip_levels,
            format_name=self.metadata.get("format", "unknown"),
        )


@dataclass
class VertexAttribute:
    """Describes a single vertex attribute for input layout creation."""
    semantic_name: str
    semantic_index: int
    format: str
    input_slot: int = 0
    aligned_byte_offset: int = 0
    instance_step_rate: int = 0


@dataclass  
class ShaderMacro:
    """HLSL shader macro definition"""
    name: str
    definition: str


@dataclass(frozen=True)
class CompiledShader:
    """Keeps compiled shader bytecode alive while exposing pointer metadata."""
    pointer: int
    length: int
    _buffer: ctypes.Array[ctypes.c_char]

    def compile_shader(
        self, 
        source: str, 
        target: str, 
        entry_point: str = "main"
    ) -> tuple[bytes, str | None]:
        """Compile HLSL shader to bytecode"""
        try:
            entry_bytes = entry_point.encode("utf-8")
            target_bytes = target.encode("utf-8")
            source_bytes = source.encode("utf-8")
            from ornata.api.exports.interop import D3DCompile, blob_to_bytes
            hr, code_blob, error_blob = D3DCompile(source_bytes, entry_bytes, target_bytes)
            if hr != 0:
                error_message = blob_to_bytes(error_blob).decode("utf-8", errors="ignore")
                return (b"", error_message)
            bytecode = blob_to_bytes(code_blob)
            return (bytecode, None)
        except Exception as e:
            return (b"", str(e))


@dataclass
class BatchKey:
    """Key for grouping geometries into batches."""
    shader_name: str
    texture_id: int | None = None
    blend_mode: str = "normal"

    def __hash__(self) -> int:
        return hash((self.shader_name, self.texture_id, self.blend_mode))


@dataclass
class BatchedGeometry:
    """Geometry data for batching."""
    vertices: list[float]
    indices: list[int]
    vertex_offset: int = 0
    index_offset: int = 0
    vertex_count: int = 0
    index_count: int = 0


@dataclass
class Geometry:
    """Geometry data for GPU rendering."""
    vertices: list[float]
    indices: list[int]
    vertex_count: int
    index_count: int


@dataclass
class PersistentBuffer:
    """Persistent buffer for reuse across frames."""
    vertex_buffer: Any | None = None
    index_buffer: Any | None = None
    vertex_data: list[float] | None = None
    index_data: list[int] | None = None
    max_vertices: int = 65536
    max_indices: int = 98304
    current_vertices: int = 0
    current_indices: int = 0
    is_dirty: bool = False

    def can_fit_geometry(self, geometry: Geometry) -> bool:
        return (self.current_vertices + geometry.vertex_count <= self.max_vertices and
                self.current_indices + geometry.index_count <= self.max_indices)

    def add_geometry(self, geometry: Geometry) -> bool:
        if not self.can_fit_geometry(geometry):
            return False
        if self.vertex_data is None:
            self.vertex_data = []
        if self.index_data is None:
            self.index_data = []
        
        adjusted_indices = [idx + self.current_vertices for idx in geometry.indices]
        self.vertex_data.extend(geometry.vertices)
        self.index_data.extend(adjusted_indices)
        self.current_vertices += geometry.vertex_count
        self.current_indices += geometry.index_count
        self.is_dirty = True
        return True

    def clear(self) -> None:
        if self.vertex_data is not None:
            self.vertex_data.clear()
        if self.index_data is not None:
            self.index_data.clear()
        self.current_vertices = 0
        self.current_indices = 0
        self.is_dirty = True

    def is_empty(self) -> bool:
        return self.current_vertices == 0


@dataclass
class MemoryAlignment:
    """Memory alignment requirements for different data types."""
    type_name: str
    alignment_bytes: int
    size_bytes: int
    
    def __str__(self) -> str:
        return f"{self.type_name}: {self.alignment_bytes}-byte aligned ({self.size_bytes} bytes)"


@dataclass(frozen=True)
class InstanceTransform:
    """Transform data for a single instance."""
    x: float = 0.0
    y: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    rotation: float = 0.0


@dataclass(frozen=True)
class Matrix4:
    """4x4 matrix for 3D transformations."""
    data: list[list[float]]

    def __post_init__(self) -> None:
        if len(self.data) != 4 or any(len(row) != 4 for row in self.data):
            raise ValueError("Matrix4 must be 4x4")


@dataclass
class BlendState:
    """Configuration for blending operations in software pipeline."""
    enabled: bool = False
    src_factor: BlendFactor = BlendFactor.ONE
    dst_factor: BlendFactor = BlendFactor.ZERO
    operation: BlendOperation = BlendOperation.ADD
    src_alpha_factor: BlendFactor = BlendFactor.ONE
    dst_alpha_factor: BlendFactor = BlendFactor.ZERO
    alpha_operation: BlendOperation = BlendOperation.ADD


@dataclass
class DepthState:
    """Configuration for depth testing in software pipeline."""
    enabled: bool = False
    function: DepthFunction = DepthFunction.LESS
    write_enabled: bool = True


@dataclass
class RasterizerState:
    """Configuration for rasterization in software pipeline."""
    cull_mode: CullMode = CullMode.NONE
    fill_mode: FillMode = FillMode.SOLID
    depth_bias: float = 0.0
    slope_scaled_depth_bias: float = 0.0


@dataclass
class PipelineConfig:
    """Configuration for software graphics pipeline."""
    blend_state: BlendState = field(default_factory=BlendState)
    depth_state: DepthState = field(default_factory=DepthState)
    rasterizer_state: RasterizerState = field(default_factory=RasterizerState)
    viewport_width: int = 800
    viewport_height: int = 600


@dataclass(frozen=True)
class ComponentIdentity:
    """Hashable identity representation of a renderable component."""
    component_name: str
    component_type: str
    properties_hash: str
    styling_hash: str

    def __hash__(self) -> int:
        return hash((self.component_name, self.component_type, self.properties_hash, self.styling_hash))


@dataclass
class InstanceGroup:
    """Group of identical components for instanced rendering."""
    identity: ComponentIdentity
    base_geometry: Geometry | None = None
    transforms: list[InstanceTransform] = field(default_factory=list)
    component_count: int = 0

    def add_instance(self, transform: InstanceTransform) -> None:
        self.transforms.append(transform)
        self.component_count += 1

    def is_instancable(self, min_instances: int = 2) -> bool:
        return self.component_count >= min_instances and self.base_geometry is not None


@dataclass
class InstancedShader:
    """Shader configuration for GPU instanced rendering."""
    vertex_shader: str
    fragment_shader: str = "#version 460\nout vec4 fragColor;\nvoid main() { fragColor = vec4(1.0); }"
    instance_attributes: list[str] | None = None

    def __post_init__(self) -> None:
        if self.instance_attributes is None:
            self.instance_attributes = [
                "a_instance_position",
                "a_instance_scale_rot",
                "a_instance_color",
            ]

    def get_vertex_layout(self) -> str:
        return """#version 460
layout(location = 0) in vec2 a_position;
layout(location = 1) in vec4 a_color;
layout(location = 2) in vec2 a_instance_position;
layout(location = 3) in vec4 a_instance_scale_rot;
layout(location = 4) in vec4 a_instance_color;
uniform mat4 u_view_projection;
out vec4 v_color;
out vec4 v_instance_color;
void main() {
    vec2 position = a_position * a_instance_scale_rot.zw + a_instance_position;
    gl_Position = u_view_projection * vec4(position, 0.0, 1.0);
    v_color = a_color;
    v_instance_color = a_instance_color;
}"""


@dataclass
class BufferStats:
    """Statistics for buffer pool usage."""
    created: int = 0
    reused: int = 0
    active: int = 0
    leaked: int = 0


@dataclass
class MemoryBlock:
    """Represents a block of GPU memory."""
    id: str
    size: int
    usage: str
    alignment: int
    address: int | None = None
    state: ResidencyState = ResidencyState.RESIDENT
    allocated: bool = False
    last_accessed: float = 0.0
    access_count: int = 0
    priority: int = 0


@dataclass
class TransferRequest:
    """Represents a data transfer request."""
    id: str
    data: list[float] | list[int] | bytes
    size: int
    direction: TransferDirection
    priority: int = 0
    callback: Callable[[TransferRequest], None] | None = None


@dataclass
class SyncPoint:
    """Represents a synchronization point in the GPU command stream."""
    id: str
    type: SyncType
    barrier_type: BarrierType
    command_buffer: Any | None = None
    is_signaled: bool = False


@dataclass(frozen=True)
class BindingGroup:
    """Describe a set of bindings for a specific platform."""
    foundation: str
    com: str | None
    graphics: dict[str, str]
    windowing: dict[str, str]


@dataclass(slots=True, frozen=True)
class GPUBackendInfo:
    """Describes a GPU backend implementation."""
    name: str
    vendor: str
    api_version: str
    driver_version: str | None = None
    capabilities: dict[str, Any] = field(default_factory=dict)
    limits: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class GPUBufferInfo:
    """Metadata about a GPU buffer."""
    size_bytes: int
    usage: str
    mapped: bool = False
    label: str | None = None


@dataclass(slots=True)
class CompositorLayer:
    """Describes a drawable layer managed by the compositor."""
    name: str
    texture: Texture
    rect: Rect
    transform: Transform = field(default_factory=Transform)
    blend_mode: BlendMode = BlendMode.NORMAL
    opacity: float = 1.0
    z_index: int = 0
    visible: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CompilationResult:
    """Shader compilation result container."""
    bytecode: bytes | Any
    errors: list[str]
    warnings: list[str]
    success: bool
    renderer_type: RendererType
    compilation_time_ms: float = 0.0
    status: CompilationStatus = CompilationStatus.PENDING


@dataclass(slots=True, frozen=True)
class ShaderUniform:
    """Shader uniform variable definition."""
    name: str
    type_name: str
    location: int
    size_bytes: int
    array_size: int = 1


@dataclass(slots=True, frozen=True)
class ShaderAttribute:
    """Shader vertex attribute definition."""
    name: str
    type_name: str
    location: int
    size_bytes: int


@dataclass(slots=True)
class PipelineDefinition:
    """Complete shader pipeline definition."""
    name: str
    vertex_shader: str | None = None
    fragment_shader: str | None = None
    geometry_shader: str | None = None
    tessellation_control_shader: str | None = None
    tessellation_evaluation_shader: str | None = None
    mesh_shader: str | None = None
    task_shader: str | None = None
    compute_shader: str | None = None
    ray_generation_shader: str | None = None
    ray_miss_shader: str | None = None
    ray_closest_hit_shader: str | None = None

__all__ = [
    "BatchedGeometry",
    "BatchKey",
    "BindingGroup",
    "BlendState",
    "BufferStats",
    "CompilationResult",
    "ComponentIdentity",
    "CompositorLayer",
    "DepthState",
    "Geometry",
    "GPUBackendInfo",
    "GPUBufferHandle",
    "GPUBufferInfo",
    "GPUResourceHandle",
    "GPUTextureHandle",
    "GPUTextureInfo",
    "InstancedShader",
    "InstanceGroup",
    "InstanceTransform",
    "Matrix4",
    "MemoryAlignment",
    "MemoryBlock",
    "PersistentBuffer",
    "PipelineConfig",
    "PipelineDefinition",
    "RasterizerState",
    "ShaderAttribute",
    "ShaderMacro",
    "ShaderUniform",
    "SyncPoint",
    "TransferRequest",
    "VertexAttribute",
    "CompiledShader",
]
