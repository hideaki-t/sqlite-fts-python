# coding: utf-8
"""
a proof of concept implementation of SQLite FTS tokenizers in Python
"""
import sys

from cffi import FFI  # type: ignore

SQLITE_OK = 0
SQLITE_DONE = 101

ffi = FFI()

if sys.platform == "win32":
    import sqlite3  # noqa

    dll = ffi.dlopen("sqlite3.dll")
else:
    from ctypes.util import find_library

    try:
        # try to use _sqlite3.so first
        import _sqlite3  # noqa

        dll = ffi.dlopen(_sqlite3.__file__)
    except:
        dll = ffi.dlopen(find_library("sqlite3"))

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
ffi.cdef(
    """
int sqlite3_initialize(void);
"""
)

assert dll.sqlite3_initialize() == SQLITE_OK


def get_db_from_connection(c):
    db = getattr(c, "_db", None)
    if db:
        # pypy's SQLite3 connection has _db using cffi
        db = ffi.cast("sqlite3*", db)
    else:
        db = ffi.cast("PyObject *", id(c)).db
    return db


__all__ = ["get_db_from_connection", "SQLITE_OK", "SQLITE_DONE"]
