# coding: utf-8
"""
support library to write SQLite FTS5 tokenizer
"""
import sqlite3
import struct

from .error import Error
from .tokenizer import SQLITE_ERROR, SQLITE_OK, ffi, get_db_from_connection

import typing
from typing import Any, Callable, Iterable, List, Optional, Set, Tuple, TypeAlias, Union

if typing.TYPE_CHECKING:
    from . import fts3
    from .fts3 import TokenInfo, Pointer
    from cffi import FFI

    CData = FFI.CData
    CType = FFI.CType

    class SQLiteCAPI:
        def sqlite3_prepare_v2(
            self, db: CData, sql: bytes, n_byte: int, pp_stmt: Pointer[CData], _: CType
        ) -> int:
            ...

        def sqlite3_bind_pointer(
            self, stmt: CData, pos: int, ptr: Pointer[CData], typ: CData, dtor: CType
        ) -> int:
            ...

        def sqlite3_step(self, stmt: CData) -> int:
            ...

        def sqlite3_finalize(self, stmt: CData) -> int:
            ...

        def sqlite3_errmsg(self, db: CData) -> CData:
            ...

    FTS5_Tokenizer: TypeAlias = CData

    class FTS5API:
        iVersion: int

        def xCreateTokenizer(
            self,
            fts5_api: "FTS5API",
            name: bytes,
            context: Any,
            tokenizer: FTS5_Tokenizer,
            dtor: Union[CType, Callable[[CData], None]],
        ) -> int:
            ...


FTS5_TOKENIZE_QUERY = 0x0001
FTS5_TOKENIZE_PREFIX = 0x0002
FTS5_TOKENIZE_DOCUMENT = 0x0004
FTS5_TOKENIZE_AUX = 0x0008
FTS5_TOKEN_COLOCATED = 0x0001
SQLITE_ROW = 100
FTS5_API_PTR = ffi.new("const char[]", b"fts5_api_ptr")

ffi.cdef(
    """
typedef struct sqlite3_context sqlite3_context;
typedef struct sqlite3_stmt sqlite3_stmt;
typedef struct Mem sqlite3_value;
typedef uint64_t sqlite3_int64;

void sqlite3_result_text(sqlite3_context*, const char*, int, void(*)(void*));
void sqlite3_result_error_code(sqlite3_context*, int);
void sqlite3_result_error(sqlite3_context*, const char*, int);
const unsigned char *sqlite3_value_text(sqlite3_value*);
int sqlite3_value_int(sqlite3_value*);
int sqlite3_prepare_v2(sqlite3*, const char*, int, sqlite3_stmt**, const char**);
int sqlite3_prepare(sqlite3*, const char*, int, sqlite3_stmt**, const char**);
int sqlite3_bind_pointer(sqlite3_stmt*, int, void*, const char*, void(*)(void*));
int sqlite3_step(sqlite3_stmt*);
int sqlite3_finalize(sqlite3_stmt*);
int sqlite3_errcode(sqlite3 *db);
int sqlite3_extended_errcode(sqlite3 *db);
const char *sqlite3_errmsg(sqlite3*);
const void *sqlite3_errmsg16(sqlite3*);
const char *sqlite3_errstr(int);

typedef struct fts5_api fts5_api;
typedef struct fts5_tokenizer fts5_tokenizer;
typedef struct Fts5Tokenizer Fts5Tokenizer;
typedef struct Fts5ExtensionApi Fts5ExtensionApi;
typedef struct Fts5Context Fts5Context;
typedef struct Fts5PhraseIter Fts5PhraseIter;
typedef void (*fts5_extension_function)(
  const Fts5ExtensionApi*, Fts5Context*,
  sqlite3_context*, int, sqlite3_value**);

struct fts5_api {
  int iVersion;
  int (*xCreateTokenizer)(
    fts5_api*, const char*, void*,
    fts5_tokenizer*, void (*xDestroy)(void*));
  int (*xFindTokenizer)(
    fts5_api*, const char*, void**, fts5_tokenizer*);
  int (*xCreateFunction)(
    fts5_api*, const char*, void*,
    fts5_extension_function, void (*xDestroy)(void*));
};

struct fts5_tokenizer {
  int (*xCreate)(void*, const char**, int, Fts5Tokenizer**);
  void (*xDelete)(Fts5Tokenizer*);
  int (*xTokenize)(
    Fts5Tokenizer*, void*, int, const char*, int,
    int (*xToken)(
        void*, int, const char*, int, int, int));
};

struct Fts5ExtensionApi {
  int iVersion;
  void *(*xUserData)(Fts5Context*);
  int (*xColumnCount)(Fts5Context*);
  int (*xRowCount)(Fts5Context*, sqlite3_int64*);
  int (*xColumnTotalSize)(Fts5Context*, int, sqlite3_int64*);
  int (*xTokenize)(
    Fts5Context*, const char*, int, void*,
    int (*xToken)(void*, int, const char*, int, int, int));
  int (*xPhraseCount)(Fts5Context*);
  int (*xPhraseSize)(Fts5Context*, int);
  int (*xInstCount)(Fts5Context*, int*);
  int (*xInst)(Fts5Context*, int, int*, int*, int*);
  sqlite3_int64 (*xRowid)(Fts5Context*);
  int (*xColumnText)(Fts5Context*, int, const char**, int*);
  int (*xColumnSize)(Fts5Context*, int, int*);
  int (*xQueryPhrase)(Fts5Context*, int, void*,
    int(*)(const Fts5ExtensionApi*, Fts5Context*, void*)
  );
  int (*xSetAuxdata)(Fts5Context*, void*, void(*xDelete)(void*));
  void *(*xGetAuxdata)(Fts5Context*, int);
  int (*xPhraseFirst)(Fts5Context*, int, Fts5PhraseIter*, int*, int*);
  void (*xPhraseNext)(Fts5Context*, Fts5PhraseIter*, int*, int*);
  int (*xPhraseFirstColumn)(Fts5Context*, int, Fts5PhraseIter*, int*);
  void (*xPhraseNextColumn)(Fts5Context*, Fts5PhraseIter*, int*);
};
"""
)


class FTS5Tokenizer:
    """
    Tokenizer base class for FTS5.
    """

    def tokenize(self, text: str, flags: int) -> Iterable[TokenInfo]:
        """
        Tokenize given unicode text. Yields each tokenized token,
        start position(in bytes), end positon(in bytes).

        flags will be set if a FTS5 tokenizer is used for FTS5 table.
        a FTS5 tokenizer can be used for FTS3/4 table as well, but
        flags will not be set.
        """
        yield text, 0, len(text.encode("utf-8"))


class FTS3TokenizerAdaptor(FTS5Tokenizer):
    """
    wrap a FTS3 tokenizer instance to adapt it to FTS5 Tokenizer interface
    """

    def __init__(self, fts3tokenizer: "fts3.Tokenizer"):
        self.fts3tokenizer = fts3tokenizer

    def tokenize(self, text: str, flags: int):
        return self.fts3tokenizer.tokenize(text)


fts5_tokenizers = {}
"""hold references to prevent GC"""
registred_fts5_tokenizers = {}
"""hold references to prevent GC"""


def fts5_api_from_db(c: sqlite3.Connection, db: CData, dll: SQLiteCAPI) -> FTS5API:
    cur = c.cursor()
    try:
        cur.execute("SELECT sqlite_version()")
        ver = tuple(int(x) for x in cur.fetchone()[0].split("."))
        if ver < (3, 20, 0):
            cur.execute("SELECT fts5()")
            blob = cur.fetchone()[0]
            ret = ffi.cast("fts5_api*", struct.unpack("P", blob)[0])
        else:
            pRet: Pointer[CData] = ffi.new("fts5_api**")  # type: ignore
            pStmt: Pointer[CData] = ffi.new("sqlite3_stmt**")  # type: ignore
            rc = dll.sqlite3_prepare_v2(db, b"SELECT fts5(?1)", -1, pStmt, ffi.NULL)
            if rc == SQLITE_OK:
                rc = dll.sqlite3_bind_pointer(pStmt[0], 1, pRet, FTS5_API_PTR, ffi.NULL)
                if rc == SQLITE_OK and dll.sqlite3_step(pStmt[0]) == SQLITE_ROW:
                    ret = pRet[0]
                else:
                    ret = None
            else:
                ret = None
            dll.sqlite3_finalize(pStmt[0])
    finally:
        cur.close()
    if ret is None:
        raise Error(
            "unable to get fts5_api(new). rc={}/{}".format(
                rc, ffi.string(dll.sqlite3_errmsg(db)).decode("utf-8")  # type: ignore
            )
        )
    return ret  # type: ignore


def register_tokenizer(
    c: sqlite3.Connection,
    name: str,
    tokenizer: FTS5_Tokenizer,
    context: Any = None,
    on_destroy: Optional[Callable[[Any], None]] = None,
) -> bool:
    """
    register a tokenizer to SQLite connection
    """
    dll: SQLiteCAPI
    db, dll = get_db_from_connection(c)  # type: ignore
    fts5api: FTS5API = fts5_api_from_db(c, db, dll)
    pContext = ffi.new_handle(context) if context is not None else ffi.NULL
    xDestroy: Union[CType, Callable[[CData], None]]
    if on_destroy is None:
        xDestroy = ffi.NULL
    else:

        @ffi.callback("void(void*)")
        def _xDestroy(context: CData):
            on_destroy(ffi.from_handle(context))  # type: ignore

        xDestroy = _xDestroy

    r = fts5api.xCreateTokenizer(
        fts5api, name.encode("utf-8"), pContext, tokenizer, xDestroy
    )
    registred_fts5_tokenizers[name] = (tokenizer, pContext, xDestroy)
    return r == SQLITE_OK


def make_fts5_tokenizer(
    tokenizer: Union[Callable[[CData, List[str]], FTS5Tokenizer], FTS5Tokenizer]
) -> FTS5_Tokenizer:
    """
    make a FTS5 tokenizer using given tokenizer.
    tokenizer can be an instance of Tokenizer or a Tokenizer class or
    a method to get an instance of tokenizer.
    if a class is given, an instance of the class will be created as needed.
    """
    tokenizers: Set[CData] = set()

    @ffi.callback("int(void*, const char **, int, Fts5Tokenizer **)")
    def xcreate(ctx: CData, argv: Pointer[CData], argc: int, ppOut: Pointer[CData]):
        if hasattr(tokenizer, "__call__"):
            args = [ffi.string(x).decode("utf-8") for x in argv[0:argc]]  # type: ignore
            tk = tokenizer(ffi.from_handle(ctx), args)  # type: ignore
        else:
            tk = tokenizer
        th = ffi.new_handle(tk)
        tkn = ffi.cast("Fts5Tokenizer *", th)
        tokenizers.add(th)
        ppOut[0] = tkn
        return SQLITE_OK

    @ffi.callback("void(Fts5Tokenizer *)")
    def xdelete(pTokenizer: CData):
        th = ffi.cast("void *", pTokenizer)
        tk = ffi.from_handle(th)
        on_delete = getattr(tk, "on_delete", None)
        if on_delete and hasattr(on_delete, "__call__"):
            on_delete()

        tokenizers.remove(th)
        return None

    @ffi.callback(
        "int(Fts5Tokenizer *, void *, int, const char *, int, "
        "int(void*, int, const char *, int, int, int))"
    )
    def xtokenize(
        pTokenizer: CData, pCtx: CData, flags: int, pText: CData, nText: int, xToken
    ) -> int:
        tokenizer: FTS5Tokenizer = ffi.from_handle(ffi.cast("void *", pTokenizer))
        text: str = ffi.string(pText[0:nText]).decode("utf-8")  # type: ignore
        for orig, begin, end in tokenizer.tokenize(text, flags):  # type: ignore
            normalized = orig.encode("utf-8")
            if not normalized:
                continue

            # TODO: Synonym Support
            r: int = xToken(
                pCtx, 0, ffi.from_buffer(normalized), len(normalized), begin, end
            )
            if r != SQLITE_OK:
                return r
        return SQLITE_OK

    fts5_tokenizer = ffi.new("fts5_tokenizer *", [xcreate, xdelete, xtokenize])
    fts5_tokenizers[tokenizer] = (fts5_tokenizer, xcreate, xdelete, xtokenize)
    return fts5_tokenizer


__all__ = [
    "register_tokenizer",
    "make_fts5_tokenizer",
    "FTS5Tokenizer",
    "FTS5_TOKENIZE_QUERY",
    "FTS5_TOKENIZE_PREFIX",
    "FTS5_TOKENIZE_DOCUMENT",
    "FTS5_TOKENIZE_AUX",
    "FTS5_TOKEN_COLOCATED",
]
