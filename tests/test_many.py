from __future__ import print_function, unicode_literals
import sqlite3
import os
import tempfile

from faker import Factory
import pytest
import sqlitefts as fts
from sqlitefts import fts5

igo = pytest.importorskip('igo')
fake = Factory.create('ja_JP')


class IgoTokenizer(fts.Tokenizer):
    def __init__(self, path=None):
        self.tagger = igo.tagger.Tagger(path)

    def tokenize(self, text):
        for m in self.tagger.parse(text):
            start = len(text[:m.start].encode('utf-8'))
            yield m.surface, start, start + len(m.surface.encode('utf-8'))


class IgoTokenizer5(fts5.FTS5Tokenizer):
    def __init__(self, path=None):
        self.tagger = igo.tagger.Tagger(path)

    def tokenize(self, text, flags=None):
        for m in self.tagger.parse(text):
            start = len(text[:m.start].encode('utf-8'))
            yield m.surface, start, start + len(m.surface.encode('utf-8'))


@pytest.fixture
def conn():
    f, db = tempfile.mkstemp()
    try:
        os.close(f)
        c = sqlite3.connect(db)
        create_table(c)
        yield c
        c.close()
    finally:
        os.remove(db)


@pytest.fixture
def nr():
    return 10000


def create_table(c):
    fts.register_tokenizer(c, 'igo', fts.make_tokenizer_module(IgoTokenizer()))
    fts5.register_tokenizer(c, 'igo',
                            fts5.make_fts5_tokenizer(IgoTokenizer5()))
    c.execute("CREATE VIRTUAL TABLE fts USING FTS4(tokenize=igo)")
    c.execute("CREATE VIRTUAL TABLE fts5 USING FTS5(w, tokenize=igo)")


def test_insert_many_each(conn, nr):
    with conn:
        for i in range(nr):
            conn.execute('INSERT INTO fts VALUES(?)', [fake.address()])
            conn.execute('INSERT INTO fts5 VALUES(?)', [fake.address()])
    assert conn.execute("SELECT COUNT(*) FROM fts").fetchall()[0][0] == nr
    assert conn.execute("SELECT COUNT(*) FROM fts5").fetchall()[0][0] == nr


def test_insert_many_many(conn, nr):
    with conn:
        conn.executemany('INSERT INTO fts VALUES(?)', ([fake.address()]
                                                       for _ in range(nr)))
        conn.executemany('INSERT INTO fts5 VALUES(?)', ([fake.address()]
                                                        for _ in range(nr)))
    assert conn.execute("SELECT COUNT(*) FROM fts").fetchall()[0][0] == nr
    assert conn.execute("SELECT COUNT(*) FROM fts5").fetchall()[0][0] == nr


def test_insert_many_use_select(conn, nr):
    with conn:
        conn.executemany('INSERT INTO fts VALUES(?)', ([fake.address()]
                                                       for _ in range(nr)))
        conn.executemany('INSERT INTO fts5 VALUES(?)', ([fake.address()]
                                                        for _ in range(nr)))
    with conn:
        conn.execute('INSERT INTO fts SELECT * FROM fts')
        conn.execute('INSERT INTO fts5 SELECT * FROM fts5')

    assert conn.execute("SELECT COUNT(*) FROM fts").fetchall()[0][0] == nr * 2
    assert conn.execute("SELECT COUNT(*) FROM fts5").fetchall()[0][0] == nr * 2
