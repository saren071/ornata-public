# ornata/interop/ctypes_compilation/windows/com.py
"""COM interface helpers used by the Windows bindings."""

from __future__ import annotations

import ctypes as ct
from typing import TYPE_CHECKING, Any

from ornata.interop.ctypes_compilation.windows.foundation import (
    GUID,
    HRESULT,
    LPVOID,
    UINT,
    WindowsLibraryError,
    ensure_windows,
    to_int,
)

if TYPE_CHECKING:
    from collections.abc import Callable


class IUnknownVTable(ct.Structure):
    """Subset of the IUnknown vtable that every COM interface shares."""

    _fields_ = [
        ("QueryInterface", ct.WINFUNCTYPE(HRESULT, LPVOID, ct.POINTER(GUID), ct.POINTER(LPVOID))),
        ("AddRef", ct.WINFUNCTYPE(UINT, LPVOID)),
        ("Release", ct.WINFUNCTYPE(UINT, LPVOID)),
    ]


class IUnknown(ct.Structure):
    """Base COM interface wrapper providing Python-friendly helpers."""

    _fields_ = [("lpVtbl", ct.POINTER(IUnknownVTable))]

    def query_interface(self, iid: GUID) -> LPVOID:
        """Query for another interface on the same COM object."""
        ensure_windows()
        ppv = LPVOID()
        hr = self.lpVtbl.contents.QueryInterface(ct.byref(self), ct.byref(iid), ct.byref(ppv))
        if hr < 0:
            raise OSError(hr, "QueryInterface failed")
        return ppv

    def add_ref(self) -> int:
        """Increment the COM reference count."""
        ensure_windows()
        return int(self.lpVtbl.contents.AddRef(ct.byref(self)))

    def release(self) -> int:
        """Decrement the COM reference count."""
        ensure_windows()
        return int(self.lpVtbl.contents.Release(ct.byref(self)))


class COMPointer:
    """Lightweight helper that owns a single COM pointer value."""

    def __init__(self, pointer: int | ct.c_void_p | None = None) -> None:
        self._pointer = ct.c_void_p()
        if pointer is not None:
            self.assign(pointer)

    def assign(self, pointer: int | ct.c_void_p) -> None:
        """Assign the internal pointer value."""
        if isinstance(pointer, ct.c_void_p):
            value = pointer.value or 0
        else:
            value = int(pointer)
        self._pointer = ct.c_void_p(value)

    @property
    def pointer(self) -> ct.c_void_p:
        """Return the pointer as ``ctypes.c_void_p``."""
        return self._pointer

    def release(self) -> int:
        """Decrement COM refcount via IUnknown.Release if available."""
        if self.is_null():
            return 0
        addr = ct.cast(self._pointer, ct.c_void_p).value
        if addr is None:
            return 0
        return IUnknown.from_address(addr).release()

    def address(self) -> int:
        """Return the raw pointer address as an integer."""
        return int(self._pointer.value or 0)

    def is_null(self) -> bool:
        """Return ``True`` when the pointer is ``NULL``."""
        return self.address() == 0

    def out_param(self) -> Any:
        """Provide a ``void**`` for use with COM out parameters."""
        self._pointer = ct.c_void_p()
        return ct.byref(self._pointer)

    def __bool__(self) -> bool:  # pragma: no cover - tiny helper
        return not self.is_null()

    @classmethod
    def from_address(cls, pointer: int | ct.c_void_p | None) -> COMPointer:
        """Create a wrapper from an existing pointer."""
        return cls(pointer or 0)


class COMInterface(COMPointer):
    """Generic COM vtable invoker based on an index + signature table."""

    _methods_: dict[str, tuple[int, type | None, tuple[type, ...]]] = {}
    _prototype_cache: dict[tuple[int, type | None, tuple[type, ...]], Callable[..., Any]] = {}
    _lock = __import__("threading").RLock()

    def _invoke_raw(
        self,
        index: int,
        restype: type | None,
        argtypes: tuple[type, ...],
        *args: Any,
    ) -> Any:
        with self._lock:
            if self.is_null():
                raise WindowsLibraryError("COM interface pointer is NULL")

            ptr_val = to_int(self.pointer)
            print(f"DEBUG: _invoke_raw index={index} ptr={ptr_val:#x}")
            if ptr_val < 0x1000:  # Heuristic for invalid address
                raise WindowsLibraryError(f"COM interface pointer is invalid: {ptr_val:#x}")

            vtbl_ptr = ct.cast(self.pointer, ct.POINTER(ct.POINTER(ct.c_void_p)))
            try:
                vtable = vtbl_ptr.contents
                vtbl_addr = to_int(vtable)
                if vtbl_addr < 0x1000:
                    raise WindowsLibraryError(f"COM interface vtable pointer is invalid: {vtbl_addr:#x} for ptr {ptr_val:#x}")

                func_addr_obj: Any = vtable[index]
                addr_int = to_int(getattr(func_addr_obj, "value", func_addr_obj) or 0)
                # print(f"DEBUG: func_addr={addr_int:#x}")
            except Exception as e:
                raise WindowsLibraryError(f"Failed to access vtable at index {index} for ptr {ptr_val:#x}: {e}") from e

            prototype_key = (index, restype, argtypes)
            try:
                prototype: Callable[..., Any] = self._prototype_cache[prototype_key]
            except KeyError:
                if restype is None:
                    prototype = ct.WINFUNCTYPE(None, ct.c_void_p, *argtypes)
                else:
                    prototype = ct.WINFUNCTYPE(restype, ct.c_void_p, *argtypes)
                self._prototype_cache[prototype_key] = prototype

            func: Callable[..., Any] = prototype(addr_int)
            print(f"DEBUG: Calling func={addr_int:#x} index={index} with ptr={ptr_val:#x} args_len={len(args)}")
            return func(self.pointer, *args)

    def _invoke(self, name: str, *args: Any) -> Any:
        index, restype, argtypes = self._methods_[name]
        print(f"DEBUG: _invoke name={name} index={index}")
        result = self._invoke_raw(index, restype, argtypes, *args)
        return to_int(result, restype)

    def add_ref(self) -> int:
        """Increment the COM reference count."""
        return int(self._invoke_raw(1, UINT, ()))

    def release(self) -> int:
        """Decrement the COM reference count."""
        ptr_val = to_int(self.pointer)
        print(f"DEBUG: Releasing COM object {self.__class__.__name__} at {ptr_val:#x}")
        return int(self._invoke_raw(2, UINT, ()))


def declare_interface(name: str, methods: list[tuple[str, Any]]) -> type:
    """Factory to declare a COM interface subclass with a partial vtable."""
    ensure_windows()

    class _VTable(ct.Structure):
        _base_fields = list(IUnknownVTable._fields_)
        extra_fields: list[tuple[str, Any]] = [(mname, proto) for mname, proto in methods]
        _base_fields.extend(extra_fields)
        _fields_ = _base_fields

    class _Interface(IUnknown):
        _fields_ = [("lpVtbl", ct.POINTER(_VTable))]

        @classmethod
        def method(cls, method_name: str) -> Callable[..., Any]:
            try:
                return getattr(_VTable, method_name)
            except AttributeError as exc:
                raise AttributeError(f"{cls.__name__} does not expose {method_name}") from exc

        def call(self, method_name: str, *args: Any) -> Any:
            func = getattr(self.lpVtbl.contents, method_name)
            return func(ct.byref(self), *args)

    _Interface.__name__ = name
    return _Interface


__all__ = [
    "COMInterface",
    "COMPointer",
    "GUID",
    "HRESULT",
    "IUnknown",
    "IUnknownVTable",
    "declare_interface",
]
