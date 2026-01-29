"""Smoke tests that ensure every Ornata module imports successfully."""
from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from types import ModuleType
from typing import Iterator

import pytest

PACKAGE_NAME = "ornata"
PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "src" / PACKAGE_NAME


def _iter_package_modules(package_name: str) -> Iterator[str]:
    """Yield dotted module names for every module under the given package."""
    package = importlib.import_module(package_name)
    if not hasattr(package, "__path__"):
        yield package_name
        return

    for module_info in pkgutil.walk_packages(package.__path__, prefix=f"{package_name}."):
        yield module_info.name


def _load_module(name: str) -> ModuleType:
    """Import a module by name and return it."""
    return importlib.import_module(name)


@pytest.mark.parametrize("module_name", sorted(_iter_package_modules(PACKAGE_NAME)))
def test_import_all_modules(module_name: str) -> None:
    """Import every module to ensure import-time errors are caught early."""
    module = _load_module(module_name)
    assert isinstance(module, ModuleType)
