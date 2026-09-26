import sqlite3
from typing import Any

import apsw  # type: ignore

ffi: Any
dll: Any

SQLITE3DBHandle = Any
SQLITE_OK: int
SQLITE_DONE: int

def get_db_from_connection(
    c: sqlite3.Connection | apsw.Connection,
) -> SQLITE3DBHandle: ...
