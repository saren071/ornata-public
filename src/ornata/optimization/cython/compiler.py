"""Cython compilation utilities for event system optimization."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from ornata.api.exports.definitions import CythonCompilationError
from ornata.api.exports.utils import get_logger

logger = get_logger(__name__)


def compile_cython_extensions(build_dir: str | None = None) -> bool:
    """Compile all Cython extensions for the event system.

    Args:
        build_dir: Optional directory for build artifacts.

    Returns:
        bool: True if compilation successful.

    Raises:
        CythonCompilationError: If compilation fails.
    """
    try:
        # Use the setup.py script to build extensions
        setup_path = Path(__file__).parent / "setup.py"
        if not setup_path.exists():
            raise CythonCompilationError(f"Setup script not found: {setup_path}")

        cmd = [sys.executable, str(setup_path), "build_ext", "--inplace"]
        if build_dir:
            cmd.extend(["--build-lib", build_dir])

        logger.debug(f"Running Cython compilation: {' '.join(cmd)}")
        subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
            check=True
        )

        logger.info("Cython extensions compiled successfully")
        return True

    except subprocess.CalledProcessError as e:
        error_msg = f"Cython compilation failed: {e.stderr}"
        logger.error(error_msg)
        raise CythonCompilationError(error_msg) from e
    except Exception as e:
        error_msg = f"Unexpected error during Cython compilation: {e}"
        logger.error(error_msg)
        raise CythonCompilationError(error_msg) from e


def check_cython_available() -> bool:
    """Check if Cython is available for compilation.

    Returns:
        bool: True if Cython is available.
    """
    try:
        import importlib
        importlib.import_module("Cython")
        logger.debug("Cython available")
        return True
    except ImportError:
        logger.warning("Cython not available - using Python fallbacks")
        return False


def get_extension_suffix() -> str:
    """Get the appropriate extension suffix for compiled modules.

    Returns:
        str: File extension (.so or .pyd).
    """
    return ".pyd"


__all__ = [
    "CythonCompilationError",
    "compile_cython_extensions",
    "check_cython_available",
    "get_extension_suffix",
]