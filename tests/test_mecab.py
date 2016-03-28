# coding: utf-8
from __future__ import print_function
import sys

import sqlitefts as fts

import pytest
from jajp_common import *  # noqa
mecab = pytest.importorskip('MeCab')


class MeCabTokenizer(fts.Tokenizer):
    def __init__(self):
        self.tagger = mecab.Tagger()
        self.tagger.parseToNode('')

    if sys.version_info.major == 2:
        def to_mecab(self, text):
            return text.encode('utf-8')

        def from_mecab(self, text):
            return text.decode('utf-8')
    else:
        def to_mecab(self, text):
            return text

        def from_mecab(self, text):
            return text

    def tokenize(self, text):
        p = 0
        m = self.tagger.parseToNode(self.to_mecab(text))
        while m:
            l = m.length
            d = m.rlength - l
            start = p + d
            p = start + l
            if l:
                yield self.from_mecab(m.surface), start, p
            m = m.next


@pytest.fixture
def name():
    return 'mecab'


@pytest.fixture
def t():
    return MeCabTokenizer()
