# coding: utf-8
from __future__ import print_function, unicode_literals

import sqlitefts as fts

import pytest
from jajp_common import *  # noqa
janome = pytest.importorskip('janome.tokenizer')


class JanomeTokenizer(fts.Tokenizer):
    def __init__(self, path=None):
        self.tagger = janome.Tokenizer()

    def tokenize(self, text):
        p = 0
        for m in self.tagger.tokenize(text):
            if m.surface.strip():
                start = len(text[:text.index(m.surface, p)].encode('utf-8'))
                yield m.surface, start, start + len(m.surface.encode('utf-8'))
            p += len(m.surface)


@pytest.fixture
def name():
    return 'janome'


@pytest.fixture
def t():
    return JanomeTokenizer()
