# coding: utf-8
"""
a proof of concept implementation of SQLite FTS tokenizers in Python
"""
from __future__ import print_function, unicode_literals

import sys
import struct

from cffi import FFI

SQLITE_OK = 0
SQLITE_DONE = 101

if sys.version_info.major == 2:
    global buffer
else:
    buffer = lambda x: x

ffi = FFI()
ffi.cdef('''
typedef struct sqlite3 sqlite3;
int sqlite3_db_config(sqlite3 *, int op, ...);

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
    dll = ffi.dlopen("sqlite3.dll")
else:
    from ctypes.util import find_library
    dll = ffi.dlopen(find_library("sqlite3"))


def f():
    SQLITE_DBCONFIG_ENABLE_FTS3_TOKENIZER = 1004

    def enable_fts3_tokenizer(c):
        db = getattr(c, '_db', None)
        if db:
            # pypy's SQLite3 connection has _db using cffi
            db = ffi.cast('sqlite3*', db)
        else:
            db = ffi.cast('PyObject *', id(c)).db
        rc = dll.sqlite3_db_config(db, SQLITE_DBCONFIG_ENABLE_FTS3_TOKENIZER,
                                   ffi.cast('int', 1), ffi.NULL)
        return rc == 0

    return enable_fts3_tokenizer


enable_fts3_tokenizer = f()
del f


def register_tokenizer(c, name, tokenizer_module):
    """ register tokenizer module with SQLite connection. """
    module_addr = int(ffi.cast('uintptr_t', tokenizer_module))
    address_blob = buffer(struct.pack("P", module_addr))
    enable_fts3_tokenizer(c)
    r = c.execute('SELECT fts3_tokenizer(?, ?)', (name, address_blob))
    return r
