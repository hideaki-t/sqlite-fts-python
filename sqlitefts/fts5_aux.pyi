import sqlite3
from collections.abc import Callable
from typing import Any

import apsw  # type: ignore

def aux_tokenize(pApi: Any, pFts: Any, pCtx: Any, nVal: Any, apVal: Any): ...
def register_aux_function(
    con: sqlite3.Connection | apsw.Connection,
    name: str,
    f: Callable,
    ref_ctrl: bool = ...,
) -> int: ...
