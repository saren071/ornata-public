"""Auto-generated exports for ornata.gpu.backends.directx."""

from __future__ import annotations

from . import backend, buffer, context, device, input_layout, pipeline, sampler, shader_compiler, swapchain, sync, texture, utils
from .backend import DirectXBackend
from .buffer import DirectXBufferManager
from .context import (
    DirectXContext,
)
from .device import DirectXDevice
from .input_layout import DirectXInputLayout
from .pipeline import DirectXPipeline
from .sampler import DirectXSampler
from .shader_compiler import DirectXShaderCompiler
from .swapchain import DirectXSwapChain
from .sync import DirectXSync
from .texture import DirectXTexture
from .utils import (
    get_clear_color,
    get_default_viewport,
    get_instance_stride,
    get_vertex_stride,
    to_ndc_vertices,
)

__all__ = [
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
    "backend",
    "buffer",
    "context",
    "device",
    "get_clear_color",
    "get_default_viewport",
    "get_instance_stride",
    "get_vertex_stride",
    "input_layout",
    "pipeline",
    "sampler",
    "shader_compiler",
    "swapchain",
    "sync",
    "texture",
    "to_ndc_vertices",
    "utils",
]
