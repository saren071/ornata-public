"""Ensure every API export module resolves its public symbols."""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest

EXPORT_PACKAGE = "ornata.api.exports"
KNOWN_BROKEN_EXPORTS: dict[str, set[str]] = {
    f"{EXPORT_PACKAGE}.definitions": {"BEL"},
}


def _resolve_package_path(package: object) -> Path:
    path_attr = getattr(package, "__file__", None)
    if path_attr:
        return Path(path_attr).resolve().parent
    search_locations = getattr(package, "__path__", None)
    if search_locations:
        return Path(next(iter(search_locations))).resolve()
    raise RuntimeError(f"Unable to resolve path for package {package!r}")


def _iter_export_module_names() -> list[str]:
    package = importlib.import_module(EXPORT_PACKAGE)
    package_path = _resolve_package_path(package)
    module_names: list[str] = []
    for child in package_path.iterdir():
        if child.name.startswith("__") or child.name.endswith(".pyi"):
            continue
        if child.is_dir():
            module_names.append(f"{EXPORT_PACKAGE}.{child.name}")
        elif child.suffix == ".py":
            module_names.append(f"{EXPORT_PACKAGE}.{child.stem}")
    return sorted(module_names)


def _discover_export_names(module: object) -> list[str]:
    names: list[str] = []
    targets = module.__dict__.get("_EXPORT_TARGETS")
    if isinstance(targets, dict):
        names.extend(targets.keys())
    else:
        all_attr = module.__dict__.get("__all__")
        if isinstance(all_attr, (list, tuple, set)):
            names.extend(all_attr)
        else:
            names.extend(name for name in dir(module) if not name.startswith("_"))
    return sorted(set(names))


def _handle_resolution_failure(module_name: str, name: str, error: Exception) -> None:
    broken = KNOWN_BROKEN_EXPORTS.get(module_name)
    if broken and name in broken:
        pytest.xfail(f"{module_name}.{name} known broken: {error}")
    raise


@pytest.mark.parametrize("module_name", _iter_export_module_names())
def test_api_exports_resolve(module_name: str) -> None:
    """All exported names resolve without AttributeError."""
    module = importlib.import_module(module_name)
    export_names = _discover_export_names(module)
    assert export_names, f"{module_name} exposes no exports"
    for name in export_names:
        try:
            getattr(module, name)
        except Exception as error:  # noqa: BLE001
            _handle_resolution_failure(module_name, name, error)
