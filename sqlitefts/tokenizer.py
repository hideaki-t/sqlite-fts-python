# coding: utf-8
"""
a proof of concept implementation of SQLite FTS tokenizers in Python
"""
import sys
from ctypes.util import find_library
from importlib import import_module

from cffi import FFI  # type: ignore

SQLITE_OK = 0
SQLITE_DONE = 101

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

_mod_cache = {}


def _get_dll(name):
    try:
        if name != None:
            f = import_module(name).__file__
        else:
            f = None
    except:  # noqa
        # python2 ImportError, Python 3 ModuleNotFoundError
        f = None
    f = find_library("sqlite3")
    if not f:
        raise Exception("unable to find SQLite shared object")
    dll = _mod_cache.get(f)
    if not dll:
        dll = ffi.dlopen(f)
        try:
            dll.sqlite3_libversion_number()
        except AttributeError:
            # likely APSW
            dll = _get_dll(None)
        _mod_cache[f] = dll
    return dll


def get_db_from_connection(c):
    db = getattr(c, "_db", None)
    if db:
        # pypy's SQLite3 connection has _db using cffi
        return ffi.cast("sqlite3*", db), _get_dll("_sqlite3_cffi")
    return ffi.cast("PyObject *", id(c)).db, _get_dll("_sqlite3")


__all__ = ["SQLITE_OK", "SQLITE_DONE"]
