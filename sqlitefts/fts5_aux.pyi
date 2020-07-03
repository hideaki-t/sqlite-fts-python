import sqlite3
from typing import Any, Callable, Union

import apsw  # type: ignore

def aux_tokenize(pApi: Any, pFts: Any, pCtx: Any, nVal: Any, apVal: Any): ...
def register_aux_function(
    con: Union[sqlite3.Connection, apsw.Connection],
    name: str,
    f: Callable,
    ref_ctrl: bool = ...,
) -> int: ...
