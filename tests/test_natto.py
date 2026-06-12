
import sys

import pytest

import sqlitefts as fts
from jajp_common import *  # noqa

mecab = pytest.importorskip("natto")


class NattoPyTokenizer(fts.Tokenizer):
    if sys.version_info.major == 2:

        def to_mecab(self, text):
            return text.encode("utf-8")

        def from_mecab(self, text):
            return text.decode("utf-8")

    else:

        def to_mecab(self, text):
            return text

        def from_mecab(self, text):
            return text

    def tokenize(self, text):
        p = 0
        with mecab.MeCab() as tagger:
            for m in tagger.parse(self.to_mecab(text), as_nodes=1):
                token_len = m.length
                d = m.rlength - token_len
                start = p + d
                p = start + token_len
                if token_len:
                    yield self.from_mecab(m.surface), start, p


@pytest.fixture
def name():
    return "nattopy"


@pytest.fixture
def t():
    return NattoPyTokenizer()
