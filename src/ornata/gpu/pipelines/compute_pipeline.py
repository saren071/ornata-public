"""Compute pipeline management for GPU compute operations.

This module provides the ComputePipeline class for managing compute shader dispatch,
workgroup configuration, and compute pipeline state across different GPU backends.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.gpu.misc import Shader

logger = get_logger(__name__)


class ComputePipeline:
    """Manages compute pipeline state and shader dispatch operations.

    This class provides a high-level interface for configuring and executing
    compute shaders across different GPU backends, handling workgroup dimensions,
    shader binding, and dispatch operations.
    """

    def __init__(self, backend: Any) -> None:
        """Initialize compute pipeline with GPU backend.

        Args:
            backend: The GPU backend implementation to use for compute operations.
        """
        self._backend = backend
        self._current_shader: Shader | None = None
        self._workgroup_size = (1, 1, 1)
        self._is_bound = False

    def bind_shader(self, shader: Shader) -> None:
        """Bind a compute shader to the pipeline.

        Args:
            shader: The compute shader to bind for dispatch operations.

        Raises:
            GPUPipelineError: If shader binding fails.
        """
        if not shader.compiled:
            from ornata.api.exports.definitions import GPUPipelineError
            raise GPUPipelineError(f"Cannot bind uncompiled shader: {shader.name}")

        try:
            self._current_shader = shader
            self._is_bound = True
            logger.debug(f"Bound compute shader: {shader.name}")
        except Exception as e:
            self._is_bound = False
            from ornata.api.exports.definitions import GPUPipelineError
            raise GPUPipelineError(f"Failed to bind compute shader {shader.name}: {e}") from e

    def set_workgroup_size(self, x: int, y: int = 1, z: int = 1) -> None:
        """Set the workgroup dimensions for compute dispatch.

        Args:
            x: Workgroup size in X dimension.
            y: Workgroup size in Y dimension.
            z: Workgroup size in Z dimension.

        Raises:
            ValueError: If workgroup dimensions are invalid.
        """
        if x <= 0 or y <= 0 or z <= 0:
            raise ValueError("Workgroup dimensions must be positive integers")

        if x * y * z > 1024:  # Conservative limit for most GPUs
            logger.warning(f"Large workgroup size ({x}, {y}, {z}) may not be supported on all GPUs")

        self._workgroup_size = (x, y, z)
        logger.debug(f"Set workgroup size to: {self._workgroup_size}")

    def dispatch(self, groups_x: int, groups_y: int = 1, groups_z: int = 1) -> None:
        """Dispatch compute workgroups for execution.

        Args:
            groups_x: Number of workgroups in X dimension.
            groups_y: Number of workgroups in Y dimension.
            groups_z: Number of workgroups in Z dimension.

        Raises:
            GPUPipelineError: If dispatch fails or no shader is bound.
        """
        if not self._is_bound or self._current_shader is None:
            from ornata.api.exports.definitions import GPUPipelineError
            raise GPUPipelineError("No compute shader bound to pipeline")

        if groups_x <= 0 or groups_y <= 0 or groups_z <= 0:
            raise ValueError("Dispatch dimensions must be positive integers")

        try:
            dispatch_compute = getattr(self._backend, "dispatch_compute", None)
            if callable(dispatch_compute):
                dispatch_compute(self._current_shader, self._workgroup_size, (groups_x, groups_y, groups_z))
                total_workgroups = groups_x * groups_y * groups_z
                logger.debug(
                    "Dispatched %s workgroups with size %s",
                    total_workgroups,
                    self._workgroup_size,
                )
            else:
                from ornata.api.exports.definitions import GPUPipelineError
                raise GPUPipelineError("Backend does not implement compute dispatch")
        except Exception as e:
            from ornata.api.exports.definitions import GPUPipelineError
            raise GPUPipelineError(f"Compute dispatch failed: {e}") from e

    def unbind(self) -> None:
        """Unbind the current compute shader from the pipeline."""
        self._current_shader = None
        self._is_bound = False
        logger.debug("Unbound compute shader from pipeline")

    @property
    def is_bound(self) -> bool:
        """Check if a compute shader is currently bound.

        Returns:
            True if a shader is bound, False otherwise.
        """
        return self._is_bound

    @property
    def current_shader(self) -> Shader | None:
        """Get the currently bound compute shader.

        Returns:
            The bound shader or None if no shader is bound.
        """
        return self._current_shader

    @property
    def workgroup_size(self) -> tuple[int, int, int]:
        """Get the current workgroup size.

        Returns:
            Tuple of (x, y, z) workgroup dimensions.
        """
        return self._workgroup_size