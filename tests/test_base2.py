# -*- coding: utf-8 -*-
from __future__ import print_function

import unittest
import sqlite3
import re

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


class TestCase(unittest.TestCase):

    def setUp(self):
        name = 'test'
        conn = sqlite3.connect(':memory:')

        fts.register_tokenizer(conn, name, fts.make_tokenizer_module(DebugTokenizer()))
        conn.execute('CREATE VIRTUAL TABLE fts USING FTS4(tokenize={})'.format(name))

        self.testee = conn

    def testZeroLengthToken(self):
        result = self.testee.executemany('INSERT INTO fts VALUES(?)', [('Make things I',), (u'Some σ φχικλψ',)])
        self.assertEqual(2, result.rowcount)

    def testInfiniteRecursion(self):
        contents = [('abc def',), ('abc xyz',)]
        result = self.testee.executemany('INSERT INTO fts VALUES(?)', contents)
        self.assertEqual(2, result.rowcount)

        result = self.testee.execute("SELECT * FROM fts WHERE fts MATCH 'abc'").fetchall()
        self.assertEqual(2, len(result))
