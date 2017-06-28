# coding: utf-8
from __future__ import print_function, unicode_literals
import re

import pytest
apsw = pytest.importorskip('apsw')

import sqlitefts as fts


class SimpleTokenizer(fts.Tokenizer):
    _p = re.compile(r'\w+', re.UNICODE)

    def tokenize(self, text):
        for m in self._p.finditer(text):
            s, e = m.span()
            t = text[s:e]
            l = len(t.encode('utf-8'))
            p = len(text[:s].encode('utf-8'))
            yield t, p, p + l


def test_createtable():
    c = apsw.Connection(':memory:')
    name = 'simple'
    sql = "CREATE VIRTUAL TABLE fts USING FTS4(tokenize={})".format(name)
    fts.register_tokenizer(c, name,
                           fts.make_tokenizer_module(SimpleTokenizer()))
    c.cursor().execute(sql)

    r = c.cursor().execute(
        "SELECT type, name, tbl_name, sql FROM sqlite_master WHERE type='table' AND name='fts'"
    ).fetchone()
    assert r == ('table', 'fts', 'fts', sql)
    c.close()


def test_insert():
    c = apsw.Connection(':memory:')
    name = 'simple'
    content = 'これは日本語で書かれています'
    fts.register_tokenizer(c, name,
                           fts.make_tokenizer_module(SimpleTokenizer()))
    c.cursor().execute(
        "CREATE VIRTUAL TABLE fts USING FTS4(tokenize={})".format(name))
    r = c.cursor().execute('INSERT INTO fts VALUES(?)', (content, ))
    assert c.changes() == 1
    r = c.cursor().execute("SELECT content FROM fts").fetchone()
    assert r[0] == content
    c.close()


def test_match():
    c = apsw.Connection(':memory:')
    name = 'simple'
    contents = [('abc def', ), ('abc xyz', ), ('あいうえお かきくけこ', ),
                ('あいうえお らりるれろ', )]
    fts.register_tokenizer(c, name,
                           fts.make_tokenizer_module(SimpleTokenizer()))
    c.cursor().execute(
        "CREATE VIRTUAL TABLE fts USING FTS4(tokenize={})".format(name))
    r = c.cursor().executemany('INSERT INTO fts VALUES(?)', contents)
    r = c.cursor().execute("SELECT * FROM fts").fetchall()
    assert len(r) == 4
    r = c.cursor().execute(
        "SELECT * FROM fts WHERE fts MATCH 'abc'").fetchall()
    assert len(r) == 2
    r = c.cursor().execute(
        "SELECT content FROM fts WHERE fts MATCH 'def'").fetchall()
    assert len(r) == 1 and r[0][0] == contents[0][0]
    r = c.cursor().execute(
        "SELECT content FROM fts WHERE fts MATCH 'xyz'").fetchall()
    assert len(r) == 1 and r[0][0] == contents[1][0]
    r = c.cursor().execute(
        "SELECT * FROM fts WHERE fts MATCH 'zzz'").fetchall()
    assert len(r) == 0
    r = c.cursor().execute(
        "SELECT * FROM fts WHERE fts MATCH 'あいうえお'").fetchall()
    assert len(r) == 2
    r = c.cursor().execute(
        "SELECT content FROM fts WHERE fts MATCH 'かきくけこ'").fetchall()
    assert len(r) == 1 and r[0][0] == contents[2][0]
    r = c.cursor().execute(
        "SELECT content FROM fts WHERE fts MATCH 'らりるれろ'").fetchall()
    assert len(r) == 1 and r[0][0] == contents[3][0]
    r = c.cursor().execute(
        "SELECT * FROM fts WHERE fts MATCH 'まみむめも'").fetchall()
    assert len(r) == 0
    c.close()


def test_full_text_index_queries():
    name = 'simple'
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
    with apsw.Connection(':memory:') as c:
        fts.register_tokenizer(c, name,
                               fts.make_tokenizer_module(SimpleTokenizer()))
        c.cursor().execute(
            "CREATE VIRTUAL TABLE docs USING FTS4(title, body, tokenize={})".
            format(name))
        c.cursor().executemany("INSERT INTO docs(title, body) VALUES(?, ?)",
                               docs)
        r = c.cursor().execute(
            "SELECT * FROM docs WHERE docs MATCH 'Python'").fetchall()
        assert len(r) == 1
        r = c.cursor().execute(
            "SELECT * FROM docs WHERE docs MATCH 'bind'").fetchall()
        assert len(r) == 0
        r = c.cursor().execute(
            "SELECT * FROM docs WHERE docs MATCH 'binding'").fetchall()
        assert len(r) == 1
        r = c.cursor().execute(
            "SELECT * FROM docs WHERE docs MATCH 'to'").fetchall()
        assert len(r) == 2
        r = c.cursor().execute(
            "SELECT * FROM docs WHERE docs MATCH 'あいうえお'").fetchall()
        assert len(r) == 1
        r = c.cursor().execute(
            "SELECT * FROM docs WHERE docs MATCH 'らりるれろ'").fetchall()
        assert len(r) == 0
        assert (
            c.cursor().execute("SELECT * FROM docs WHERE docs MATCH 'binding'")
            .fetchall()[0] == c.cursor().execute(
                "SELECT * FROM docs WHERE body MATCH 'binding'").fetchall()[0])
        assert (
            c.cursor().execute("SELECT * FROM docs WHERE body MATCH 'binding'")
            .fetchall()[0] == c.cursor().execute(
                "SELECT * FROM docs WHERE docs MATCH 'body:binding'")
            .fetchall()[0])
        assert (
            c.cursor().execute("SELECT * FROM docs WHERE docs MATCH 'あいうえお'")
            .fetchall()[0] == c.cursor().execute(
                "SELECT * FROM docs WHERE body MATCH 'あいうえお'").fetchall()[0])
        assert (
            c.cursor().execute("SELECT * FROM docs WHERE body MATCH 'かきくけこ'")
            .fetchall()[0] == c.cursor().execute(
                "SELECT * FROM docs WHERE docs MATCH 'body:かきくけこ'")
            .fetchall()[0])
        r = c.cursor().execute(
            "SELECT * FROM docs WHERE docs MATCH 'title:bind'").fetchall()
        assert len(r) == 0
        r = c.cursor().execute(
            "SELECT * FROM docs WHERE docs MATCH 'title:README'").fetchall()
        assert len(r) == 1
        r = c.cursor().execute(
            "SELECT * FROM docs WHERE docs MATCH 'title:日本語'").fetchall()
        assert len(r) == 1
        r = c.cursor().execute(
            "SELECT * FROM docs WHERE title MATCH 'bind'").fetchall()
        assert len(r) == 0
        r = c.cursor().execute(
            "SELECT * FROM docs WHERE title MATCH 'README'").fetchall()
        assert len(r) == 1
        r = c.cursor().execute(
            "SELECT * FROM docs WHERE title MATCH '日本語'").fetchall()
        assert len(r) == 1
        r = c.cursor().execute(
            "SELECT * FROM docs WHERE docs MATCH 'to in'").fetchall()
        assert len(r) == 2
        r = c.cursor().execute(
            "SELECT * FROM docs WHERE docs MATCH 'Py*'").fetchall()
        assert len(r) == 1
        r = c.cursor().execute(
            "SELECT * FROM docs WHERE docs MATCH 'Z*'").fetchall()
        assert len(r) == 0
        r = c.cursor().execute(
            "SELECT * FROM docs WHERE docs MATCH 'あ*'").fetchall()
        assert len(r) == 1
        r = c.cursor().execute(
            "SELECT * FROM docs WHERE docs MATCH 'ん*'").fetchall()
        assert len(r) == 0
        r = c.cursor().execute(
            "SELECT * FROM docs WHERE docs MATCH 'tokenizer SQLite'").fetchall(
            )
        assert len(r) == 1
        r = c.cursor().execute(
            "SELECT * FROM docs WHERE docs MATCH '\"tokenizer SQLite\"'"
        ).fetchall()
        assert len(r) == 0
        r = c.cursor().execute(
            "SELECT * FROM docs WHERE docs MATCH 'あいうえお たちつてと'").fetchall()
        assert len(r) == 1
        r = c.cursor().execute(
            "SELECT * FROM docs WHERE docs MATCH '\"あいうえお たちつてと\"'").fetchall(
            )
        assert len(r) == 0
        r = c.cursor().execute(
            "SELECT * FROM docs WHERE docs MATCH '\"tok* SQL*\"'").fetchall()
        assert len(r) == 0
        r = c.cursor().execute(
            "SELECT * FROM docs WHERE docs MATCH '\"tok* of SQL*\"'").fetchall(
            )
        assert len(r) == 1
        r = c.cursor().execute(
            "SELECT * FROM docs WHERE docs MATCH '\"あ* さ*\"'").fetchall()
        assert len(r) == 0
        r = c.cursor().execute(
            "SELECT * FROM docs WHERE docs MATCH '\"あ* かきくけこ さ*\"'").fetchall(
            )
        assert len(r) == 1
        r = c.cursor().execute(
            "SELECT * FROM docs WHERE docs MATCH 'tokenizer NEAR SQLite'"
        ).fetchall()
        assert len(r) == 1
        r = c.cursor().execute(
            "SELECT * FROM docs WHERE docs MATCH 'binding NEAR/2 SQLite'"
        ).fetchall()
        assert len(r) == 0
        r = c.cursor().execute(
            "SELECT * FROM docs WHERE docs MATCH 'binding NEAR/3 SQLite'"
        ).fetchall()
        assert len(r) == 1
        r = c.cursor().execute(
            "SELECT * FROM docs WHERE docs MATCH 'あいうえお NEAR たちつてと'").fetchall(
            )
        assert len(r) == 1
        r = c.cursor().execute(
            "SELECT * FROM docs WHERE docs MATCH 'あいうえお NEAR/2 たちつてと'"
        ).fetchall()
        assert len(r) == 1
        r = c.cursor().execute(
            "SELECT * FROM docs WHERE docs MATCH 'あいうえお NEAR/3 たちつてと'"
        ).fetchall()
        assert len(r) == 1


def test_tokenizer_output():
    name = 'simple'
    with apsw.Connection(':memory:') as c:
        fts.register_tokenizer(c, name,
                               fts.make_tokenizer_module(SimpleTokenizer()))
        c.cursor().execute(
            "CREATE VIRTUAL TABLE tok1 USING fts3tokenize({})".format(name))
        expect = [("This", 0, 4, 0), ("is", 5, 7, 1), ("a", 8, 9, 2),
                  ("test", 10, 14, 3), ("sentence", 15, 23, 4)]
        for a, e in zip(c.cursor().execute(
                "SELECT token, start, end, position "
                "FROM tok1 WHERE input='This is a test sentence.'"), expect):
            assert e == a

        s = 'これ は テスト の 文 です'
        expect = [(None, 0, -1, 0)]
        for i, t in enumerate(s.split()):
            expect.append((t, expect[-1][2] + 1,
                           expect[-1][2] + 1 + len(t.encode('utf-8')), i))
        expect = expect[1:]
        for a, e in zip(c.cursor().execute(
                "SELECT token, start, end, position "
                "FROM tok1 WHERE input=?", [s]), expect):
            assert e == a
