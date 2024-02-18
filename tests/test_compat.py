# coding: utf-8
# test compatibility
# - a tokneizer for FTS5 can be used for FTS3
# - a tokneizer for FTS3 can be wrapped for FTS5
from __future__ import print_function, unicode_literals

import re

import _sqlite3
import pytest
from test_base import c
from test_base import test_full_text_index_queries as test_fts3
from test_fts5 import test_full_text_index_queries as test_fts5

from sqlitefts import Tokenizer, make_tokenizer_module
from sqlitefts.fts5 import FTS3TokenizerAdaptor, FTS5Tokenizer, make_fts5_tokenizer

if not hasattr(_sqlite3, "__file__"):
    pytest.skip("detected statically linked sqlite", allow_module_level=True)


class SimpleFTS5Tokenizer(FTS5Tokenizer):
    _p = re.compile(r"\w+", re.UNICODE)

    def tokenize(self, text, flags=None):
        for m in self._p.finditer(text):
            s, e = m.span()
            t = text[s:e]
            l = len(t.encode("utf-8"))
            p = len(text[:s].encode("utf-8"))
            yield t, p, p + l


class SimpleFTS3Tokenizer(Tokenizer):
    _p = re.compile(r"\w+", re.UNICODE)

    def tokenize(self, text):
        for m in self._p.finditer(text):
            s, e = m.span()
            t = text[s:e]
            l = len(t.encode("utf-8"))
            p = len(text[:s].encode("utf-8"))
            yield t, p, p + l


@pytest.fixture
def tokenizer_module():
    return make_tokenizer_module(SimpleFTS5Tokenizer())


@pytest.fixture
def tm():
    return make_fts5_tokenizer(FTS3TokenizerAdaptor(SimpleFTS3Tokenizer()))
