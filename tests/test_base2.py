# -*- coding: utf-8 -*-
from __future__ import print_function

import sqlite3
import re

import pytest

import sqlitefts as fts


class BaseTokenizer(fts.Tokenizer):

    _spliter = re.compile(r'\s+|\S+')
    _nonws = re.compile(r'\S+')

    def _normalize(self, token):
        return token

    def _tokenize(self, text):
        pos = 0
        for t in self._spliter.findall(text):
            byteLen = len(t.encode('utf-8'))
            if self._nonws.match(t):
                yield self._normalize(t), pos, pos + byteLen
            pos += byteLen

    def tokenize(self, text):
        return self._tokenize(text)


class DebugTokenizer(BaseTokenizer):

    _limit = 16

    def _normalize(self, token):
        if not self._limit:
            raise RuntimeError()
        self._limit -= 1

        print(token, token[0:-1])
        return token[0:-1]


class OriginalDebugTokenizer(fts.Tokenizer):

    _limit = 16

    def tokenize(self, text):
        if not self._limit:
            raise RuntimeError()
        self._limit -= 1

        print(text, [w[0:-1] for w in text.split(' ')])
        return (w[0:-1] for w in text.split(' '))


@pytest.fixture
def db():
    name = 'test'
    conn = sqlite3.connect(':memory:')

    fts.register_tokenizer(conn, name,
                           fts.make_tokenizer_module(DebugTokenizer()))
    conn.execute('CREATE VIRTUAL TABLE fts USING FTS4(tokenize={})'.format(
        name))

    return conn


def testZeroLengthToken(db):
    result = db.executemany('INSERT INTO fts VALUES(?)',
                            [('Make things I', ), (u'Some σ φχικλψ', )])
    assert 2 == result.rowcount


def testInfiniteRecursion(db):
    contents = [('abc def', ), ('abc xyz', )]
    result = db.executemany('INSERT INTO fts VALUES(?)', contents)
    assert 2 == result.rowcount

    result = db.execute("SELECT * FROM fts WHERE fts MATCH 'abc'").fetchall()
    assert 2 == len(result)
