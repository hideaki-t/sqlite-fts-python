
import os

import pytest

import sqlitefts as fts
from jajp_common import *  # noqa

mecab = pytest.importorskip("MeCab")


class MeCabTokenizer(fts.Tokenizer):
    def __init__(self):
        try:
            self.tagger = mecab.Tagger()
        except:
            self.tagger = mecab.Tagger("".join(["-r", os.getenv("MECABRC", "/etc/mecabrc")]))
            self.tagger.parseToNode("")

    def tokenize(self, text):
        p = 0
        m = self.tagger.parseToNode(text)
        while m:
            token_len = m.length
            d = m.rlength - token_len
            start = p + d
            p = start + token_len
            if token_len:
                yield m.surface, start, p
            m = m.next


@pytest.fixture
def name():
    return "mecab"


@pytest.fixture
def t():
    return MeCabTokenizer()
