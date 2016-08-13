# coding: utf-8
"""
PoC SQLite FTS5 tokenizer in Python
"""
from __future__ import print_function, unicode_literals
import struct

from .tokenizer import ffi, SQLITE_OK

FTS5_TOKENIZE_QUERY = 0x0001
FTS5_TOKENIZE_PREFIX = 0x0002
FTS5_TOKENIZE_DOCUMENT = 0x0004
FTS5_TOKENIZE_AUX = 0x0008
FTS5_TOKEN_COLOCATED = 0x0001

ffi.cdef('''
typedef struct fts5_api fts5_api;
typedef struct fts5_tokenizer fts5_tokenizer;
typedef struct Fts5Tokenizer Fts5Tokenizer;

struct fts5_api {
  int iVersion;
  int (*xCreateTokenizer)(
    fts5_api *pApi, const char *zName, void *pContext,
    fts5_tokenizer *pTokenizer,void (*xDestroy)(void*));
};

struct fts5_tokenizer {
  int (*xCreate)(void*, const char **azArg, int nArg, Fts5Tokenizer **ppOut);
  void (*xDelete)(Fts5Tokenizer*);
  int (*xTokenize)(
    Fts5Tokenizer*, void *pCtx, int flags, const char *pText, int nText,
    int (*xToken)(
        void *pCtx, int tflags,const char *pToken,
        int nToken, int iStart, int iEnd));
};
''')

fts5_tokenizers = {}
"""hold references to prevent GC"""


def fts5_api_from_db(c):
    cur = c.cursor()
    try:
        cur.execute('SELECT fts5()')
        blob = cur.fetchone()[0]
        pRet = ffi.cast('fts5_api*', struct.unpack("P", blob)[0])
    finally:
        cur.close()
    return pRet


def register_tokenizer(c, name, tokenizer, context=None, on_destroy=None):
    """ need to keep reference of context and on_destroy """
    fts5api = fts5_api_from_db(c)
    pContext = ffi.new_handle(context)
    if on_destroy is None:
        xDestroy = ffi.NULL
    else:

        @ffi.callback('void(void*)')
        def xDestroy(context):
            on_destroy(ffi.from_handle(context))

    fts5_tokenizers[name] = (tokenizer, pContext, xDestroy)
    r = fts5api.xCreateTokenizer(fts5api, name.encode('utf-8'), pContext,
                                 tokenizer, xDestroy)
    return r == SQLITE_OK


def make_fts5_tokenizer(tokenizer):
    """ make tokenizer module """
    t = ffi.new_handle(tokenizer)
    tokenizers = {}

    @ffi.callback('int(void*, const char **, int, Fts5Tokenizer **)')
    def xcreate(ctx, argv, argc, ppOut):
        # is keeping ctor instead of keeping tokenizer instance good idea?
        # i.e. t = ctor(context, argv)
        tkn = ffi.cast('Fts5Tokenizer *', t)
        tokenizers[int(ffi.cast('intptr_t', tkn))] = tkn
        ppOut[0] = tkn
        return SQLITE_OK

    @ffi.callback('void(Fts5Tokenizer *)')
    def xdelete(pTokenizer):
        del tokenizers[int(ffi.cast('intptr_t', pTokenizer))]
        return None

    @ffi.callback('int(Fts5Tokenizer *, void *, int, const char *, int, '
                  'int(void*, int, const char *, int, int, int))')
    def xtokenize(pTokenizer, pCtx, flags, pText, nText, xToken):
        tokenizer = ffi.from_handle(ffi.cast('void *', pTokenizer))
        text = ffi.string(pText[0:nText]).decode('utf-8')
        for normalized, inputBegin, inputEnd in tokenizer.tokenize(text):
            normalized = normalized.encode('utf-8')
            if not normalized:
                continue

            # TODO: Synonym Support
            r = xToken(pCtx, 0, ffi.new('char[]', normalized), len(normalized),
                       inputBegin, inputEnd)
            if r != SQLITE_OK:
                return r
        return SQLITE_OK

    fts5_tokenizer = ffi.new("fts5_tokenizer *", [xcreate, xdelete, xtokenize])
    fts5_tokenizers[tokenizer] = (fts5_tokenizer, xcreate, xdelete, xtokenize)
    return fts5_tokenizer


__all__ = ["register_tokenizer", "make_fts5_tokenizer"]
