# coding: utf-8
from __future__ import print_function, unicode_literals
import sqlite3
import re

from cffi import FFI

from sqlitefts import fts5
from sqlitefts import Tokenizer

ffi = FFI()


class SimpleTokenizer(Tokenizer):
    _p = re.compile(r'\w+', re.UNICODE)

    def tokenize(self, text):
        for m in self._p.finditer(text):
            s, e = m.span()
            t = text[s:e]
            l = len(t.encode('utf-8'))
            p = len(text[:s].encode('utf-8'))
            yield t, p, p + l


def test_fts5_api_from_db():
    c = sqlite3.connect(':memory:')
    fts5api = fts5.fts5_api_from_db(c)
    assert fts5api.iVersion == 2
    assert fts5api.xCreateTokenizer
    c.close()


def test_make_tokenizer():
    c = sqlite3.connect(':memory:')
    tm = fts5.make_fts5_tokenizer(SimpleTokenizer())
    assert all(
        getattr(tm, x) is not None
        for x in ('xCreate', 'xDelete', 'xTokenize'))
    c.close()


def test_register_tokenizer():
    name = 'simpe'
    c = sqlite3.connect(':memory:')
    tm = fts5.make_fts5_tokenizer(SimpleTokenizer())
    assert fts5.register_tokenizer(c, name, tm)
    c.close()


def test_register_tokenizer_with_destroy():
    name = 'simpe'
    c = sqlite3.connect(':memory:')

    arg_on_destroy = []
    context = "hello"

    def on_destroy(x):
        arg_on_destroy.append(x)

    tm = fts5.make_fts5_tokenizer(SimpleTokenizer())
    assert fts5.register_tokenizer(
        c, name, tm, context=context, on_destroy=on_destroy)
    c.close()
    assert arg_on_destroy == [context]


def test_createtable():
    c = sqlite3.connect(':memory:')
    c.row_factory = sqlite3.Row
    name = 'super_simple'
    sql = "CREATE VIRTUAL TABLE fts USING fts5(w, tokenize={})".format(name)
    fts5.register_tokenizer(c, name,
                            fts5.make_fts5_tokenizer(SimpleTokenizer()))
    c.execute(sql)

    r = c.execute(
        "SELECT * FROM sqlite_master WHERE type='table' AND name='fts'").fetchone(
        )
    assert r
    assert r[str('type')] == 'table' and r[str('name')] == 'fts' and r[str(
        'tbl_name')] == 'fts'
    assert r[str('sql')].upper() == sql.upper()
    c.close()


def test_insert():
    c = sqlite3.connect(':memory:')
    c.row_factory = sqlite3.Row
    name = 'super_simple'
    content = 'これは日本語で書かれています'
    fts5.register_tokenizer(c, name,
                            fts5.make_fts5_tokenizer(SimpleTokenizer()))
    c.execute(
        "CREATE VIRTUAL TABLE fts USING FTS5(content, tokenize={})".format(
            name))
    r = c.execute('INSERT INTO fts VALUES(?)', (content, ))
    assert r.rowcount == 1
    r = c.execute("SELECT * FROM fts").fetchone()
    assert r
    assert r[str('content')] == content
    c.close()


def test_match():
    c = sqlite3.connect(':memory:')
    c.row_factory = sqlite3.Row
    name = 'super_simple'
    contents = [('abc def', ), ('abc xyz', ), ('あいうえお かきくけこ', ),
                ('あいうえお らりるれろ', )]
    fts5.register_tokenizer(c, name,
                            fts5.make_fts5_tokenizer(SimpleTokenizer()))
    c.execute(
        "CREATE VIRTUAL TABLE fts USING FTS5(content, tokenize={})".format(
            name))
    r = c.executemany('INSERT INTO fts VALUES(?)', contents)
    assert r.rowcount == 4
    r = c.execute("SELECT * FROM fts").fetchall()
    assert len(r) == 4
    r = c.execute("SELECT * FROM fts WHERE fts MATCH 'abc'").fetchall()
    assert len(r) == 2
    r = c.execute("SELECT * FROM fts WHERE fts MATCH 'def'").fetchall()
    assert len(r) == 1 and r[0][str('content')] == contents[0][0]
    r = c.execute("SELECT * FROM fts WHERE fts MATCH 'xyz'").fetchall()
    assert len(r) == 1 and r[0][str('content')] == contents[1][0]
    r = c.execute("SELECT * FROM fts WHERE fts MATCH 'zzz'").fetchall()
    assert len(r) == 0
    r = c.execute("SELECT * FROM fts WHERE fts MATCH 'あいうえお'").fetchall()
    assert len(r) == 2
    r = c.execute("SELECT * FROM fts WHERE fts MATCH 'かきくけこ'").fetchall()
    assert len(r) == 1 and r[0][str('content')] == contents[2][0]
    r = c.execute("SELECT * FROM fts WHERE fts MATCH 'らりるれろ'").fetchall()
    assert len(r) == 1 and r[0][str('content')] == contents[3][0]
    r = c.execute("SELECT * FROM fts WHERE fts MATCH 'まみむめも'").fetchall()
    assert len(r) == 0
    c.close()


def test_full_text_index_queries():
    name = 'super_simple'
    docs = [(
        'README',
        'sqlitefts-python provides binding for tokenizer of SQLite Full-Text search(FTS3/4). It allows you to write tokenizers in Python.'
    ), ('LICENSE',
        '''Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:'''),
            ('日本語', 'あいうえお かきくけこ さしすせそ たちつてと なにぬねの')]
    with sqlite3.connect(':memory:') as c:
        c.row_factory = sqlite3.Row
        fts5.register_tokenizer(c, name,
                                fts5.make_fts5_tokenizer(SimpleTokenizer()))
        c.execute(
            "CREATE VIRTUAL TABLE docs USING FTS5(title, body, tokenize={})".format(
                name))
        c.executemany("INSERT INTO docs(title, body) VALUES(?, ?)", docs)
        r = c.execute("SELECT * FROM docs WHERE docs MATCH 'Python'").fetchall(
        )
        assert len(r) == 1
        r = c.execute("SELECT * FROM docs WHERE docs MATCH 'bind'").fetchall()
        assert len(r) == 0
        r = c.execute(
            "SELECT * FROM docs WHERE docs MATCH 'binding'").fetchall()
        assert len(r) == 1
        r = c.execute("SELECT * FROM docs WHERE docs MATCH 'to'").fetchall()
        assert len(r) == 2
        r = c.execute("SELECT * FROM docs WHERE docs MATCH 'あいうえお'").fetchall()
        assert len(r) == 1
        r = c.execute("SELECT * FROM docs WHERE docs MATCH 'らりるれろ'").fetchall()
        assert len(r) == 0
        assert (
            c.execute(
                "SELECT * FROM docs WHERE docs MATCH 'binding'").fetchall()[0]
            == c.execute(
                "SELECT * FROM docs WHERE docs MATCH 'body:binding'").fetchall(
                )[0])
        assert (c.execute(
            "SELECT * FROM docs WHERE docs MATCH 'body:binding'").fetchall(
            )[0] == c.execute(
                "SELECT * FROM docs WHERE docs MATCH 'body:binding'").fetchall(
                )[0])
        assert (
            c.execute("SELECT * FROM docs WHERE docs MATCH 'あいうえお'").fetchall(
            )[0] == c.execute(
                "SELECT * FROM docs WHERE docs MATCH 'body:あいうえお'").fetchall()[
                    0])
        r = c.execute(
            "SELECT * FROM docs WHERE docs MATCH 'title:bind'").fetchall()
        assert len(r) == 0
        r = c.execute(
            "SELECT * FROM docs WHERE docs MATCH 'title:README'").fetchall()
        assert len(r) == 1
        r = c.execute(
            "SELECT * FROM docs WHERE docs MATCH 'title:日本語'").fetchall()
        assert len(r) == 1
        r = c.execute("SELECT * FROM docs WHERE docs MATCH 'to in'").fetchall()
        assert len(r) == 2
        r = c.execute("SELECT * FROM docs WHERE docs MATCH 'Py*'").fetchall()
        assert len(r) == 1
        r = c.execute("SELECT * FROM docs WHERE docs MATCH 'Z*'").fetchall()
        assert len(r) == 0
        r = c.execute("SELECT * FROM docs WHERE docs MATCH 'あ*'").fetchall()
        assert len(r) == 1
        r = c.execute("SELECT * FROM docs WHERE docs MATCH 'ん*'").fetchall()
        assert len(r) == 0
        r = c.execute(
            "SELECT * FROM docs WHERE docs MATCH 'tokenizer SQLite'").fetchall(
            )
        assert len(r) == 1
        r = c.execute(
            "SELECT * FROM docs WHERE docs MATCH '\"tokenizer SQLite\"'").fetchall(
            )
        assert len(r) == 0
        r = c.execute(
            "SELECT * FROM docs WHERE docs MATCH 'あいうえお たちつてと'").fetchall()
        assert len(r) == 1
        r = c.execute(
            "SELECT * FROM docs WHERE docs MATCH '\"あいうえお たちつてと\"'").fetchall()
        assert len(r) == 0
        r = c.execute(
            "SELECT * FROM docs WHERE docs MATCH 'tok* + SQL*'").fetchall()
        assert len(r) == 0
        r = c.execute(
            "SELECT * FROM docs WHERE docs MATCH 'tok* of SQL*'").fetchall()
        assert len(r) == 1
        r = c.execute(
            "SELECT * FROM docs WHERE docs MATCH 'あ* + さ*'").fetchall()
        assert len(r) == 0
        r = c.execute(
            "SELECT * FROM docs WHERE docs MATCH 'あ* かきくけこ さ*'").fetchall()
        assert len(r) == 1
        r = c.execute(
            "SELECT * FROM docs WHERE docs MATCH 'NEAR(tokenizer SQLite)'").fetchall(
            )
        assert len(r) == 1
        r = c.execute(
            "SELECT * FROM docs WHERE docs MATCH 'NEAR(binding SQLite, 2)'").fetchall(
            )
        assert len(r) == 0
        r = c.execute(
            "SELECT * FROM docs WHERE docs MATCH 'NEAR(binding SQLite, 3)'").fetchall(
            )
        assert len(r) == 1
        r = c.execute(
            "SELECT * FROM docs WHERE docs MATCH 'NEAR(あいうえお たちつてと)'").fetchall(
            )
        assert len(r) == 1
        r = c.execute(
            "SELECT * FROM docs WHERE docs MATCH 'NEAR(あいうえお たちつてと, 2)'").fetchall(
            )
        assert len(r) == 1
        r = c.execute(
            "SELECT * FROM docs WHERE docs MATCH 'NEAR(あいうえお たちつてと, 3)'").fetchall(
            )
        assert len(r) == 1
