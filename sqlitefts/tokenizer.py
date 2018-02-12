# coding: utf-8
'''
a proof of concept implementation of SQLite FTS tokenizers in Python
'''
from __future__ import print_function, unicode_literals

import sys
import ctypes

from cffi import FFI

SQLITE_OK = 0
SQLITE_DONE = 101

ffi = FFI()

if sys.platform == 'win32':
    dll = ffi.dlopen("sqlite3.dll")
else:
    from ctypes.util import find_library
    dll = ffi.dlopen(find_library("sqlite3"))

if hasattr(ctypes, 'pythonapi') and \
    hasattr(ctypes.pythonapi, '_Py_PrintReferences'):
    # for a python built with Py_TRACE_REFS
    ffi.cdef('''
typedef struct sqlite3 sqlite3;
typedef struct {
  void *_ob_next;
  void *_ob_prev;
  size_t ob_refcnt;
  void *ob_type;
  sqlite3 *db;
} PyObject;
''')
else:
    ffi.cdef('''
typedef struct sqlite3 sqlite3;
typedef struct {
  size_t ob_refcnt;
  void *ob_type;
  sqlite3 *db;
} PyObject;
''')


def get_db_from_connection(c):
    db = getattr(c, '_db', None)
    if db:
        # pypy's SQLite3 connection has _db using cffi
        db = ffi.cast('sqlite3*', db)
    else:
        db = ffi.cast('PyObject *', id(c)).db
    return db
