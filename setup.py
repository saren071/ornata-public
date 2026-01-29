#!/usr/bin/env python3
# Type: ignore is allowed here due to cython being untyped
"""
Setup script for Ornata with Cython extensions.
"""

import sys

from Cython.Build.Dependencies import cythonize  # type: ignore [assignment]
from setuptools import Extension, setup

# Cython extensions to build
extensions = [
    Extension(
        "ornata.optimization.cython.vdom_diff",
        sources=["src/ornata/optimization/cython/vdom_diff.pyx"],
        include_dirs=[],
        define_macros=[("CYTHON_TRACE", "0")],
    ),
]
# Platform-specific optimizations
if sys.platform == "win32":
    # Windows-specific optimizations (DirectX-ready)
    for ext in extensions:
        ext.extra_compile_args = ["/O2", "/GL"]
        ext.extra_link_args = ["/LTCG"]
# Cythonize extensions with optimizations
cython_extensions = cythonize( # type: ignore [assignment]
    extensions,
    compiler_directives={
        "language_level": 3,
        "boundscheck": False,
        "wraparound": False,
        "initializedcheck": False,
        "nonecheck": False,
        "overflowcheck": False,
        "embedsignature": True,
        "freethreading_compatible": True,  # Enable free-threading support
    },
    build_dir="build",
)

if __name__ == "__main__":
    setup(
        ext_modules=cython_extensions,  # type: ignore [assignment]
    )
