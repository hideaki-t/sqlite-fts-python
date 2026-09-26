import pytest

import sqlitefts as fts
from jajp_common import BaseJaJpTest

igo = pytest.importorskip("igo")


class IgoTokenizer(fts.Tokenizer):
    def __init__(self, path=None):
        self.tagger = igo.tagger.Tagger(path)

    def tokenize(self, text):
        for m in self.tagger.parse(text):
            start = len(text[: m.start].encode("utf-8"))
            yield m.surface, start, start + len(m.surface.encode("utf-8"))


class TestIgo(BaseJaJpTest):
    @pytest.fixture
    def name(self):
        return "igo"

    @pytest.fixture
    def t(self):
        return IgoTokenizer()
