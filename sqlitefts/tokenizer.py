# coding: utf-8
"""
a proof of concept implementation of SQLite FTS tokenizers in Python
"""
from __future__ import annotations

import sqlite3
import sys
from ctypes.util import find_library
from importlib import import_module
from typing import Any

from _cffi_backend import Lib as cffi_lib
from cffi import FFI

from .error import Error

SQLITE_OK = 0
SQLITE_DONE = 101
SQLITE_ERROR = 1

ffi = FFI()
ffi.cdef("int sqlite3_libversion_number(void);")
if hasattr(sys, "getobjects"):
    # for a python built with Py_TRACE_REFS
    ffi.cdef(
        """
typedef struct sqlite3 sqlite3;
typedef struct {
  void *_ob_next;
  void *_ob_prev;
  size_t ob_refcnt;
  void *ob_type;
  sqlite3 *db;
} PyObject;
"""
    )
else:
    ffi.cdef(
        """
typedef struct sqlite3 sqlite3;
typedef struct {
  size_t ob_refcnt;
  void *ob_type;
  sqlite3 *db;
} PyObject;
"""
    )

_mod_cache: dict[str, cffi_lib] = {}

if sys.platform == "win32":

    def _get_dll(_):
        import sqlite3  # noqa

        dll = _mod_cache.get("sqlite3.dll")
        if not dll:
            _mod_cache["sqlite3.dll"] = dll = ffi.dlopen("sqlite3.dll")
        return dll

else:

    def _get_dll(name: str) -> cffi_lib:
        try:
            f = import_module(name).__file__
        except ModuleNotFoundError:
            f = find_library("sqlite3")
        if not f:
            raise Exception("unable to find SQLite shared object")
        dll = _mod_cache.get(f)
        if not dll:
            dll = ffi.dlopen(f)
            try:
                dll.sqlite3_libversion_number()  # type: ignore
            except AttributeError as exc:
                raise Error(f"{f} does not expose SQLite API") from exc

            _mod_cache[f] = dll
        return dll


def get_db_from_connection(c: sqlite3.Connection) -> tuple[Any, cffi_lib]:
    _db = getattr(c, "_db", None)
    if _db:
        # pypy's SQLite3 connection has _db using cffi
        return ffi.cast("sqlite3*", _db), _get_dll("_sqlite3_cffi")
    return ffi.cast("PyObject *", id(c)).db, _get_dll("_sqlite3")  # type: ignore


__all__ = ["SQLITE_OK", "SQLITE_DONE", "SQLITE_ERROR", "ffi"]
