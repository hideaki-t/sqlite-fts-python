import sqlite3
from typing import Any, Callable, Iterable, Optional, Tuple, Union

import apsw  # type: ignore

from .fts3 import Tokenizer as FTS3Tokenizer

FTS5TokenizerHandle = Any
FTS5_TOKENIZE_QUERY: int
FTS5_TOKENIZE_PREFIX: int
FTS5_TOKENIZE_DOCUMENT: int
FTS5_TOKENIZE_AUX: int
FTS5_TOKEN_COLOCATED: int

class FTS5Tokenizer:
    def tokenize(self, text: str, flags: int = ...) -> Iterable[Tuple[str, int, int]]: ...

class FTS3TokenizerAdaptor(FTS5Tokenizer):
    fts3tokenizer: Any = ...
    def __init__(self, fts3tokenizer: FTS3Tokenizer) -> None: ...
    def tokenize(self, text: str, flags: int = ...) -> Iterable[Tuple[str, int, int]]: ...

def register_tokenizer(
    c: Union[sqlite3.Connection, apsw.Connection],
    name: str,
    tokenizer: FTS5TokenizerHandle,
    context: Any = ...,
    on_destroy: Optional[Callable[[Any], None]] = ...,
) -> bool: ...
def make_fts5_tokenizer(
    tokenizer: Union[FTS5Tokenizer, Callable[[], FTS5Tokenizer]],
) -> FTS5TokenizerHandle: ...
