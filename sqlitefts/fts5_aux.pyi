import sqlite3
from typing import Any, Callable

def aux_tokenize(pApi: Any, pFts: Any, pCtx: Any, nVal: Any, apVal: Any): ...
def register_aux_function(
    con: sqlite3.Connection,
    name: str,
    f: Callable,
    ref_ctrl: bool = ...,
) -> int: ...
