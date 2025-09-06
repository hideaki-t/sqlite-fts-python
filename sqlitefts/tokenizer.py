# coding: utf-8
"""
a proof of concept implementation of SQLite FTS tokenizers in Python
"""

import sys
import sysconfig

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

if sysconfig.get_config_var("Py_GIL_DISABLED") == 1:
    ffi.cdef(
        """
typedef struct sqlite3 sqlite3;
typedef struct {
  uintptr_t ob_tid;
  uint16_t _padding;
  uint8_t ob_mutex;
  uint8_t ob_gc_bits;
  uint32_t ob_ref_local;
  ssize_t ob_ref_shared;
  void *ob_type;
  sqlite3 *db;
} PyObject;
"""
    )
elif hasattr(sys, "getobjects"):
    # for a python built with Py_TRACE_REFS
    ffi.cdef(
        """
typedef struct sqlite3 sqlite3;
typedef struct {
  union {
    ssize_t ob_refcnt;
    uint32_t ob_refcnt_split[2];
  };
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
