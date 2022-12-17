# coding: utf-8
"""
support library to write SQLite FTS3 tokenizer
"""
from __future__ import annotations

import sqlite3
import struct
import typing
import warnings
from typing import (
    Callable,
    Dict,
    Generic,
    Iterable,
    Iterator,
    List,
    Tuple,
    TypeAlias,
    TypeVar,
    Union,
)

import cffi

from .error import Error
from .tokenizer import SQLITE_DONE, SQLITE_ERROR, SQLITE_OK, ffi, get_db_from_connection

if typing.TYPE_CHECKING:
    Pointed = TypeVar("Pointed")

    class Pointer(Generic[Pointed]):
        def __getitem__(self, n: int) -> Pointed:
            ...

        def __setitem__(self, key: int, value: Pointed, /) -> Pointed:
            ...

    FTS3TokenizerModule: TypeAlias = cffi.FFI.CData
    TokenizerMapValue: TypeAlias = Tuple[
        FTS3TokenizerModule,
        Callable[[], int],
        Callable[[], int],
        Callable[[], int],
        Callable[[], int],
        Callable[[], int],
    ]

    class SQLiteTokenizer:
        t: Pointer[Tokenizer]

    class FTS3TokenizerCursor:
        pTokenizer: SQLiteTokenizer
        tokens: cffi.FFI.CData
        pos: int
        offset: int

    TokenInfo: TypeAlias = Tuple[str, int, int]
    TokenInfoInternal: TypeAlias = Tuple[bytes, int, int]

SQLITE_DBCONFIG_ENABLE_FTS3_TOKENIZER = 1004

ffi.cdef(
    """
int sqlite3_db_config(sqlite3 *, int op, ...);

typedef struct sqlite3_tokenizer_module sqlite3_tokenizer_module;
typedef struct sqlite3_tokenizer sqlite3_tokenizer;
typedef struct sqlite3_tokenizer_cursor sqlite3_tokenizer_cursor;
struct sqlite3_tokenizer_module {
  int iVersion;
  int (*xCreate)(int, const char*const*, sqlite3_tokenizer**);
  int (*xDestroy)(sqlite3_tokenizer*);
  int (*xOpen)(
    sqlite3_tokenizer*, const char*, int, sqlite3_tokenizer_cursor**);
  int (*xClose)(sqlite3_tokenizer_cursor*);
  int (*xNext)(
    sqlite3_tokenizer_cursor*, const char**, int*, int*, int*, int*);
  int (*xLanguageid)(sqlite3_tokenizer_cursor*, int);
};

struct sqlite3_tokenizer {
  const sqlite3_tokenizer_module *pModule;
  void *t;
};

struct sqlite3_tokenizer_cursor {
  sqlite3_tokenizer *pTokenizer;
  void *tokens;
  size_t pos;
  size_t offset;
};
"""
)


class Tokenizer:
    """
    Tokenizer base class.
    """

    def tokenize(self, text: str) -> Iterable[TokenInfo]:
        """
        Tokenize given unicode text. Yields each tokenized token,
        start position(in bytes), end positon(in bytes)
        """
        yield text, 0, len(text.encode("utf-8"))


tokenizer_modules: Dict[
    Union[Callable[[List[str]], Tokenizer], Tokenizer], TokenizerMapValue
] = {}
"""hold references to prevent GC"""


def make_tokenizer_module(
    tokenizer: Union[Callable[[List[str]], Tokenizer], Tokenizer]
) -> FTS3TokenizerModule:
    """tokenizer module"""
    tokenizers: Dict[SQLiteTokenizer, Pointer[Tokenizer]] = {}
    cursors: Dict[FTS3TokenizerCursor, cffi.FFI.CData] = {}

    @ffi.callback("int(int, const char *const*, sqlite3_tokenizer **)")
    def xcreate(
        argc: int,
        argv: Pointer[cffi.FFI.CData],
        ppTokenizer: Pointer[SQLiteTokenizer],
    ) -> int:
        if hasattr(tokenizer, "__call__"):
            args: list[str] = [ffi.string(x).decode("utf-8") for x in argv[0:argc]]  # type: ignore
            tk = tokenizer(args)  # type: ignore
        elif isinstance(tokenizer, Tokenizer):
            tk = tokenizer
        else:
            return SQLITE_ERROR

        th = typing.cast(Pointer[Tokenizer], ffi.new_handle(tk))
        tkn: SQLiteTokenizer = typing.cast(
            SQLiteTokenizer, ffi.new("sqlite3_tokenizer *")
        )
        tkn.t = th
        tokenizers[tkn] = th
        ppTokenizer[0] = tkn
        return SQLITE_OK

    @ffi.callback("int(sqlite3_tokenizer *)")
    def xdestroy(pTokenizer: SQLiteTokenizer) -> int:
        del tokenizers[pTokenizer]
        return SQLITE_OK

    @ffi.callback(
        "int(sqlite3_tokenizer*, const char *, int, sqlite3_tokenizer_cursor **)"
    )
    def xopen(
        pTokenizer: SQLiteTokenizer,
        pInput: cffi.FFI.CData,
        nInput: int,
        ppCursor: Pointer[FTS3TokenizerCursor],
    ) -> int:
        cur: FTS3TokenizerCursor = typing.cast(
            FTS3TokenizerCursor, ffi.new("sqlite3_tokenizer_cursor *")
        )
        tokenizer: Tokenizer = ffi.from_handle(
            typing.cast(cffi.FFI.CData, pTokenizer.t)
        )
        i: str = typing.cast(str, ffi.string(pInput).decode("utf-8"))  # type: ignore
        tokens = [(n.encode("utf-8"), b, e) for n, b, e in tokenizer.tokenize(i) if n]
        tknh = ffi.new_handle(iter(tokens))
        cur.pTokenizer = pTokenizer
        cur.tokens = tknh
        cur.pos = 0
        cur.offset = 0
        cursors[cur] = tknh
        ppCursor[0] = cur
        return SQLITE_OK

    @ffi.callback(
        "int(sqlite3_tokenizer_cursor*, const char **, int *, int *, int *, int *)"
    )
    def xnext(
        pCursor: Pointer[FTS3TokenizerCursor],
        ppToken: Pointer[cffi.FFI.CData],
        pnBytes: Pointer[int],
        piStartOffset: Pointer[int],
        piEndOffset: Pointer[int],
        piPosition: Pointer[int],
    ) -> int:
        try:
            cur = pCursor[0]
            tokens: Iterator[TokenInfoInternal] = ffi.from_handle(cur.tokens)
            normalized, inputBegin, inputEnd = next(tokens)
            ppToken[0] = ffi.from_buffer(normalized)
            pnBytes[0] = len(normalized)
            piStartOffset[0] = inputBegin
            piEndOffset[0] = inputEnd
            cur.offset = inputEnd
            piPosition[0] = cur.pos
            cur.pos += 1
        except StopIteration:
            return SQLITE_DONE
        return SQLITE_OK

    @ffi.callback("int(sqlite3_tokenizer_cursor *)")
    def xclose(pCursor: FTS3TokenizerCursor) -> int:
        tk: Tokenizer = ffi.from_handle(
            typing.cast(cffi.FFI.CData, pCursor.pTokenizer.t)
        )
        on_close = getattr(tk, "on_close", None)
        if on_close and hasattr(on_close, "__call__"):
            on_close()

        del cursors[pCursor]
        return SQLITE_OK

    tokenizer_module = ffi.new(
        "sqlite3_tokenizer_module*", [0, xcreate, xdestroy, xopen, xclose, xnext]
    )
    tokenizer_modules[tokenizer] = (
        tokenizer_module,
        xcreate,
        xdestroy,
        xopen,
        xclose,
        xnext,
    )
    return tokenizer_module


def enable_fts3_tokenizer(c: sqlite3.Connection) -> bool:
    db, dll = get_db_from_connection(c)
    rc: int = dll.sqlite3_db_config(  # type: ignore
        db, SQLITE_DBCONFIG_ENABLE_FTS3_TOKENIZER, ffi.cast("int", 1), ffi.NULL  # type: ignore
    )
    return rc == SQLITE_OK


def register_tokenizer(
    conn: sqlite3.Connection, name: str, tokenizer_module: FTS3TokenizerModule
):
    """register tokenizer module with SQLite connection."""
    module_addr = int(ffi.cast("uintptr_t", tokenizer_module))
    address_blob = sqlite3.Binary(struct.pack("P", module_addr))
    if not enable_fts3_tokenizer(conn):
        warnings.warn("enabling 2-arg fts3_tokenizer failed.", RuntimeWarning)
    cur = conn.cursor()
    try:
        r = cur.execute("SELECT fts3_tokenizer(?, ?)", (name, address_blob)).fetchall()
    finally:
        cur.close()
    return r


__all__ = ["Tokenizer", "make_tokenizer_module", "register_tokenizer", "Error"]
