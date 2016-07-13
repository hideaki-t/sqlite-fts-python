# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sqlite3
import re

import pytest

import sqlitefts as fts
from sqlitefts import ranking


class Tokenizer(fts.Tokenizer):

    _spliter = re.compile(r'\s+|\S+', re.UNICODE)
    _nonws = re.compile(r'\S+', re.UNICODE)

    def _normalize(self, token):
        return token.lower()

    def _tokenize(self, text):
        pos = 0
        for t in self._spliter.findall(text):
            byteLen = len(t.encode('utf-8'))
            if self._nonws.match(t):
                yield self._normalize(t), pos, pos + byteLen
            pos += byteLen

    def tokenize(self, text):
        return self._tokenize(text)


@pytest.fixture
def db():
    name = 'test'
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row

    fts.register_tokenizer(conn, name, fts.make_tokenizer_module(Tokenizer()))

    conn.execute('CREATE VIRTUAL TABLE fts3 USING FTS3(tokenize={})'.format(
        name))
    conn.execute('CREATE VIRTUAL TABLE fts4 USING FTS4(tokenize={})'.format(
        name))

    values = [
        ['Make thing I'],
        ['Some thing φχικλψ thing'],
        [
            'Fusce volutpat hendrerit sem. Fusce sit amet vulputate dui. '
            'Sed posuere mi a nisl aliquet tempor. Praesent tincidunt vel nunc ac pharetra.'
        ],
        [
            'Nam molestie euismod leo id aliquam. In hac habitasse platea dictumst.'
        ],
        [
            'Vivamus tincidunt feugiat tellus ac bibendum. In rhoncus dignissim suscipit.'
        ],
        [
            'Pellentesque hendrerit nulla rutrum luctus rutrum. Fusce hendrerit fermentum nunc at posuere.'
        ],
    ]
    for n in ('fts3', 'fts4'):
        result = conn.executemany('INSERT INTO {0} VALUES(?)'.format(n),
                                  values)
        assert result.rowcount == len(values)

    conn.create_function('bm25', 2, ranking.bm25)
    conn.create_function('rank', 1, ranking.simple)

    return conn


def testSimple(db):
    sql = ("SELECT content, rank(matchinfo(fts3, 'pcx')) AS rank "
           "FROM fts3 "
           "WHERE fts3 MATCH :query "
           "ORDER BY rank")
    actual = [dict(x) for x in db.execute(sql, {'query': 'thing'})]

    assert 2 == len(actual)
    assert ['Some thing φχικλψ thing', 'Make thing I'] \
        == [x['content'] for x in actual]
    assert {'content': 'Some thing φχικλψ thing',
            'rank': -0.6666666666666666} == actual[0]
    assert {'content': 'Make thing I',
            'rank': -0.3333333333333333} == actual[1]


def testBm25(db):
    sql = ("SELECT content, bm25(matchinfo(fts4, 'pcnalx'), 1) AS rank "
           "FROM fts4 "
           "WHERE fts4 MATCH :query "
           "ORDER BY rank")
    actual = [dict(x) for x in db.execute(sql, {'query': 'thing'})]

    assert 2 == len(actual)
    assert {'content': 'Some thing φχικλψ thing',
            'rank': -0.9722786938230542} == actual[0]
    assert {'content': 'Make thing I',
            'rank': -0.8236501036844982} == actual[1]
