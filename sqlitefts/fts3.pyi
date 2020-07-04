import sqlite3
from typing import Any, Iterator, List, Tuple, Union

import apsw  # type: ignore

TokenizerModule = Any

class Tokenizer:
    def tokenize(self, text: str) -> Iterator[Tuple[str, int, int]]: ...

def make_tokenizer_module(tokenizer: Tokenizer) -> TokenizerModule: ...
def register_tokenizer(
    conn: Union[sqlite3.Connection, apsw.Connection],
    name: str,
    tokenizer_module: TokenizerModule,
) -> List[Any]: ...
