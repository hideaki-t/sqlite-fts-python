from .tokenizer import SQLITE_OK
from .fts5 import ffi, dll, fts5_api_from_db

from typing import Dict, Callable, Tuple, Any, Union, TYPE_CHECKING
if TYPE_CHECKING:
    import sqlite3
    import apsw  # type: ignore

SQLITE_TRANSIENT = ffi.cast('void(*)(void*)', -1)

_aux_funcs_holder: Dict[Any, Tuple[Any, Callable]] = {}
'''holding references of aux funcs to prevent GC'''


@ffi.callback('void(const Fts5ExtensionApi*, Fts5Context*,'
              'sqlite3_context*, int, sqlite3_value**)')
def aux_tokenize(pApi, pFts, pCtx, nVal, apVal):
    ''' FTS5 AUX function to tokenize a column.

    this function is a callback function, thus it should not be called directly
    '''
    if nVal != 1:
        dll.sqlite3_result_error(
            pCtx, ffi.new('char[]', 'this function accepts only 1 argument'))
        return

    col = dll.sqlite3_value_int(apVal[0])
    pz = ffi.new('char**')
    pn = ffi.new('int*')
    rc = pApi.xColumnText(pFts, col, pz, pn)
    if rc != SQLITE_OK:
        dll.sqlite3_result_error_code(pCtx, rc)
        return

    tokens = []

    @ffi.callback('int(void*, int, const char*, int, int, int)')
    def token(pCtx, tflags, pToken, nToken, iStart, iEnd):
        tokens.append(ffi.string(pToken[0:nToken]))
        return SQLITE_OK

    rc = pApi.xTokenize(pFts, pz[0], pn[0], ffi.NULL, token)
    if rc == SQLITE_OK:
        dll.sqlite3_result_text(pCtx,
                                ffi.new('char []', b', '.join(tokens)), -1,
                                SQLITE_TRANSIENT)
    else:
        dll.sqlite3_result_error_code(pCtx, rc)


def register_aux_function(con: 'Union[sqlite3.Connection, apsw.Connection]',
                          name: str,
                          f: Callable,
                          ref_ctrl: bool=True) -> int:
    '''register a FTS5 auxiliary function to given connection.

    ref_ctrl can be set to False safely only if the given function
    has a valid lifetime.
    If ref_ctrl is True, the connection must be closed explicitly.
    '''
    fts5api = fts5_api_from_db(con)

    if ref_ctrl:

        @ffi.callback('void(void*)')
        def destroy(pCtx):
            del _aux_funcs_holder[h]

        h = ffi.new_handle(con)
    else:
        h = destroy = ffi.NULL

    r = fts5api.xCreateFunction(fts5api, name.encode('utf-8'), h, f, destroy)
    if r == SQLITE_OK and ref_ctrl:
        _aux_funcs_holder[h] = (destroy, f)
    return r
