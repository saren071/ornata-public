"""Type stubs for the cli subsystem exports."""

from __future__ import annotations

from ornata.cli.main import build_parser as build_parser
from ornata.cli.main import main as main

__all__ = [
    "build_parser",
    "main",
]