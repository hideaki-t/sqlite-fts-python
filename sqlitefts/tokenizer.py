# coding: utf-8
"""
a proof of concept implementation of SQLite FTS tokenizers in Python
"""
from __future__ import print_function, unicode_literals

import sys
import ctypes
from ctypes import POINTER, CFUNCTYPE
import struct

SQLITE_OK = 0
SQLITE_DONE = 101

if sys.version_info.major == 2:
    global buffer
else:
    buffer = lambda x: x


def f():
    if sys.platform == 'win32':
        dll = ctypes.CDLL("sqlite3")
    else:
        from ctypes.util import find_library
        dll = ctypes.CDLL(find_library("sqlite3"))

    SQLITE_DBCONFIG_ENABLE_FTS3_TOKENIZER = 1004

    # this structure completely depends on
    # the definition of pysqlite_Connection and PyObject_HEAD
    # this won't work if
    # Py_TRACE_REFS is enabled
    # AND/OR
    # the definition of "sqlite3* db" in pysqlite_Connection is changed/moved
    class PyObject(ctypes.Structure):
        _fields_ = (("ob_refcnt", ctypes.c_size_t),
                    ("ob_type", ctypes.c_void_p), ("db", ctypes.c_void_p))

    dll.sqlite3_db_config.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                      ctypes.c_int, ctypes.c_int]

    def enable_fts3_tokenizer(c):
        rc = dll.sqlite3_db_config(
            ctypes.cast(
                id(c), ctypes.POINTER(PyObject)).contents.db,
            SQLITE_DBCONFIG_ENABLE_FTS3_TOKENIZER, 1, 0)
        return rc == 0

    return enable_fts3_tokenizer


enable_fts3_tokenizer = f()


class sqlite3_tokenizer_module(ctypes.Structure):
    pass


class sqlite3_tokenizer(ctypes.Structure):
    _fields_ = [(str("pModule"), POINTER(sqlite3_tokenizer_module)),
                (str("t"), ctypes.py_object)]


class sqlite3_tokenizer_cursor(ctypes.Structure):
    _fields_ = [(str("pTokenizer"), POINTER(sqlite3_tokenizer)),
                (str("tokens"), ctypes.py_object),
                (str("offset"), ctypes.c_int), (str("pos"), ctypes.c_int)]


xCreate = CFUNCTYPE(ctypes.c_int, ctypes.c_int, POINTER(ctypes.c_char_p),
                    POINTER(POINTER(sqlite3_tokenizer)))
xDestroy = CFUNCTYPE(ctypes.c_int, POINTER(sqlite3_tokenizer))
xOpen = CFUNCTYPE(ctypes.c_int, POINTER(sqlite3_tokenizer), ctypes.c_char_p,
                  ctypes.c_int, POINTER(POINTER(sqlite3_tokenizer_cursor)))
xClose = CFUNCTYPE(ctypes.c_int, POINTER(sqlite3_tokenizer_cursor))
xNext = CFUNCTYPE(ctypes.c_int, POINTER(sqlite3_tokenizer_cursor),
                  POINTER(ctypes.c_char_p), POINTER(ctypes.c_int),
                  POINTER(ctypes.c_int), POINTER(ctypes.c_int),
                  POINTER(ctypes.c_int))

sqlite3_tokenizer_module._fields_ = [
    (str("iVersion"), ctypes.c_int), (str("xCreate"), xCreate),
    (str("xDestroy"), xDestroy), (str("xOpen"), xOpen),
    (str("xClose"), xClose), (str("xNext"), xNext)
]


class Tokenizer:
    """ Tokenizer base class """

    def tokenize(text):
        """ Tokenize given unicode text. Yields each tokenized token, start position(in bytes), end positon(in bytes)"""
        yield text, 0, len(text.encode('utf-8'))


tokenizer_modules = {}
"""hold references to prevent GC"""


def make_tokenizer_module(tokenizer):
    """ make tokenizer module """
    tokenizers = {}
    cursors = {}

    def xcreate(argc, argv, ppTokenizer):
        tkn = sqlite3_tokenizer()
        tkn.t = tokenizer
        tokenizers[ctypes.addressof(tkn)] = tkn
        ppTokenizer[0] = ctypes.pointer(tkn)
        return SQLITE_OK

    def xdestroy(pTokenizer):
        del tokenizers[ctypes.addressof(pTokenizer[0])]
        return SQLITE_OK

    def xopen(pTokenizer, pInput, nInput, ppCursor):
        cur = sqlite3_tokenizer_cursor()
        cur.pTokenizer = pTokenizer
        cur.tokens = pTokenizer[0].t.tokenize(pInput.decode('utf-8'))
        cur.pos = 0
        cur.offset = 0
        cursors[ctypes.addressof(cur)] = cur
        ppCursor[0] = ctypes.pointer(cur)
        return SQLITE_OK

    def xnext(pCursor, ppToken, pnBytes, piStartOffset, piEndOffset,
              piPosition):
        try:
            cur = pCursor[0]

            while True:
                normalized, inputBegin, inputEnd = next(cur.tokens)
                normalized = normalized.encode('utf-8')
                if normalized:
                    break

            ppToken[0] = normalized
            pnBytes[0] = len(normalized)
            piStartOffset[0] = inputBegin
            piEndOffset[0] = inputEnd
            cur.offset = inputEnd
            piPosition[0] = cur.pos
            cur.pos += 1
        except StopIteration:
            return SQLITE_DONE
        return SQLITE_OK

    def xclose(pCursor):
        del cursors[ctypes.addressof(pCursor[0])]
        return SQLITE_OK

    tokenizer_module = sqlite3_tokenizer_module(
        0, xCreate(xcreate), xDestroy(xdestroy), xOpen(xopen), xClose(xclose),
        xNext(xnext))
    return tokenizer_module


def register_tokenizer(c, name, tokenizer_module):
    """ register tokenizer module with SQLite connection. """
    if not enable_fts3_tokenizer(c):
        raise Exception("cannot enable custom tokenizer")
    module_addr = ctypes.addressof(tokenizer_module)
    address_blob = buffer(struct.pack("P", module_addr))
    r = c.execute('SELECT fts3_tokenizer(?, ?)', (name, address_blob))
    tokenizer_modules[module_addr] = tokenizer_module
    return r
