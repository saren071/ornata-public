"""Type stubs for the gpu subsystem exports."""

from __future__ import annotations

from ornata.gpu import batching as batching
from ornata.gpu import buffers as buffers
from ornata.gpu import device as device
from ornata.gpu import fallback as fallback
from ornata.gpu import instancing as instancing
from ornata.gpu import memory as memory
from ornata.gpu import pipelines as pipelines
from ornata.gpu import programs as programs
from ornata.gpu import resources as resources
from ornata.gpu import textures as textures
from ornata.gpu.backends import directx as directx
from ornata.gpu.backends import opengl as opengl
from ornata.gpu.backends.directx import backend as backend
from ornata.gpu.backends.directx import buffer as buffer
from ornata.gpu.backends.directx import context as context
from ornata.gpu.backends.directx import input_layout as input_layout
from ornata.gpu.backends.directx import shader_compiler as shader_compiler
from ornata.gpu.backends.directx import swapchain as swapchain
from ornata.gpu.backends.directx import sync as sync
from ornata.gpu.backends.directx.backend import DirectXBackend as DirectXBackend
from ornata.gpu.backends.directx.buffer import DirectXBufferManager as DirectXBufferManager
from ornata.gpu.backends.directx.context import DirectXContext as DirectXContext
from ornata.gpu.backends.directx.device import DirectXDevice as DirectXDevice
from ornata.gpu.backends.directx.input_layout import DirectXInputLayout as DirectXInputLayout
from ornata.gpu.backends.directx.pipeline import DirectXPipeline as DirectXPipeline
from ornata.gpu.backends.directx.sampler import DirectXSampler as DirectXSampler
from ornata.gpu.backends.directx.shader_compiler import DirectXShaderCompiler as DirectXShaderCompiler
from ornata.gpu.backends.directx.shader_compiler import _CompiledShader as _CompiledShader  #type: ignore
from ornata.gpu.backends.directx.swapchain import DirectXSwapChain as DirectXSwapChain
from ornata.gpu.backends.directx.sync import DirectXSync as DirectXSync
from ornata.gpu.backends.directx.texture import DirectXTexture as DirectXTexture
from ornata.gpu.backends.directx.utils import to_ndc_vertices as to_ndc_vertices
from ornata.gpu.backends.opengl import ibo as ibo
from ornata.gpu.backends.opengl import program as program
from ornata.gpu.backends.opengl import shader as shader
from ornata.gpu.backends.opengl import state as state
from ornata.gpu.backends.opengl import ubo as ubo
from ornata.gpu.backends.opengl import vao as vao
from ornata.gpu.backends.opengl import vbo as vbo
from ornata.gpu.backends.opengl.backend import OpenGLBackend as OpenGLBackend
from ornata.gpu.backends.opengl.context import OpenGLContextManager as OpenGLContextManager
from ornata.gpu.backends.opengl.ibo import OpenGLIBOManager as OpenGLIBOManager
from ornata.gpu.backends.opengl.instancing import OpenGLInstancingManager as OpenGLInstancingManager
from ornata.gpu.backends.opengl.pipeline import OpenGLPipelineManager as OpenGLPipelineManager
from ornata.gpu.backends.opengl.program import OpenGLProgramManager as OpenGLProgramManager
from ornata.gpu.backends.opengl.shader import OpenGLShaderCompiler as OpenGLShaderCompiler
from ornata.gpu.backends.opengl.state import OpenGLStateManager as OpenGLStateManager
from ornata.gpu.backends.opengl.textures import OpenGLTextureManager as OpenGLTextureManager
from ornata.gpu.backends.opengl.ubo import OpenGLUBOManager as OpenGLUBOManager
from ornata.gpu.backends.opengl.utils import check_opengl_error as check_opengl_error
from ornata.gpu.backends.opengl.utils import get_max_texture_size as get_max_texture_size
from ornata.gpu.backends.opengl.utils import get_max_viewport_dims as get_max_viewport_dims
from ornata.gpu.backends.opengl.utils import get_opengl_extensions as get_opengl_extensions
from ornata.gpu.backends.opengl.utils import get_opengl_version as get_opengl_version
from ornata.gpu.backends.opengl.utils import has_opengl_extension as has_opengl_extension
from ornata.gpu.backends.opengl.utils import log_opengl_info as log_opengl_info
from ornata.gpu.backends.opengl.vao import OpenGLVAOManager as OpenGLVAOManager
from ornata.gpu.backends.opengl.vbo import OpenGLVBOManager as OpenGLVBOManager
from ornata.gpu.batching.batching import BatchedGeometry as BatchedGeometry
from ornata.gpu.batching.batching import BatchKey as BatchKey
from ornata.gpu.batching.batching import GeometryBatch as GeometryBatch
from ornata.gpu.batching.batching import PersistentBuffer as PersistentBuffer
from ornata.gpu.batching.batching import RenderBatcher as RenderBatcher
from ornata.gpu.buffers import index as index
from ornata.gpu.buffers import uniform as uniform
from ornata.gpu.buffers import vertex as vertex
from ornata.gpu.buffers.base import GPUBuffer as GPUBuffer
from ornata.gpu.buffers.index import IndexBuffer as IndexBuffer
from ornata.gpu.buffers.uniform import UniformBuffer as UniformBuffer
from ornata.gpu.buffers.vertex import VertexBuffer as VertexBuffer
from ornata.gpu.device import capabilities as capabilities
from ornata.gpu.device import limits as limits
from ornata.gpu.device import render_with_gpu_acceleration as render_with_gpu_acceleration
from ornata.gpu.device import selection as selection
from ornata.gpu.device.capabilities import Capabilities as Capabilities
from ornata.gpu.device.device import DeviceManager as DeviceManager
from ornata.gpu.device.device import get_device_manager as get_device_manager
from ornata.gpu.device.geometry import GeometryConverter as GeometryConverter
from ornata.gpu.device.geometry import component_to_gpu_geometry as component_to_gpu_geometry  #type: ignore
from ornata.gpu.device.geometry import cpu_render as cpu_render  #type: ignore
from ornata.gpu.device.geometry import get_geometry_converter as get_geometry_converter
from ornata.gpu.device.limits import Limits as Limits
from ornata.gpu.device.selection import DeviceSelector as DeviceSelector
from ornata.gpu.fallback import blitter as blitter
from ornata.gpu.fallback import cpu_fallback as cpu_fallback
from ornata.gpu.fallback import math as math
from ornata.gpu.fallback import rasterizer as rasterizer
from ornata.gpu.fallback import sw_buffers as sw_buffers
from ornata.gpu.fallback import sw_pipeline as sw_pipeline
from ornata.gpu.fallback import sw_textures as sw_textures
from ornata.gpu.fallback.batching import CPUFallbackBatcher as CPUFallbackBatcher
from ornata.gpu.fallback.blitter import CPUBlitter as CPUBlitter
from ornata.gpu.fallback.cpu_fallback import CPUFallback as CPUFallback
from ornata.gpu.fallback.instancing import CPUInstancer as CPUInstancer
from ornata.gpu.fallback.math import Matrix4 as Matrix4
from ornata.gpu.fallback.math import identity_matrix as identity_matrix
from ornata.gpu.fallback.math import look_at_matrix as look_at_matrix
from ornata.gpu.fallback.math import matrix_multiply as matrix_multiply
from ornata.gpu.fallback.math import ndc_to_screen as ndc_to_screen
from ornata.gpu.fallback.math import orthographic_matrix as orthographic_matrix
from ornata.gpu.fallback.math import perspective_matrix as perspective_matrix
from ornata.gpu.fallback.math import rotate_x_matrix as rotate_x_matrix
from ornata.gpu.fallback.math import rotate_y_matrix as rotate_y_matrix
from ornata.gpu.fallback.math import rotate_z_matrix as rotate_z_matrix
from ornata.gpu.fallback.math import scale_matrix as scale_matrix
from ornata.gpu.fallback.math import screen_to_ndc as screen_to_ndc
from ornata.gpu.fallback.math import transform_point as transform_point
from ornata.gpu.fallback.math import transform_vector as transform_vector
from ornata.gpu.fallback.math import translate_matrix as translate_matrix
from ornata.gpu.fallback.math import vector_add as vector_add
from ornata.gpu.fallback.math import vector_cross as vector_cross
from ornata.gpu.fallback.math import vector_dot as vector_dot
from ornata.gpu.fallback.math import vector_length as vector_length
from ornata.gpu.fallback.math import vector_normalize as vector_normalize
from ornata.gpu.fallback.math import vector_scale as vector_scale
from ornata.gpu.fallback.math import vector_subtract as vector_subtract
from ornata.gpu.fallback.math import viewport_matrix as viewport_matrix
from ornata.gpu.fallback.rasterizer import SoftwareRasterizer as SoftwareRasterizer
from ornata.gpu.fallback.sw_buffers import SwIndexBuffer as SwIndexBuffer
from ornata.gpu.fallback.sw_buffers import SwVertexBuffer as SwVertexBuffer
from ornata.gpu.fallback.sw_pipeline import BlendFactor as BlendFactor
from ornata.gpu.fallback.sw_pipeline import BlendOperation as BlendOperation
from ornata.gpu.fallback.sw_pipeline import DepthFunction as DepthFunction
from ornata.gpu.fallback.sw_pipeline import PipelineConfig as PipelineConfig
from ornata.gpu.fallback.sw_pipeline import SoftwarePipeline as SoftwarePipeline
from ornata.gpu.fallback.sw_pipeline import SoftwareShaderProgram as SoftwareShaderProgram
from ornata.gpu.fallback.sw_pipeline import _coerce_matrix as _coerce_matrix  #type: ignore
from ornata.gpu.fallback.sw_pipeline import _resolve_blend_factor as _resolve_blend_factor  #type: ignore
from ornata.gpu.fallback.sw_textures import SwTexture2D as SwTexture2D
from ornata.gpu.fallback.sw_textures import process_texture_coordinates as process_texture_coordinates
from ornata.gpu.instancing.instancing import ComponentIdentity as ComponentIdentity
from ornata.gpu.instancing.instancing import InstanceDetector as InstanceDetector
from ornata.gpu.instancing.instancing import InstanceGroup as InstanceGroup
from ornata.gpu.instancing.instancing import InstanceTransform as InstanceTransform
from ornata.gpu.memory import allocator as allocator
from ornata.gpu.memory import residency as residency
from ornata.gpu.memory import staging as staging
from ornata.gpu.memory.allocator import Allocator as Allocator
from ornata.gpu.memory.allocator import BufferStats as BufferStats
from ornata.gpu.memory.residency import MemoryBlock as MemoryBlock
from ornata.gpu.memory.residency import Residency as Residency
from ornata.gpu.memory.residency import ResidencyState as ResidencyState
from ornata.gpu.memory.staging import Staging as Staging
from ornata.gpu.memory.staging import TransferDirection as TransferDirection
from ornata.gpu.memory.staging import TransferRequest as TransferRequest
from ornata.gpu.memory.staging import _coerce_transfer_data as _coerce_transfer_data  #type: ignore
from ornata.gpu.memory.sync import BarrierType as BarrierType
from ornata.gpu.memory.sync import Sync as Sync
from ornata.gpu.memory.sync import SyncPoint as SyncPoint
from ornata.gpu.memory.sync import SyncType as SyncType
from ornata.gpu.misc import (
    Buffer,
    Canvas,
    CompositorBase,
    GPUBackend,
    GPUContext,
    GPUResource,
    PlatformWindow,
    RenderTarget,
    Shader,
    Texture,
    component_to_gui_node,
    create_event_fast,
)
from ornata.gpu.pipelines import compute_pipeline as compute_pipeline
from ornata.gpu.pipelines import graphics_pipeline as graphics_pipeline
from ornata.gpu.pipelines.compute_pipeline import ComputePipeline as ComputePipeline
from ornata.gpu.pipelines.graphics_pipeline import GraphicsPipeline as GraphicsPipeline
from ornata.gpu.programs import compute_program as compute_program
from ornata.gpu.programs import fragment_program as fragment_program
from ornata.gpu.programs import geometry_program as geometry_program
from ornata.gpu.programs import mesh_program as mesh_program
from ornata.gpu.programs import raytracing_programs as raytracing_programs
from ornata.gpu.programs import shader_manager as shader_manager
from ornata.gpu.programs import task_program as task_program
from ornata.gpu.programs import tess_control_program as tess_control_program
from ornata.gpu.programs import tess_eval_program as tess_eval_program
from ornata.gpu.programs import vertex_program as vertex_program
from ornata.gpu.programs.base import ShaderProgramBase as ShaderProgramBase
from ornata.gpu.programs.compute_program import ComputeProgram as ComputeProgram
from ornata.gpu.programs.fragment_program import FragmentProgram as FragmentProgram
from ornata.gpu.programs.fragment_program import load_fragment_program_source as load_fragment_program_source
from ornata.gpu.programs.geometry_program import GeometryProgram as GeometryProgram
from ornata.gpu.programs.mesh_program import MeshProgram as MeshProgram
from ornata.gpu.programs.raytracing_programs import RayClosestHitProgram as RayClosestHitProgram
from ornata.gpu.programs.raytracing_programs import RayGenProgram as RayGenProgram
from ornata.gpu.programs.raytracing_programs import RayMissProgram as RayMissProgram
from ornata.gpu.programs.shader_manager import ShaderManager as ShaderManager
from ornata.gpu.programs.task_program import TaskProgram as TaskProgram
from ornata.gpu.programs.tess_control_program import TessControlProgram as TessControlProgram
from ornata.gpu.programs.tess_eval_program import TessEvalProgram as TessEvalProgram
from ornata.gpu.programs.vertex_program import VertexProgram as VertexProgram
from ornata.gpu.programs.vertex_program import load_vertex_program_source as load_vertex_program_source
from ornata.gpu.resources import (
    GPUBufferHandle as GPUBufferHandle,
)
from ornata.gpu.resources import (
    GPUResourceHandle as GPUResourceHandle,
)
from ornata.gpu.resources import (
    GPUResourceManager as GPUResourceManager,
)
from ornata.gpu.resources import (
    GPUTextureHandle as GPUTextureHandle,
)
from ornata.gpu.resources import (
    create_gpu_buffer as create_gpu_buffer,
)
from ornata.gpu.resources import (
    create_gpu_texture as create_gpu_texture,
)
from ornata.gpu.resources import (
    get_gpu_resource_manager as get_gpu_resource_manager,
)
from ornata.gpu.textures import sampler_state as sampler_state
from ornata.gpu.textures import texture2d as texture2d
from ornata.gpu.textures import texturecube as texturecube
from ornata.gpu.textures.sampler_state import FilterMode as FilterMode
from ornata.gpu.textures.sampler_state import SamplerState as SamplerState
from ornata.gpu.textures.sampler_state import WrapMode as WrapMode
from ornata.gpu.textures.sampler_state import _gl_filter as _gl_filter  #type: ignore
from ornata.gpu.textures.sampler_state import _gl_wrap as _gl_wrap  #type: ignore
from ornata.gpu.textures.texture2d import Texture2D as Texture2D
from ornata.gpu.textures.texturecube import CubeTexture as CubeTexture

__all__ = [
    "Allocator",
    "BarrierType",
    "BatchKey",
    "BatchedGeometry",
    "BlendFactor",
    "BlendOperation",
    "BufferStats",
    "CPUBlitter",
    "CPUFallback",
    "CPUFallbackBatcher",
    "CPUInstancer",
    "Capabilities",
    "ComponentIdentity",
    "ComputePipeline",
    "ComputeProgram",
    "DepthFunction",
    "DeviceManager",
    "DeviceSelector",
    "DirectXBackend",
    "DirectXBufferManager",
    "DirectXContext",
    "DirectXDevice",
    "DirectXInputLayout",
    "DirectXPipeline",
    "DirectXSampler",
    "DirectXShaderCompiler",
    "DirectXSwapChain",
    "DirectXSync",
    "DirectXTexture",
    "FilterMode",
    "FragmentProgram",
    "GPUBuffer",
    "GeometryBatch",
    "GeometryConverter",
    "GeometryProgram",
    "GraphicsPipeline",
    "IndexBuffer",
    "InstanceDetector",
    "InstanceGroup",
    "InstanceTransform",
    "Limits",
    "Matrix4",
    "MemoryBlock",
    "MeshProgram",
    "OpenGLBackend",
    "OpenGLContextManager",
    "OpenGLIBOManager",
    "OpenGLInstancingManager",
    "OpenGLPipelineManager",
    "OpenGLProgramManager",
    "OpenGLShaderCompiler",
    "OpenGLStateManager",
    "OpenGLTextureManager",
    "OpenGLUBOManager",
    "OpenGLVAOManager",
    "OpenGLVBOManager",
    "PersistentBuffer",
    "PipelineConfig",
    "RayClosestHitProgram",
    "RayGenProgram",
    "RayMissProgram",
    "RenderBatcher",
    "Residency",
    "ResidencyState",
    "SamplerState",
    "ShaderManager",
    "ShaderProgramBase",
    "SoftwarePipeline",
    "SoftwareRasterizer",
    "SoftwareShaderProgram",
    "Staging",
    "SwIndexBuffer",
    "SwTexture2D",
    "SwVertexBuffer",
    "Sync",
    "SyncPoint",
    "SyncType",
    "TaskProgram",
    "TessControlProgram",
    "TessEvalProgram",
    "Texture2D",
    "CubeTexture",
    "TransferDirection",
    "TransferRequest",
    "UniformBuffer",
    "VertexBuffer",
    "VertexProgram",
    "WrapMode",
    "_CompiledShader",
    "_coerce_matrix",
    "_coerce_transfer_data",
    "_gl_filter",
    "_gl_wrap",
    "_resolve_blend_factor",
    "allocator",
    "backend",
    "batching",
    "blitter",
    "buffer",
    "buffers",
    "capabilities",
    "check_opengl_error",
    "component_to_gpu_geometry",
    "compute_pipeline",
    "compute_program",
    "context",
    "cpu_fallback",
    "cpu_render",
    "device",
    "directx",
    "fallback",
    "fragment_program",
    "geometry_program",
    "get_device_manager",
    "get_geometry_converter",
    "get_max_texture_size",
    "get_max_viewport_dims",
    "get_opengl_extensions",
    "get_opengl_version",
    "graphics_pipeline",
    "has_opengl_extension",
    "ibo",
    "identity_matrix",
    "index",
    "input_layout",
    "instancing",
    "limits",
    "load_fragment_program_source",
    "load_vertex_program_source",
    "log_opengl_info",
    "look_at_matrix",
    "math",
    "matrix_multiply",
    "memory",
    "mesh_program",
    "ndc_to_screen",
    "opengl",
    "orthographic_matrix",
    "perspective_matrix",
    "pipelines",
    "process_texture_coordinates",
    "program",
    "programs",
    "rasterizer",
    "raytracing_programs",
    "render_with_gpu_acceleration",
    "residency",
    "rotate_x_matrix",
    "rotate_y_matrix",
    "rotate_z_matrix",
    "sampler_state",
    "scale_matrix",
    "screen_to_ndc",
    "selection",
    "shader",
    "shader_compiler",
    "shader_manager",
    "staging",
    "state",
    "sw_buffers",
    "sw_pipeline",
    "sw_textures",
    "swapchain",
    "sync",
    "task_program",
    "tess_control_program",
    "tess_eval_program",
    "texture2d",
    "texturecube",
    "textures",
    "to_ndc_vertices",
    "transform_point",
    "transform_vector",
    "translate_matrix",
    "ubo",
    "uniform",
    "vao",
    "vbo",
    "vector_add",
    "vector_cross",
    "vector_dot",
    "vector_length",
    "vector_normalize",
    "vector_scale",
    "vector_subtract",
    "vertex",
    "vertex_program",
    "viewport_matrix",
    "GPUResource",
    "Shader",
    "Texture",
    "Buffer",
    "RenderTarget",
    "GPUBackend",
    "GPUContext",
    "CompositorBase",
    "PlatformWindow",
    "Canvas",
    "create_event_fast",
    "component_to_gui_node",
]
