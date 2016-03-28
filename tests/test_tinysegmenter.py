# coding: utf-8
from __future__ import print_function, unicode_literals

import sqlitefts as fts

import pytest
from jajp_common import *  # noqa
ts = pytest.importorskip('tinysegmenter')


class TinySegmenterTokenizer(fts.Tokenizer):
    def __init__(self, path=None):
        pass

    def tokenize(self, text):
        p = 0
        for t in ts.tokenize(text):
            lt = len(t)
            np = p + text[p:].index(t)
            start = len(text[:np].encode('utf-8')) + (lt - len(t.lstrip()))
            txt = t.strip()
            yield txt, start, start + len(txt.encode('utf-8'))
            p = np + lt


@pytest.fixture
def name():
    return 'tinysegmenter'


@pytest.fixture
def t():
    return TinySegmenterTokenizer()
