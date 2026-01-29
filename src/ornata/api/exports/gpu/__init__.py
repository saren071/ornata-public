"""Auto-generated lazy exports for the gpu subsystem."""

from __future__ import annotations

from importlib import import_module

from ornata.api._warnings import setup_internal_warnings

setup_internal_warnings()

_EXPORT_TARGETS: dict[str, str] = {
    "batching": "ornata.gpu:batching",
    "buffers": "ornata.gpu:buffers",
    "device": "ornata.gpu:device",
    "fallback": "ornata.gpu:fallback",
    "instancing": "ornata.gpu:instancing",
    "memory": "ornata.gpu:memory",
    "pipelines": "ornata.gpu:pipelines",
    "programs": "ornata.gpu:programs",
    "resources": "ornata.gpu:resources",
    "textures": "ornata.gpu:textures",
    "directx": "ornata.gpu.backends:directx",
    "opengl": "ornata.gpu.backends:opengl",
    "backend": "ornata.gpu.backends.directx:backend",
    "buffer": "ornata.gpu.backends.directx:buffer",
    "context": "ornata.gpu.backends.directx:context",
    "input_layout": "ornata.gpu.backends.directx:input_layout",
    "shader_compiler": "ornata.gpu.backends.directx:shader_compiler",
    "swapchain": "ornata.gpu.backends.directx:swapchain",
    "sync": "ornata.gpu.backends.directx:sync",
    "DirectXBackend": "ornata.gpu.backends.directx.backend:DirectXBackend",
    "DirectXBufferManager": "ornata.gpu.backends.directx.buffer:DirectXBufferManager",
    "DirectXContext": "ornata.gpu.backends.directx.context:DirectXContext",
    "DirectXDevice": "ornata.gpu.backends.directx.device:DirectXDevice",
    "DirectXInputLayout": "ornata.gpu.backends.directx.input_layout:DirectXInputLayout",
    "DirectXPipeline": "ornata.gpu.backends.directx.pipeline:DirectXPipeline",
    "DirectXSampler": "ornata.gpu.backends.directx.sampler:DirectXSampler",
    "DirectXShaderCompiler": "ornata.gpu.backends.directx.shader_compiler:DirectXShaderCompiler",
    "DirectXSwapChain": "ornata.gpu.backends.directx.swapchain:DirectXSwapChain",
    "DirectXSync": "ornata.gpu.backends.directx.sync:DirectXSync",
    "DirectXTexture": "ornata.gpu.backends.directx.texture:DirectXTexture",
    "to_ndc_vertices": "ornata.gpu.backends.directx.utils:to_ndc_vertices",
    "ibo": "ornata.gpu.backends.opengl:ibo",
    "program": "ornata.gpu.backends.opengl:program",
    "shader": "ornata.gpu.backends.opengl:shader",
    "state": "ornata.gpu.backends.opengl:state",
    "ubo": "ornata.gpu.backends.opengl:ubo",
    "vao": "ornata.gpu.backends.opengl:vao",
    "vbo": "ornata.gpu.backends.opengl:vbo",
    "OpenGLBackend": "ornata.gpu.backends.opengl.backend:OpenGLBackend",
    "OpenGLContextManager": "ornata.gpu.backends.opengl.context:OpenGLContextManager",
    "OpenGLIBOManager": "ornata.gpu.backends.opengl.ibo:OpenGLIBOManager",
    "OpenGLInstancingManager": "ornata.gpu.backends.opengl.instancing:OpenGLInstancingManager",
    "OpenGLPipelineManager": "ornata.gpu.backends.opengl.pipeline:OpenGLPipelineManager",
    "OpenGLProgramManager": "ornata.gpu.backends.opengl.program:OpenGLProgramManager",
    "OpenGLShaderCompiler": "ornata.gpu.backends.opengl.shader:OpenGLShaderCompiler",
    "OpenGLStateManager": "ornata.gpu.backends.opengl.state:OpenGLStateManager",
    "OpenGLTextureManager": "ornata.gpu.backends.opengl.textures:OpenGLTextureManager",
    "OpenGLUBOManager": "ornata.gpu.backends.opengl.ubo:OpenGLUBOManager",
    "check_opengl_error": "ornata.gpu.backends.opengl.utils:check_opengl_error",
    "get_max_texture_size": "ornata.gpu.backends.opengl.utils:get_max_texture_size",
    "get_max_viewport_dims": "ornata.gpu.backends.opengl.utils:get_max_viewport_dims",
    "get_opengl_extensions": "ornata.gpu.backends.opengl.utils:get_opengl_extensions",
    "get_opengl_version": "ornata.gpu.backends.opengl.utils:get_opengl_version",
    "has_opengl_extension": "ornata.gpu.backends.opengl.utils:has_opengl_extension",
    "log_opengl_info": "ornata.gpu.backends.opengl.utils:log_opengl_info",
    "OpenGLVAOManager": "ornata.gpu.backends.opengl.vao:OpenGLVAOManager",
    "OpenGLVBOManager": "ornata.gpu.backends.opengl.vbo:OpenGLVBOManager",
    "BatchedGeometry": "ornata.gpu.batching.batching:BatchedGeometry",
    "BatchKey": "ornata.gpu.batching.batching:BatchKey",
    "GeometryBatch": "ornata.gpu.batching.batching:GeometryBatch",
    "PersistentBuffer": "ornata.gpu.batching.batching:PersistentBuffer",
    "RenderBatcher": "ornata.gpu.batching.batching:RenderBatcher",
    "index": "ornata.gpu.buffers:index",
    "uniform": "ornata.gpu.buffers:uniform",
    "vertex": "ornata.gpu.buffers:vertex",
    "GPUBuffer": "ornata.gpu.buffers.base:GPUBuffer",
    "IndexBuffer": "ornata.gpu.buffers.index:IndexBuffer",
    "UniformBuffer": "ornata.gpu.buffers.uniform:UniformBuffer",
    "VertexBuffer": "ornata.gpu.buffers.vertex:VertexBuffer",
    "capabilities": "ornata.gpu.device:capabilities",
    "limits": "ornata.gpu.device:limits",
    "render_with_gpu_acceleration": "ornata.gpu.device:render_with_gpu_acceleration",
    "selection": "ornata.gpu.device:selection",
    "Capabilities": "ornata.gpu.device.capabilities:Capabilities",
    "DeviceManager": "ornata.gpu.device.device:DeviceManager",
    "get_device_manager": "ornata.gpu.device.device:get_device_manager",
    "GeometryConverter": "ornata.gpu.device.geometry:GeometryConverter",
    "component_to_gpu_geometry": "ornata.gpu.device.geometry:component_to_gpu_geometry",
    "cpu_render": "ornata.gpu.device.geometry:cpu_render",
    "get_geometry_converter": "ornata.gpu.device.geometry:get_geometry_converter",
    "Limits": "ornata.gpu.device.limits:Limits",
    "DeviceSelector": "ornata.gpu.device.selection:DeviceSelector",
    "blitter": "ornata.gpu.fallback:blitter",
    "cpu_fallback": "ornata.gpu.fallback:cpu_fallback",
    "math": "ornata.gpu.fallback:math",
    "rasterizer": "ornata.gpu.fallback:rasterizer",
    "sw_buffers": "ornata.gpu.fallback:sw_buffers",
    "sw_pipeline": "ornata.gpu.fallback:sw_pipeline",
    "sw_textures": "ornata.gpu.fallback:sw_textures",
    "CPUFallbackBatcher": "ornata.gpu.fallback.batching:CPUFallbackBatcher",
    "CPUBlitter": "ornata.gpu.fallback.blitter:CPUBlitter",
    "CPUFallback": "ornata.gpu.fallback.cpu_fallback:CPUFallback",
    "CPUInstancer": "ornata.gpu.fallback.instancing:CPUInstancer",
    "Matrix4": "ornata.gpu.fallback.math:Matrix4",
    "identity_matrix": "ornata.gpu.fallback.math:identity_matrix",
    "look_at_matrix": "ornata.gpu.fallback.math:look_at_matrix",
    "matrix_multiply": "ornata.gpu.fallback.math:matrix_multiply",
    "ndc_to_screen": "ornata.gpu.fallback.math:ndc_to_screen",
    "orthographic_matrix": "ornata.gpu.fallback.math:orthographic_matrix",
    "perspective_matrix": "ornata.gpu.fallback.math:perspective_matrix",
    "rotate_x_matrix": "ornata.gpu.fallback.math:rotate_x_matrix",
    "rotate_y_matrix": "ornata.gpu.fallback.math:rotate_y_matrix",
    "rotate_z_matrix": "ornata.gpu.fallback.math:rotate_z_matrix",
    "scale_matrix": "ornata.gpu.fallback.math:scale_matrix",
    "screen_to_ndc": "ornata.gpu.fallback.math:screen_to_ndc",
    "transform_point": "ornata.gpu.fallback.math:transform_point",
    "transform_vector": "ornata.gpu.fallback.math:transform_vector",
    "translate_matrix": "ornata.gpu.fallback.math:translate_matrix",
    "vector_add": "ornata.gpu.fallback.math:vector_add",
    "vector_cross": "ornata.gpu.fallback.math:vector_cross",
    "vector_dot": "ornata.gpu.fallback.math:vector_dot",
    "vector_length": "ornata.gpu.fallback.math:vector_length",
    "vector_normalize": "ornata.gpu.fallback.math:vector_normalize",
    "vector_scale": "ornata.gpu.fallback.math:vector_scale",
    "vector_subtract": "ornata.gpu.fallback.math:vector_subtract",
    "viewport_matrix": "ornata.gpu.fallback.math:viewport_matrix",
    "SoftwareRasterizer": "ornata.gpu.fallback.rasterizer:SoftwareRasterizer",
    "SwIndexBuffer": "ornata.gpu.fallback.sw_buffers:SwIndexBuffer",
    "SwVertexBuffer": "ornata.gpu.fallback.sw_buffers:SwVertexBuffer",
    "BlendFactor": "ornata.gpu.fallback.sw_pipeline:BlendFactor",
    "BlendOperation": "ornata.gpu.fallback.sw_pipeline:BlendOperation",
    "DepthFunction": "ornata.gpu.fallback.sw_pipeline:DepthFunction",
    "PipelineConfig": "ornata.gpu.fallback.sw_pipeline:PipelineConfig",
    "SoftwarePipeline": "ornata.gpu.fallback.sw_pipeline:SoftwarePipeline",
    "SoftwareShaderProgram": "ornata.gpu.fallback.sw_pipeline:SoftwareShaderProgram",
    "coerce_matrix": "ornata.gpu.fallback.sw_pipeline:coerce_matrix",
    "resolve_blend_factor": "ornata.gpu.fallback.sw_pipeline:resolve_blend_factor",
    "SwTexture2D": "ornata.gpu.fallback.sw_textures:SwTexture2D",
    "process_texture_coordinates": "ornata.gpu.fallback.sw_textures:process_texture_coordinates",
    "ComponentIdentity": "ornata.gpu.instancing.instancing:ComponentIdentity",
    "InstanceDetector": "ornata.gpu.instancing.instancing:InstanceDetector",
    "InstanceGroup": "ornata.gpu.instancing.instancing:InstanceGroup",
    "InstanceTransform": "ornata.gpu.instancing.instancing:InstanceTransform",
    "allocator": "ornata.gpu.memory:allocator",
    "residency": "ornata.gpu.memory:residency",
    "staging": "ornata.gpu.memory:staging",
    "Allocator": "ornata.gpu.memory.allocator:Allocator",
    "BufferStats": "ornata.gpu.memory.allocator:BufferStats",
    "MemoryBlock": "ornata.gpu.memory.residency:MemoryBlock",
    "Residency": "ornata.gpu.memory.residency:Residency",
    "ResidencyState": "ornata.gpu.memory.residency:ResidencyState",
    "Staging": "ornata.gpu.memory.staging:Staging",
    "TransferDirection": "ornata.gpu.memory.staging:TransferDirection",
    "TransferRequest": "ornata.gpu.memory.staging:TransferRequest",
    "_coerce_transfer_data": "ornata.gpu.memory.staging:_coerce_transfer_data",
    "BarrierType": "ornata.gpu.memory.sync:BarrierType",
    "Sync": "ornata.gpu.memory.sync:Sync",
    "SyncPoint": "ornata.gpu.memory.sync:SyncPoint",
    "SyncType": "ornata.gpu.memory.sync:SyncType",
    "compute_pipeline": "ornata.gpu.pipelines:compute_pipeline",
    "graphics_pipeline": "ornata.gpu.pipelines:graphics_pipeline",
    "ComputePipeline": "ornata.gpu.pipelines.compute_pipeline:ComputePipeline",
    "GraphicsPipeline": "ornata.gpu.pipelines.graphics_pipeline:GraphicsPipeline",
    "compute_program": "ornata.gpu.programs:compute_program",
    "fragment_program": "ornata.gpu.programs:fragment_program",
    "geometry_program": "ornata.gpu.programs:geometry_program",
    "mesh_program": "ornata.gpu.programs:mesh_program",
    "raytracing_programs": "ornata.gpu.programs:raytracing_programs",
    "shader_manager": "ornata.gpu.programs:shader_manager",
    "task_program": "ornata.gpu.programs:task_program",
    "tess_control_program": "ornata.gpu.programs:tess_control_program",
    "tess_eval_program": "ornata.gpu.programs:tess_eval_program",
    "vertex_program": "ornata.gpu.programs:vertex_program",
    "ShaderProgramBase": "ornata.gpu.programs.base:ShaderProgramBase",
    "ComputeProgram": "ornata.gpu.programs.compute_program:ComputeProgram",
    "FragmentProgram": "ornata.gpu.programs.fragment_program:FragmentProgram",
    "load_fragment_program_source": "ornata.gpu.programs.fragment_program:load_fragment_program_source",
    "GeometryProgram": "ornata.gpu.programs.geometry_program:GeometryProgram",
    "MeshProgram": "ornata.gpu.programs.mesh_program:MeshProgram",
    "RayClosestHitProgram": "ornata.gpu.programs.raytracing_programs:RayClosestHitProgram",
    "RayGenProgram": "ornata.gpu.programs.raytracing_programs:RayGenProgram",
    "RayMissProgram": "ornata.gpu.programs.raytracing_programs:RayMissProgram",
    "ShaderManager": "ornata.gpu.programs.shader_manager:ShaderManager",
    "TaskProgram": "ornata.gpu.programs.task_program:TaskProgram",
    "TessControlProgram": "ornata.gpu.programs.tess_control_program:TessControlProgram",
    "TessEvalProgram": "ornata.gpu.programs.tess_eval_program:TessEvalProgram",
    "VertexProgram": "ornata.gpu.programs.vertex_program:VertexProgram",
    "load_vertex_program_source": "ornata.gpu.programs.vertex_program:load_vertex_program_source",
    "GPUBufferHandle": "ornata.gpu.resources:GPUBufferHandle",
    "GPUResourceManager": "ornata.gpu.resources:GPUResourceManager",
    "GPUTextureHandle": "ornata.gpu.resources:GPUTextureHandle",
    "create_gpu_buffer": "ornata.gpu.resources:create_gpu_buffer",
    "create_gpu_texture": "ornata.gpu.resources:create_gpu_texture",
    "get_gpu_resource_manager": "ornata.gpu.resources:get_gpu_resource_manager",
    "sampler_state": "ornata.gpu.textures:sampler_state",
    "texture2d": "ornata.gpu.textures:texture2d",
    "texturecube": "ornata.gpu.textures:texturecube",
    "FilterMode": "ornata.gpu.textures.sampler_state:FilterMode",
    "SamplerState": "ornata.gpu.textures.sampler_state:SamplerState",
    "WrapMode": "ornata.gpu.textures.sampler_state:WrapMode",
    "Texture2D": "ornata.gpu.textures.texture2d:Texture2D",
    "CubeTexture": "ornata.gpu.textures.texturecube:CubeTexture",
    "GPUResource": "ornata.gpu.misc:GPUResource",
    "Shader": "ornata.gpu.misc:Shader",
    "Texture": "ornata.gpu.misc:Texture",
    "Buffer": "ornata.gpu.misc:Buffer",
    "RenderTarget": "ornata.gpu.misc:RenderTarget",
    "GPUBackend": "ornata.gpu.misc:GPUBackend",
    "GPUContext": "ornata.gpu.misc:GPUContext",
    "CompositorBase": "ornata.gpu.misc:CompositorBase",
    "PlatformWindow": "ornata.gpu.misc:PlatformWindow",
    "Canvas": "ornata.gpu.misc:Canvas",
    "create_event_fast": "ornata.gpu.misc:create_event_fast",
    "component_to_gui_node": "ornata.gpu.misc:component_to_gui_node",
}

_RESOLVED_EXPORTS: dict[str, object] = {}

__all__ = ["__getattr__"]

def _load_target(name: str) -> object:
    """Load and cache ``name`` for this subsystem.

    Parameters
    ----------
    name : str
        Export name to resolve.

    Returns
    -------
    object
        Resolved attribute from the owning module.

    Raises
    ------
    AttributeError
        If ``name`` is unknown to this subsystem.
    """

    target = _EXPORT_TARGETS.get(name)
    if target is None:
        raise AttributeError(
            "module 'ornata.api.exports.gpu' has no attribute {name!r}"
        )
    module_name, _, attr_name = target.partition(':')
    module = import_module(module_name)
    value = getattr(module, attr_name)
    _RESOLVED_EXPORTS[name] = value
    globals()[name] = value
    return value

def __getattr__(name: str) -> object:
    """Resolve an export attribute on first access.

    Parameters
    ----------
    name : str
        Export name requested from this module.

    Returns
    -------
    object
        Resolved export value.

    Raises
    ------
    AttributeError
        If ``name`` is not part of this subsystem.
    """

    if name in _RESOLVED_EXPORTS:
        return _RESOLVED_EXPORTS[name]
    return _load_target(name)

def __dir__() -> list[str]:
    """Return the sorted list of exportable names.

    Returns
    -------
    list[str]
        Sorted names available via this module.
    """

    names = ['__getattr__']
    names.extend(_EXPORT_TARGETS)
    return sorted(names)
