# coding: utf-8
'''
support library to write SQLite FTS3 tokenizer
'''
from __future__ import print_function, unicode_literals
import sys
import struct
import warnings

from .tokenizer import (ffi, dll, get_db_from_connection, SQLITE_OK,
                        SQLITE_DONE)
from .error import Error

SQLITE_DBCONFIG_ENABLE_FTS3_TOKENIZER = 1004

ffi.cdef('''
int sqlite3_db_config(sqlite3 *, int op, ...);

typedef struct sqlite3_tokenizer_module sqlite3_tokenizer_module;
typedef struct sqlite3_tokenizer sqlite3_tokenizer;
typedef struct sqlite3_tokenizer_cursor sqlite3_tokenizer_cursor;
struct sqlite3_tokenizer_module {
  int iVersion;
  int (*xCreate)(int, const char*const*, sqlite3_tokenizer**);
  int (*xDestroy)(sqlite3_tokenizer*);
  int (*xOpen)(
    sqlite3_tokenizer*, const char*, int, sqlite3_tokenizer_cursor**);
  int (*xClose)(sqlite3_tokenizer_cursor*);
  int (*xNext)(
    sqlite3_tokenizer_cursor*, const char**, int*, int*, int*, int*);
  int (*xLanguageid)(sqlite3_tokenizer_cursor*, int);
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


class Tokenizer(object):
    '''
    Tokenizer base class.
    '''

    def tokenize(text):
        '''
        Tokenize given unicode text. Yields each tokenized token,
        start position(in bytes), end positon(in bytes)
        '''
        yield text, 0, len(text.encode('utf-8'))


tokenizer_modules = {}
'''hold references to prevent GC'''


def make_tokenizer_module(tokenizer):
    '''tokenizer module'''
    tokenizers = {}
    cursors = {}

    @ffi.callback('int(int, const char *const*, sqlite3_tokenizer **)')
    def xcreate(argc, argv, ppTokenizer):
        if hasattr(tokenizer, '__call__'):
            args = [ffi.string(x).decode('utf-8') for x in argv[0:argc]]
            tk = tokenizer(args)
        else:
            tk = tokenizer
        th = ffi.new_handle(tk)
        tkn = ffi.new('sqlite3_tokenizer *')
        tkn.t = th
        tokenizers[tkn] = th
        ppTokenizer[0] = tkn
        return SQLITE_OK

    @ffi.callback('int(sqlite3_tokenizer *)')
    def xdestroy(pTokenizer):
        tkn = pTokenizer
        del tokenizers[tkn]
        return SQLITE_OK

    @ffi.callback(
        'int(sqlite3_tokenizer*, const char *, int, sqlite3_tokenizer_cursor **)'
    )
    def xopen(pTokenizer, pInput, nInput, ppCursor):
        cur = ffi.new('sqlite3_tokenizer_cursor *')
        tokenizer = ffi.from_handle(pTokenizer.t)
        i = ffi.string(pInput).decode('utf-8')
        tokens = [(n.encode('utf-8'), b, e)
                  for n, b, e in tokenizer.tokenize(i) if n]
        tknh = ffi.new_handle(iter(tokens))
        cur.pTokenizer = pTokenizer
        cur.tokens = tknh
        cur.pos = 0
        cur.offset = 0
        cursors[cur] = tknh
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
            normalized, inputBegin, inputEnd = next(tokens)
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
        tk = ffi.from_handle(pCursor.pTokenizer.t)
        on_close = getattr(tk, 'on_close', None)
        if on_close and hasattr(on_close, '__call__'):
            on_close()

        del cursors[pCursor]
        return SQLITE_OK

    tokenizer_module = ffi.new('sqlite3_tokenizer_module*',
                               [0, xcreate, xdestroy, xopen, xclose, xnext])
    tokenizer_modules[tokenizer] = (tokenizer_module, xcreate, xdestroy, xopen,
                                    xclose, xnext)
    return tokenizer_module


def enable_fts3_tokenizer(c):
    db = get_db_from_connection(c)
    rc = dll.sqlite3_db_config(db, SQLITE_DBCONFIG_ENABLE_FTS3_TOKENIZER,
                               ffi.cast('int', 1), ffi.NULL)
    return rc == SQLITE_OK


def register_tokenizer(conn, name, tokenizer_module):
    '''register tokenizer module with SQLite connection.'''
    module_addr = int(ffi.cast('uintptr_t', tokenizer_module))
    address_blob = struct.pack('P', module_addr)
    if sys.version_info.major == 2:
        address_blob = buffer(address_blob)
    if not enable_fts3_tokenizer(conn):
        warnings.warn('enabling 2-arg fts3_tokenizer failed.', RuntimeWarning)
    cur = conn.cursor()
    try:
        r = cur.execute('SELECT fts3_tokenizer(?, ?)',
                        (name, address_blob)).fetchall()
    finally:
        cur.close()
    return r


__all__ = ['Tokenizer', 'make_tokenizer_module', 'register_tokenizer']
