# coding: utf-8
"""
a proof of concept implementation of SQLite FTS tokenizers in Python
"""
from __future__ import print_function, unicode_literals

import sys
import ctypes
from ctypes import POINTER, CFUNCTYPE
import struct
import igo


class sqlite3_tokenizer_module(ctypes.Structure):
    pass


class sqlite3_tokenizer(ctypes.Structure):
    _fields_ = [("pModule", POINTER(sqlite3_tokenizer_module)),
                ("t", ctypes.py_object)]


class sqlite3_tokenizer_cursor(ctypes.Structure):
    _fields_ = [("pTokenizer", POINTER(sqlite3_tokenizer)),
                ("nodes", ctypes.py_object),
                ("offset", ctypes.c_int),
                ("pos", ctypes.c_int)]

xCreate = CFUNCTYPE(ctypes.c_int, ctypes.c_int, POINTER(ctypes.c_char_p),
                    POINTER(POINTER(sqlite3_tokenizer)))
xDestroy = CFUNCTYPE(ctypes.c_int, POINTER(sqlite3_tokenizer))
xOpen = CFUNCTYPE(ctypes.c_int, POINTER(sqlite3_tokenizer),
                  ctypes.c_char_p, ctypes.c_int,
                  POINTER(POINTER(sqlite3_tokenizer_cursor)))
xClose = CFUNCTYPE(ctypes.c_int, POINTER(sqlite3_tokenizer_cursor))
xNext = CFUNCTYPE(ctypes.c_int, POINTER(sqlite3_tokenizer_cursor),
                  POINTER(ctypes.c_char_p), POINTER(ctypes.c_int),
                  POINTER(ctypes.c_int), POINTER(ctypes.c_int),
                  POINTER(ctypes.c_int))

sqlite3_tokenizer_module._fields_ = [
    ("iVersion", ctypes.c_int), ("xCreate", xCreate), ("xDestroy", xDestroy),
    ("xOpen", xOpen), ("xClose", xClose), ("xNext", xNext)]


def make_tokenizer_module():
    tokenizers = {}
    cursors = {}

    def xcreate(argc, argv, ppTokenizer):
        tkn = sqlite3_tokenizer()
        if argc > 0:
            tkn.t = igo.tagger.Tagger(argv[0].decode('utf-8'))
        else:
            tkn.t = igo.tagger.Tagger()
        tokenizers[ctypes.addressof(tkn)] = tkn
        ppTokenizer[0] = ctypes.pointer(tkn)
        return 0

    def xdestroy(pTokenizer):
        del(tokenizers[ctypes.addressof(pTokenizer[0])])
        return 0

    def xopen(pTokenizer, pInput, nInput, ppCursor):
        cur = sqlite3_tokenizer_cursor()
        cur.pTokenizer = pTokenizer
        cur.nodes = iter(pTokenizer[0].t.parse(pInput.decode('utf-8')))
        cur.pos = 0
        cur.offset = 0
        cursors[ctypes.addressof(cur)] = cur
        ppCursor[0] = ctypes.pointer(cur)
        return 0

    def xnext(pCursor, ppToken, pnBytes,
              piStartOffset, piEndOffset, piPosition):
        try:
            cur = pCursor[0]
            m = next(pCursor[0].nodes)
            token = m.surface.encode('utf-8')
            tokenlen = len(token)
            ppToken[0] = token
            pnBytes[0] = tokenlen
            piStartOffset[0] = cur.offset
            cur.offset += tokenlen
            piEndOffset[0] = cur.offset
            piPosition[0] = cur.pos
            cur.pos += 1
        except StopIteration:
            return 101
        return 0

    def xclose(pCursor):
        del(cursors[ctypes.addressof(pCursor[0])])
        return 0

    return sqlite3_tokenizer_module(
        0,
        xCreate(xcreate),
        xDestroy(xdestroy),
        xOpen(xopen),
        xClose(xclose),
        xNext(xnext))

tokenizer_module = make_tokenizer_module()


def register_tokenizer(c):
    if sys.version_info.major == 2:
        global buffer
    else:
        buffer = lambda x: x
    address_blob = buffer(struct.pack("P", ctypes.addressof(tokenizer_module)))
    c.execute('SELECT fts3_tokenizer(?, ?)', ('igo', address_blob))


if __name__ == '__main__':
    import sqlite3
    c = sqlite3.connect(':memory:')
    register_tokenizer(c)
    c.execute("CREATE VIRTUAL TABLE fts USING FTS4(tokenize=igo '/home/hideaki/works/dat/ipadic')")
    c.execute('INSERT INTO fts VALUES(?)', ('これは日本語で書かれています',))
    c.execute('INSERT INTO fts VALUES(?)', (' これは　日本語の文章を 全文検索するテストです',))
    for i in c.execute("SELECT * FROM fts WHERE fts MATCH '日本語'").fetchall():
        print(i[0])
    c.close()
