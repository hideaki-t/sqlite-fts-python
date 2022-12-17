import sqlite3
from typing import Any, Tuple, Union

import apsw  # type: ignore
from _cffi_backend import Lib

SQLITE3DBHandle = Any
SQLITE_OK: int
SQLITE_DONE: int

def get_db_from_connection(
    c: Union[sqlite3.Connection, apsw.Connection]
) -> Tuple[SQLITE3DBHandle, Lib]: ...
