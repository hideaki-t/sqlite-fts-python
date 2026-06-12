import sqlite3

import pytest


@pytest.fixture
def test_docs():
    return [
        (
            "README",
            "sqlitefts-python provides binding for tokenizer of SQLite "
            "Full-Text search(FTS3/4). It allows you to write tokenizers in Python.",
        ),
        (
            "LICENSE",
            """Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:""",
        ),
        ("日本語", "あいうえお かきくけこ さしすせそ たちつてと なにぬねの"),
    ]


@pytest.fixture
def c():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    return conn
