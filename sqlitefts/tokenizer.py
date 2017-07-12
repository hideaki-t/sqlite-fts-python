# coding: utf-8
"""
a proof of concept implementation of SQLite FTS tokenizers in Python
"""
from __future__ import print_function, unicode_literals

import sys
import struct

from cffi import FFI

from . import Error

SQLITE_OK = 0
SQLITE_DONE = 101
SQLITE_Fts3Tokenizer = 0x40000000

if sys.version_info.major == 2:
    global buffer
else:
    buffer = lambda x: x

ffi = FFI()
ffi.cdef('''
typedef struct sqlite3_vfs sqlite3_vfs;
typedef struct sqlite3_mutex sqlite3_mutex;
struct Vdbe;
typedef struct CollSeq CollSeq;
typedef struct Db Db;

typedef struct sqlite3 {
  sqlite3_vfs *pVfs;
  struct Vdbe *pVdbe;
  CollSeq *pDfltColl;
  sqlite3_mutex *mutex;
  Db *aDb;
  int nDb;
  int flags;
} sqlite3;

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

typedef struct sqlite3_tokenizer_module sqlite3_tokenizer_module;
typedef struct sqlite3_tokenizer sqlite3_tokenizer;
typedef struct sqlite3_tokenizer_cursor sqlite3_tokenizer_cursor;
struct sqlite3_tokenizer_module {
  int iVersion;
  int (*xCreate)(
    int argc, const char *const*argv, sqlite3_tokenizer **ppTokenizer);
  int (*xDestroy)(sqlite3_tokenizer *pTokenizer);
  int (*xOpen)(
    sqlite3_tokenizer *pTokenizer, const char *pInput, int nBytes,
    sqlite3_tokenizer_cursor **ppCursor);
  int (*xClose)(sqlite3_tokenizer_cursor *pCursor);
  int (*xNext)(
    sqlite3_tokenizer_cursor *pCursor, const char **ppToken, int *pnBytes,
    int *piStartOffset, int *piEndOffset, int *piPosition);
  int (*xLanguageid)(sqlite3_tokenizer_cursor *pCsr, int iLangid);
};

struct sqlite3_tokenizer {
  const sqlite3_tokenizer_module *pModule;
  void *t;
};

struct sqlite3_tokenizer_cursor {
  sqlite3_tokenizer *pTokenizer;
  void *tokens;
  size_t pos;
  size_t offset;
};
''')


def f():
    def enable_fts3_tokenizer(c):
        db = getattr(c, '_db', None)
        if db:
            # pypy's SQLite3 connection has _db using cffi
            db = ffi.cast('sqlite3*', db)
        else:
            db = ffi.cast('PyObject *', id(c)).db
        db.flags |= SQLITE_Fts3Tokenizer

    return enable_fts3_tokenizer


enable_fts3_tokenizer = f()
del f


class Tokenizer:
    """ Tokenizer base class """

    def tokenize(text):
        """
        Tokenize given unicode text. Yields each tokenized token,
        start position(in bytes), end positon(in bytes)
        """
        yield text, 0, len(text.encode('utf-8'))


tokenizer_modules = {}
"""hold references to prevent GC"""


def make_tokenizer_module(tokenizer):
    """ make tokenizer module """
    if tokenizer in tokenizer_modules:
        return tokenizer_modules[tokenizer]

    t = ffi.new_handle(tokenizer)
    tokenizers = {}
    cursors = {}

    @ffi.callback('int(int, const char *const*, sqlite3_tokenizer **)')
    def xcreate(argc, argv, ppTokenizer):
        tkn = ffi.new('sqlite3_tokenizer *')
        tkn.t = t
        tokenizers[int(ffi.cast('intptr_t', tkn))] = tkn
        ppTokenizer[0] = tkn
        return SQLITE_OK

    @ffi.callback('int(sqlite3_tokenizer *)')
    def xdestroy(pTokenizer):
        del tokenizers[int(ffi.cast('intptr_t', pTokenizer))]
        return SQLITE_OK

    @ffi.callback(
        'int(sqlite3_tokenizer*, const char *, int, sqlite3_tokenizer_cursor **)'
    )
    def xopen(pTokenizer, pInput, nInput, ppCursor):
        cur = ffi.new('sqlite3_tokenizer_cursor *')
        tokenizer = ffi.from_handle(pTokenizer.t)
        tokens = tokenizer.tokenize(ffi.string(pInput).decode('utf-8'))
        tknh = ffi.new_handle(tokens)
        cur.pTokenizer = pTokenizer
        cur.tokens = tknh
        cur.pos = 0
        cur.offset = 0
        cursors[int(ffi.cast('intptr_t', cur))] = cur, tknh
        ppCursor[0] = cur
        return SQLITE_OK

    @ffi.callback(
        'int(sqlite3_tokenizer_cursor*, const char **, int *, int *, int *, int *)'
    )
    def xnext(pCursor, ppToken, pnBytes, piStartOffset, piEndOffset,
              piPosition):
        try:
            cur = pCursor[0]
            tokens = ffi.from_handle(cur.tokens)
            while True:
                normalized, inputBegin, inputEnd = next(tokens)
                normalized = normalized.encode('utf-8')
                if normalized:
                    break

            ppToken[0] = ffi.from_buffer(normalized)
            pnBytes[0] = len(normalized)
            piStartOffset[0] = inputBegin
            piEndOffset[0] = inputEnd
            cur.offset = inputEnd
            piPosition[0] = cur.pos
            cur.pos += 1
        except StopIteration:
            return SQLITE_DONE
        return SQLITE_OK

    @ffi.callback('int(sqlite3_tokenizer_cursor *)')
    def xclose(pCursor):
        del cursors[int(ffi.cast('intptr_t', pCursor))]
        return SQLITE_OK

    tokenizer_module = ffi.new("sqlite3_tokenizer_module *",
                               [0, xcreate, xdestroy, xopen, xclose, xnext])
    tokenizer_modules[tokenizer] = (xcreate, xdestroy, xopen, xclose, xnext)
    return tokenizer_module


def register_tokenizer(c, name, tokenizer_module):
    """ register tokenizer module with SQLite connection. """
    module_addr = int(ffi.cast('uintptr_t', tokenizer_module))
    address_blob = buffer(struct.pack("P", module_addr))
    enable_fts3_tokenizer(c)
    cur = c.cursor()
    try:
        r = cur.execute('SELECT fts3_tokenizer(?, ?)',
                        (name, address_blob)).fetchall()
        tokenizer_modules[module_addr] = tokenizer_module
    finally:
        cur.close()
    return r
