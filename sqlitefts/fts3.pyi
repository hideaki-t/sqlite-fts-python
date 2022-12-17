import sqlite3
from typing import Any, Iterator, List, Tuple

TokenizerModule = Any

class Tokenizer:
    def tokenize(self, text: str) -> Iterator[Tuple[str, int, int]]: ...

def make_tokenizer_module(tokenizer: Tokenizer) -> TokenizerModule: ...
def register_tokenizer(
    conn: sqlite3.Connection,
    name: str,
    tokenizer_module: TokenizerModule,
) -> List[Any]: ...
