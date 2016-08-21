# coding: utf-8
from __future__ import print_function, unicode_literals
import sqlite3
import re
from collections import Counter

from sqlitefts import fts5, fts5_aux

import pytest
from cffi import FFI

ffi = FFI()


class SimpleTokenizer(fts5.FTS5Tokenizer):
    _p = re.compile(r'\w+', re.UNICODE)

    def tokenize(self, text, flags):
        for m in self._p.finditer(text):
            s, e = m.span()
            t = text[s:e]
            l = len(t.encode('utf-8'))
            p = len(text[:s].encode('utf-8'))
            yield t, p, p + l


@pytest.fixture
def c():
    c = sqlite3.connect(':memory:')
    c.row_factory = sqlite3.Row
    return c


@pytest.fixture
def tm():
    return fts5.make_fts5_tokenizer(SimpleTokenizer())


def test_fts5_api_from_db(c):
    fts5api = fts5.fts5_api_from_db(c)
    assert fts5api.iVersion == 2
    assert fts5api.xCreateTokenizer
    c.close()


def test_make_tokenizer(c):
    tm = fts5.make_fts5_tokenizer(SimpleTokenizer())
    assert all(
        getattr(tm, x) is not None
        for x in ('xCreate', 'xDelete', 'xTokenize'))
    c.close()


def test_make_tokenizer_by_class(c):
    tm = fts5.make_fts5_tokenizer(SimpleTokenizer)
    assert all(
        getattr(tm, x) is not None
        for x in ('xCreate', 'xDelete', 'xTokenize'))
    c.close()


def test_register_tokenizer(c, tm):
    name = 'super_simple'
    assert fts5.register_tokenizer(c, name, tm)
    c.close()


def test_register_tokenizer_with_destroy(c, tm):
    name = 'super_simple'
    arg_on_destroy = []
    context = "hello"

    def on_destroy(x):
        arg_on_destroy.append(x)

    assert fts5.register_tokenizer(
        c, name, tm, context=context, on_destroy=on_destroy)
    c.close()
    assert arg_on_destroy == [context]


def test_createtable(c, tm):
    name = 'super_simple'
    sql = "CREATE VIRTUAL TABLE fts USING fts5(w, tokenize={})".format(name)
    fts5.register_tokenizer(c, name, tm)
    c.execute(sql)

    r = c.execute(
        "SELECT * FROM sqlite_master WHERE type='table' AND name='fts'").fetchone(
        )
    assert r
    assert r[str('type')] == 'table' and r[str('name')] == 'fts' and r[str(
        'tbl_name')] == 'fts'
    assert r[str('sql')].upper() == sql.upper()
    c.close()


def test_createtale_using_tokenizer_class(c):
    initialized = {}
    deleted = Counter()

    class ST(SimpleTokenizer):
        def __init__(self, context=None, args=None):
            initialized[self] = (context, tuple(args))

        def on_delete(self):
            deleted[self] += 1

    name = 'super_simple'
    fts5.register_tokenizer(
        c, name, fts5.make_fts5_tokenizer(ST), context='test')
    sql = (
        "CREATE VIRTUAL TABLE fts "
        "USING FTS5(content, tokenize='{} {} {}')").format(name, 'arg', '引数')
    c.execute(sql)
    assert len(initialized) == 1
    assert list(initialized.values()) == [('test', ('arg', '引数'))]
    assert len(deleted) == 0
    sql = (
        "CREATE VIRTUAL TABLE fts_2 "
        "USING FTS5(content, tokenize='{} {} {}')").format(name, 'arg2', '引数2')
    c.execute(sql)
    c.close()
    assert set(initialized.values()) == {('test', ('arg', '引数')),
                                         ('test', ('arg2', '引数2'))}
    assert list(x for x in deleted.values()) == [1, 1]


def test_insert(c, tm):
    name = 'super_simple'
    content = 'これは日本語で書かれています'
    fts5.register_tokenizer(c, name, tm)
    c.execute("CREATE VIRTUAL TABLE fts USING FTS5(content, tokenize={})".
              format(name))
    r = c.execute('INSERT INTO fts VALUES(?)', (content, ))
    assert r.rowcount == 1
    r = c.execute("SELECT * FROM fts").fetchone()
    assert r
    assert r[str('content')] == content
    c.close()


def test_match(c, tm):
    name = 'super_simple'
    contents = [('abc def', ), ('abc xyz', ), ('あいうえお かきくけこ', ),
                ('あいうえお らりるれろ', )]
    fts5.register_tokenizer(c, name, tm)
    c.execute("CREATE VIRTUAL TABLE fts USING FTS5(content, tokenize={})".
              format(name))
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


def test_full_text_index_queries(c, tm):
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
    with c:
        fts5.register_tokenizer(c, name, tm)
        c.execute(
            "CREATE VIRTUAL TABLE docs USING FTS5(title, body, tokenize={})".
            format(name))
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
        assert (c.execute(
            "SELECT * FROM docs WHERE docs MATCH 'binding'").fetchall()[0] ==
                c.execute("SELECT * FROM docs WHERE docs MATCH 'body:binding'")
                .fetchall()[0])
        assert (c.execute("SELECT * FROM docs WHERE docs MATCH 'body:binding'")
                .fetchall()[0] ==
                c.execute("SELECT * FROM docs WHERE docs MATCH 'body:binding'")
                .fetchall()[0])
        assert (c.execute(
            "SELECT * FROM docs WHERE docs MATCH 'あいうえお'").fetchall()[0] ==
                c.execute("SELECT * FROM docs WHERE docs MATCH 'body:あいうえお'")
                .fetchall()[0])
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


def test_flags(c):
    flags_counter = Counter()

    class ST(SimpleTokenizer):
        def tokenize(self, text, flags):
            flags_counter[flags] += 1
            return super(ST, self).tokenize(text, flags)

    name = 'super_simple2'
    fts5.register_tokenizer(c, name, fts5.make_fts5_tokenizer(ST()))
    sql = ("CREATE VIRTUAL TABLE fts "
           "USING FTS5(content, tokenize='{}')").format(name)
    c.execute(sql)
    c.executemany('INSERT INTO fts VALUES(?)',
                  [('abc def', ), ('abc xyz', ), ('あいうえお かきくけこ', ),
                   ('あいうえお らりるれろ', )])
    c.execute("SELECT * FROM fts WHERE fts MATCH 'abc'").fetchall()
    c.execute("SELECT * FROM fts WHERE fts MATCH 'abc'").fetchall()
    c.close()
    assert flags_counter[fts5.FTS5_TOKENIZE_DOCUMENT] == 4
    assert flags_counter[fts5.FTS5_TOKENIZE_QUERY] == 2


def test_aux_and_tokenize(c, tm):
    name = 'super_simple'
    fts5.register_tokenizer(c, name, tm)
    fts5_aux.register_aux_function(c, 'tokenize', fts5_aux.aux_tokenize)
    c.execute("CREATE VIRTUAL TABLE fts USING FTS5(content, tokenize={})".
              format(name))
    r = c.executemany('INSERT INTO fts VALUES(?)',
                      (['hello world'], ['こんにちは 世界']))
    assert r.rowcount == 2
    r = c.execute('SELECT tokenize(fts, 0) FROM fts')
    assert [x[0] for x in r.fetchall()] == ['hello, world', 'こんにちは, 世界']
    c.close()
