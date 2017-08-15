from __future__ import print_function, unicode_literals
import sqlite3
import os
import tempfile

from faker import Factory
import pytest
import sqlitefts as fts

igo = pytest.importorskip('igo')
fake = Factory.create('ja_JP')


class IgoTokenizer(fts.Tokenizer):
    def __init__(self, path=None):
        self.tagger = igo.tagger.Tagger(path)

    def tokenize(self, text):
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
    c.execute("CREATE VIRTUAL TABLE fts USING FTS4(tokenize=igo)")


def test_insert_many_each(conn, nr):
    with conn:
        for i in range(nr):
            conn.execute('INSERT INTO fts VALUES(?)', [fake.address()])
    r = conn.execute("SELECT COUNT(*) FROM fts").fetchall()
    assert r[0][0] == nr


def test_insert_many_many(conn, nr):
    with conn:
        conn.executemany('INSERT INTO fts VALUES(?)', ([fake.address()]
                                                       for _ in range(nr)))
    r = conn.execute("SELECT COUNT(*) FROM fts").fetchall()
    assert r[0][0] == nr


def test_insert_many_use_select(conn, nr):
    with conn:
        conn.executemany('INSERT INTO fts VALUES(?)', ([fake.address()]
                                                       for _ in range(nr)))
    with conn:
        conn.execute('INSERT INTO fts SELECT * FROM fts')

    r = conn.execute("SELECT COUNT(*) FROM fts").fetchall()
    assert r[0][0] == nr * 2
