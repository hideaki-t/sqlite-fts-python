import sqlite3
from collections.abc import Iterator
from typing import Any

import apsw  # type: ignore

TokenizerModule = Any

class Tokenizer:
    def tokenize(self, text: str) -> Iterator[tuple[str, int, int]]: ...

def make_tokenizer_module(tokenizer: Tokenizer) -> TokenizerModule: ...
def register_tokenizer(
    conn: sqlite3.Connection | apsw.Connection,
    name: str,
    tokenizer_module: TokenizerModule,
) -> list[Any]: ...
