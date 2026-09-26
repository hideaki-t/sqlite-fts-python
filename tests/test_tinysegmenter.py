import pytest

import sqlitefts as fts
from tests.jajp_common import BaseJaJpTest

tinysegmenter = pytest.importorskip("tinysegmenter")
ts = tinysegmenter.TinySegmenter()


class TinySegmenterTokenizer(fts.Tokenizer):
    def __init__(self, path=None):
        pass

    def tokenize(self, text):
        p = 0
        for t in ts.tokenize(text):
            lt = len(t)
            np = p + text[p:].index(t)
            start = len(text[:np].encode("utf-8")) + (lt - len(t.lstrip()))
            txt = t.strip()
            yield txt, start, start + len(txt.encode("utf-8"))
            p = np + lt


class TestTinySegmenter(BaseJaJpTest):
    @pytest.fixture
    def name(self):
        return "tinysegmenter"

    @pytest.fixture
    def t(self):
        return TinySegmenterTokenizer()
