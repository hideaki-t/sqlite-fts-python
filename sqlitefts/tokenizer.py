# coding: utf-8
"""
a proof of concept implementation of SQLite FTS tokenizers in Python
"""
import sys

from .error import Error
from cffi import FFI  # type: ignore

SQLITE_OK = 0
SQLITE_DONE = 101

ffi = FFI()

if sys.platform == "win32":
    import sqlite3  # noqa

    dll = ffi.dlopen("sqlite3.dll")
else:

    def get_dll():
        from ctypes.util import find_library
        from ctypes import CDLL
        import _sqlite3  # noqa

        so = getattr(_sqlite3, "__file__", find_library("sqlite3"))
        if so is None:
            raise Error("no sqlite3 lib found")
        cdll = CDLL(so)
        if not hasattr(cdll, "sqlite3_initialize"):
            raise Error("required symbols not found in " + so)
        cdll.sqlite3_initialize()
        return ffi.dlopen(so)

    dll = get_dll()
    del get_dll

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


def get_db_from_connection(c):
    db = getattr(c, "_db", None)
    if db:
        # pypy's SQLite3 connection has _db using cffi
        db = ffi.cast("sqlite3*", db)
    else:
        db = ffi.cast("PyObject *", id(c)).db
    return db


__all__ = ["get_db_from_connection", "SQLITE_OK", "SQLITE_DONE"]
