# coding: utf-8
'''
a proof of concept implementation of SQLite FTS tokenizers in Python
'''
from __future__ import print_function, unicode_literals
import sys

from cffi import FFI

SQLITE_OK = 0
SQLITE_DONE = 101

ffi = FFI()
ffi.cdef('''
typedef struct sqlite3 sqlite3;
int sqlite3_db_config(sqlite3 *, int, ...);

/*
this structure completely depends on the definition of pysqlite_Connection and
PyObject_HEAD. this won't work if
Py_TRACE_REFS is enabled
AND/OR
the definition of "sqlite3* db" in pysqlite_Connection is changed/moved
*/
typedef struct {
  size_t ob_refcnt;
  void *ob_type;
  sqlite3 *db;
} PyObject;
''')

if sys.platform == 'win32':
    dll = ffi.dlopen('sqlite3.dll')
else:
    from ctypes.util import find_library
    dll = ffi.dlopen(find_library('sqlite3'))


def get_db_from_connection(c):
    db = getattr(c, '_db', None)
    if db:
        # pypy's SQLite3 connection has _db using cffi
        db = ffi.cast('sqlite3*', db)
    else:
        db = ffi.cast('PyObject *', id(c)).db
    return db
