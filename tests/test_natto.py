

import pytest

import sqlitefts as fts
from jajp_common import *  # noqa

mecab = pytest.importorskip("natto")


class NattoPyTokenizer(fts.Tokenizer):
    def tokenize(self, text):
        p = 0
        with mecab.MeCab() as tagger:
            for m in tagger.parse(text, as_nodes=1):
                token_len = m.length
                d = m.rlength - token_len
                start = p + d
                p = start + token_len
                if token_len:
                    yield m.surface, start, p


@pytest.fixture
def name():
    return "nattopy"


@pytest.fixture
def t():
    return NattoPyTokenizer()
