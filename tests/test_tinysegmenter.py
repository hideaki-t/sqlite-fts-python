# coding: utf-8
from __future__ import print_function, unicode_literals
import sqlite3
import ctypes
import struct

import sqlitefts as fts

import pytest
ts = pytest.importorskip('tinysegmenter')


class TinySegmenterTokenizer(fts.Tokenizer):
    def __init__(self, path=None):
        self.segmenter = ts.TinySegmenter()

    def tokenize(self, text):
        p = 0
        for t in self.segmenter.tokenize(text):
            lt = len(t)
            np = p + text[p:].index(t)
            start = len(text[:np].encode('utf-8')) + (lt - len(t.lstrip()))
            txt = t.strip()
            yield txt, start, start + len(txt.encode('utf-8'))
            p = np + lt


t = TinySegmenterTokenizer()


def test_make_tokenizer():
    c = sqlite3.connect(':memory:')
    tokenizer_module = fts.make_tokenizer_module(t)
    assert fts.tokenizer.sqlite3_tokenizer_module == type(tokenizer_module)
    c.close()


def test_reginster_tokenizer():
    name = 'tinysegmenter'
    c = sqlite3.connect(':memory:')
    tokenizer_module = fts.make_tokenizer_module(t)
    fts.register_tokenizer(c, name, tokenizer_module)
    v = c.execute("SELECT FTS3_TOKENIZER(?)", (name,)).fetchone()[0]
    assert ctypes.addressof(tokenizer_module) == struct.unpack("P", v)[0]
    c.close()


def test_createtable():
    c = sqlite3.connect(':memory:')
    c.row_factory = sqlite3.Row
    name = 'tinysegmenter'
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


def test_tokenizer_output():
    name = 'tinysegmenter'
    with sqlite3.connect(':memory:') as c:
        fts.register_tokenizer(c, name, fts.make_tokenizer_module(t))
        c.execute("CREATE VIRTUAL TABLE tok1 USING fts3tokenize({})".format(name))
        expect = [("This", 0, 4, 0), ("is", 5, 7, 1),
                  ("a", 8, 9, 2), ("test", 10, 14, 3), ("sentence", 15, 23, 4)]
        for a, e in zip(c.execute("SELECT token, start, end, position "
                                  "FROM tok1 WHERE input='This is a test sentence.'"), expect):
            assert e == a

        s = 'これ は テスト の 文 です'
        expect = [(None, 0, 0, 0)]
        for i, txt in enumerate(s.split()):
            expect.append((txt, expect[-1][2], expect[-1][2] + len(txt.encode('utf-8')), i))
        expect = expect[1:]
        for a, e in zip(c.execute("SELECT token, start, end, position "
                                  "FROM tok1 WHERE input=?", [s.replace(' ', '')]), expect):
            assert e == a
