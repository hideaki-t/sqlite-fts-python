# coding: utf-8
from __future__ import print_function, unicode_literals
import sys
import os
import sqlite3
import ctypes
import struct

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import sqlitefts.sqlite_tokenizer as fts

import pytest
igo = pytest.importorskip('igo')

class IgoTokenizer(fts.Tokenizer):
    def __init__(self, path=None):
        self.tagger = igo.tagger.Tagger(path)

    def tokenize(self, text):
        return iter([m.surface for m in self.tagger.parse(text)])


t = IgoTokenizer('./ipadic')

def test_make_tokenizer():
    c = sqlite3.connect(':memory:')
    tokenizer_module = fts.make_tokenizer_module(t)
    assert fts.sqlite3_tokenizer_module == type(tokenizer_module)
    c.close()


def test_reginster_tokenizer():
    name = 'igo'
    c = sqlite3.connect(':memory:')
    tokenizer_module = fts.make_tokenizer_module(t)
    fts.register_tokenizer(c, name, tokenizer_module)
    v = c.execute("SELECT FTS3_TOKENIZER(?)", (name,)).fetchone()[0]
    assert ctypes.addressof(tokenizer_module) == struct.unpack("P", v)[0]
    c.close()


def test_createtable():
    c = sqlite3.connect(':memory:')
    c.row_factory = sqlite3.Row
    name = 'igo'
    sql = "CREATE VIRTUAL TABLE fts USING FTS4(tokenize={})".format(name)
    fts.register_tokenizer(c, name, fts.make_tokenizer_module(t))
    c.execute(sql)
    r = c.execute("SELECT * FROM sqlite_master WHERE type='table' AND name='fts'").fetchone()
    assert r
    assert r[str('type')] == 'table' and r[str('name')] == 'fts' and r[str('tbl_name')] == 'fts'
    assert r[str('sql')].upper() == sql.upper()
    c.close()


def test_insert():
    c = sqlite3.connect(':memory:')
    c.row_factory = sqlite3.Row
    name = 'igo'
    content = 'これは日本語で書かれています'
    fts.register_tokenizer(c, name, fts.make_tokenizer_module(t))
    c.execute("CREATE VIRTUAL TABLE fts USING FTS4(tokenize={})".format(name))
    r = c.execute('INSERT INTO fts VALUES(?)', (content,))
    assert r.rowcount == 1
    r = c.execute("SELECT * FROM fts").fetchone()
    assert r
    assert r[str('content')] == content
    c.close()


def test_match():
    c = sqlite3.connect(':memory:')
    c.row_factory = sqlite3.Row
    name = 'igo'
    contents = [('これは日本語で書かれています',),
                (' これは　日本語の文章を 全文検索するテストです',)]
    fts.register_tokenizer(c, name, fts.make_tokenizer_module(t))
    c.execute("CREATE VIRTUAL TABLE fts USING FTS4(tokenize={})".format(name))
    r = c.executemany('INSERT INTO fts VALUES(?)', contents)
    assert r.rowcount == 2
    r = c.execute("SELECT * FROM fts").fetchall()
    assert len(r) == 2
    r = c.execute("SELECT * FROM fts WHERE fts MATCH '日本語'").fetchall()
    assert len(r) == 2
    r = c.execute("SELECT * FROM fts WHERE fts MATCH '書かれて'").fetchall()
    assert len(r) == 1 and r[0][str('content')] == contents[0][0]
    r = c.execute("SELECT * FROM fts WHERE fts MATCH 'テスト'").fetchall()
    assert len(r) == 1 and r[0][str('content')] == contents[1][0]
    r = c.execute("SELECT * FROM fts WHERE fts MATCH 'コレは'").fetchall()
    assert len(r) == 0
    c.close()
