# coding: utf-8
"""
PoC SQLite FTS5 tokenizer in Python
"""
from __future__ import print_function, unicode_literals

from .tokenizer import ffi, SQLITE_OK, SQLITE_DONE

ffi.cdef('''
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

            ppToken[0] = ffi.new('char []', normalized)  # ??
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
    tokenizer_modules[tokenizer] = (tokenizer_module, xcreate, xdestroy, xopen,
                                    xclose, xnext)
    return tokenizer_module
